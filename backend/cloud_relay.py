import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from .config import SERVER_IP, BASE_DIR

logger = logging.getLogger("cloud_relay")

_cached_home_hub: Optional[str] = None
_cached_home_hub_exp: float = 0.0

def is_cloud_instance() -> bool:
    """Check if this instance is running on Cloud/VPS rather than user's home LAN."""
    return (
        os.environ.get("CLOUD_HOSTED", "0") == "1"
        or os.environ.get("RENDER") is not None
        or os.environ.get("KOYEB") is not None
        or SERVER_IP.startswith("10.")
        or SERVER_IP.startswith("172.")
        or SERVER_IP == "127.0.0.1"
        or not SERVER_IP.startswith("192.168.50.")
    )

async def get_active_home_hub_url(force_refresh: bool = False) -> Optional[str]:
    """Retrieve verified active Home PC Hub Cloudflare tunnel URL."""
    global _cached_home_hub, _cached_home_hub_exp
    now = time.time()
    if not force_refresh and _cached_home_hub and now < _cached_home_hub_exp:
        return _cached_home_hub

    cand = None
    # 1. Try local endpoint.json if not on cloud
    ep_file = BASE_DIR / "endpoint.json"
    if ep_file.exists():
        try:
            data = json.loads(ep_file.read_text(encoding="utf-8"))
            url = data.get("hub_url")
            if url and "trycloudflare.com" in url:
                cand = url
        except Exception:
            pass

    # 2. Fetch from GitHub raw
    if not cand:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t={int(now)}")
                if res.status_code == 200:
                    data = res.json()
                    url = data.get("hub_url")
                    if url and "trycloudflare.com" in url:
                        cand = url
        except Exception as e:
            logger.debug(f"GitHub endpoint fetch notice: {e}")

    if not cand:
        return None

    # Verify reachability
    try:
        clean = cand.rstrip("/")
        async with httpx.AsyncClient(timeout=3.5, verify=False) as client:
            probe = await client.get(
                f"{clean}/api/auth/status",
                headers={"bypass-tunnel-reminder": "true"}
            )
            if probe.status_code == 200:
                _cached_home_hub = clean
                _cached_home_hub_exp = now + 20.0  # Cache for 20 seconds
                return clean
    except Exception as e:
        logger.debug(f"Home Hub tunnel probe failed: {e}")

    return None

def should_forward_to_home_hub(device_id: Optional[str]) -> bool:
    """Determine if a casting/control action should be delegated to Home PC Hub."""
    if not is_cloud_instance():
        return False
    if not device_id or device_id == "web_receiver":
        return False
    # If device is a physical home TV (TCL, Hisense, 192.168.x.x)
    return True

async def forward_to_home_hub(
    path: str,
    method: str = "POST",
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 25.0
) -> Dict[str, Any]:
    """Forward an action directly to Home PC Hub tunnel and return response."""
    hub_url = await get_active_home_hub_url()
    if not hub_url:
        return {
            "status": "error",
            "message": "Home Laptop Hub is offline. Turn on your laptop to cast directly to your Smart TV, or open /tv in your TV browser.",
            "tv_online": False,
            "offline_reason": "laptop_hub_offline"
        }

    clean_path = path if path.startswith("/") else f"/{path}"
    target_url = f"{hub_url}{clean_path}"
    headers = {
        "bypass-tunnel-reminder": "true",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            if method.upper() == "POST":
                resp = await client.post(target_url, json=json_data, params=params, headers=headers)
            elif method.upper() == "GET":
                resp = await client.get(target_url, params=params, headers=headers)
            else:
                resp = await client.request(method, target_url, json=json_data, params=params, headers=headers)

            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception:
                    return {"status": "ok", "raw": resp.text}
            else:
                return {
                    "status": "error",
                    "code": resp.status_code,
                    "message": f"Home Hub returned HTTP {resp.status_code}: {resp.text[:120]}"
                }
    except httpx.TimeoutException:
        return {
            "status": "error",
            "message": "Home Hub request timed out. Please verify your laptop is awake and connected to Wi-Fi."
        }
    except Exception as e:
        logger.error(f"Error forwarding request to Home Hub: {e}")
        return {
            "status": "error",
            "message": f"Failed to relay command to Home Hub: {str(e)}"
        }
