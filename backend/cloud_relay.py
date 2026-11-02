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

async def probe_tunnel(url: str, timeout: float = 1.8) -> bool:
    """Fast health probe to determine if Home PC Hub tunnel is actively alive."""
    try:
        clean = url.rstrip("/")
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            r = await client.get(
                f"{clean}/api/auth/status",
                headers={"bypass-tunnel-reminder": "true"}
            )
            return r.status_code == 200
    except Exception:
        return False

async def get_active_home_hub_url(force_refresh: bool = False) -> Optional[str]:
    """Retrieve verified active Home PC Hub Cloudflare tunnel URL with fast health check."""
    global _cached_home_hub, _cached_home_hub_exp
    now = time.time()
    if not force_refresh and now < _cached_home_hub_exp:
        return _cached_home_hub

    cand = None
    # 1. Try local endpoint.json
    ep_file = BASE_DIR / "endpoint.json"
    if ep_file.exists():
        try:
            data = json.loads(ep_file.read_text(encoding="utf-8"))
            url = data.get("hub_url")
            if url and "trycloudflare.com" in url:
                cand = url
        except Exception:
            pass

    # 2. Fetch from GitHub raw fallback
    if not cand:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t={int(now)}")
                if res.status_code == 200:
                    data = res.json()
                    url = data.get("hub_url")
                    if url and "trycloudflare.com" in url:
                        cand = url
        except Exception as e:
            logger.debug(f"GitHub endpoint fetch notice: {e}")

    if not cand:
        _cached_home_hub = None
        _cached_home_hub_exp = now + 15.0
        return None

    clean = cand.rstrip("/")
    # Quick probe: if laptop is asleep/off, this fails in 1.8s instead of hanging for 70s!
    is_alive = await probe_tunnel(clean, timeout=1.8)
    if is_alive:
        _cached_home_hub = clean
        _cached_home_hub_exp = now + 45.0  # Cache verified candidate
        return clean

    _cached_home_hub = None
    _cached_home_hub_exp = now + 12.0  # Cache offline state
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
    timeout: float = 6.0
) -> Dict[str, Any]:
    """Forward an action directly to Home PC Hub tunnel with fast fallback if laptop is off."""
    hub_url = await get_active_home_hub_url()
    if not hub_url:
        return {
            "status": "fallback",
            "use_web_cast": True,
            "message": "Direct phone-to-TV casting active. Select your TV from the Cast prompt.",
            "tv_online": True,
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
            elif resp.status_code in (502, 503, 504):
                logger.warning(f"Home Hub tunnel returned {resp.status_code}")
                await get_active_home_hub_url(force_refresh=True)
            else:
                return {
                    "status": "error",
                    "code": resp.status_code,
                    "message": f"Home Hub returned HTTP {resp.status_code}: {resp.text[:120]}"
                }
    except Exception as e:
        logger.debug(f"Home hub forward notice: {e}")

    # If tunnel truly unreachable, seamlessly signal frontend to trigger in-browser phone-to-TV Web Cast!
    return {
        "status": "fallback",
        "use_web_cast": True,
        "message": "Direct phone-to-TV casting active. Select your TV from the Cast prompt.",
        "tv_online": True,
        "offline_reason": "laptop_hub_offline"
    }
