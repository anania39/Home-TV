import os
import subprocess
import re
import json
import shutil
import asyncio
import time
import httpx
from urllib.parse import quote
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import PORT, SERVER_IP, STATIC_DIR, MEDIA_DIR, is_local_network, BASE_DIR, NO_DEVICES
from .discovery import device_manager
from .dlna_controller import dlna_controller
from .hisense_remote import get_hisense_remote, send_wake_on_lan
from .iptv_manager import iptv_manager
from .stream_proxy import proxy_stream, segment_engine, session_manager
from .websocket_manager import ws_manager
from .tunnel import tunnel_manager
from .google_cast_controller import google_cast_controller
from .sports_scraper import sports_scraper, CATEGORIES
from .dns_service_manager import is_daemon_running, start_daemon, get_status as get_dns_service_status, set_global_no_ads, set_device_no_ads
from .device_scanner import device_scanner
from .asus_router_controller import asus_router_controller

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("tv_hub")

async def monitor_tv_status_loop():
    """Real feedback: continuously query the active TV hardware for power & transport state."""
    while True:
        try:
            await asyncio.sleep(7.0)
            selected_id = device_manager.selected_device_id
            dev = device_manager.get_device(selected_id) if selected_id != "web_receiver" else None

            if dev and dev.get("is_google_tv"):
                try:
                    cast_status = await asyncio.to_thread(google_cast_controller.get_status, dev["ip"])
                    ws_manager.update_state({
                        "selected_device_id": selected_id,
                        "tv_online": cast_status.get("tv_online", False),
                        "state": cast_status.get("state", "IDLE"),
                        "status_text": cast_status.get("status_text", f"{dev['name']} Ready"),
                        "volume": cast_status.get("volume", 20),
                        "muted": cast_status.get("muted", False)
                    })
                    await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)
                except Exception as e:
                    logger.debug(f"Google Cast status monitor error: {e}")

            elif dev and dev.get("av_transport_url"):
                av_url = dev["av_transport_url"]
                rc_url = dev.get("rendering_control_url")
                try:
                    transport = await dlna_controller.get_transport_info(av_url)
                    raw_state = transport.get("state", "STANDBY")

                    if raw_state not in ["STANDBY", "UNKNOWN", "ERROR"]:
                        tv_online = True
                        current_title = ws_manager.current_state.get("title", "")
                        if current_title.startswith("http://") or current_title.startswith("https://") or "proxy?url=" in current_title or "%2F" in current_title or "googlevideo.com" in current_title:
                            current_title = ""
                        
                        if raw_state == "PLAYING":
                            display_state = "PLAYING"
                            status_text = f"Playing: {current_title}" if current_title else f"{dev['name']} Playing"
                        elif raw_state in ["STOPPED", "NO_MEDIA_PRESENT"]:
                            display_state = "IDLE"
                            status_text = "TV Ready / Idle"
                        elif raw_state == "PAUSED_PLAYBACK":
                            display_state = "PAUSED"
                            status_text = "Playback Paused"
                        else:
                            display_state = raw_state
                            status_text = f"TV: {raw_state}"

                        vol = await dlna_controller.get_volume(rc_url) if rc_url else -1
                        updates = {
                            "selected_device_id": selected_id,
                            "tv_online": True,
                            "state": display_state,
                            "status_text": status_text,
                        }
                        if vol >= 0:
                            updates["volume"] = vol

                        ws_manager.update_state(updates)
                        await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)
                    else:
                        ws_manager.update_state({
                            "tv_online": False,
                            "state": "STANDBY",
                            "status_text": f"{dev['name']} is in Standby"
                        })
                        await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)
                except Exception:
                    ws_manager.update_state({
                        "tv_online": False,
                        "state": "STANDBY",
                        "status_text": f"{dev['name']} is in Standby"
                    })
                    await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)

            elif selected_id == "web_receiver":
                is_active = len(ws_manager.receivers) > 0
                ws_manager.update_state({
                    "tv_online": is_active,
                    "state": ws_manager.current_state.get("state", "IDLE") if is_active else "STANDBY",
                    "status_text": "Web Receiver Connected" if is_active else "No Browser Receiver Connected"
                })
                await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Status monitor error: {e}")

# Background task for periodic SSDP scan
async def periodic_scan_task():
    # Initial scan
    await device_manager.scan(timeout=3.0)
    while True:
        try:
            await asyncio.sleep(45.0)
            await device_manager.scan(timeout=2.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Periodic scan warning: {e}")

def start_mdns_broadcast(port: int):
    """Broadcast tvhub.local on home Wi-Fi so phones/tablets can open http://tvhub.local:8000 without typing numbers."""
    try:
        from zeroconf import Zeroconf, ServiceInfo
        info = ServiceInfo(
            "_http._tcp.local.",
            "TV Hub._http._tcp.local.",
            addresses=[socket.inet_aton(SERVER_IP)],
            port=port,
            properties={"path": "/"},
            server="tvhub.local."
        )
        zc = Zeroconf()
        zc.register_service(info)
        logger.info(f"🌐 Permanent Local mDNS Active: http://tvhub.local:{port}")
        return zc
    except Exception as e:
        logger.debug(f"mDNS registration notice: {e}")
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 TV HUB SERVER STARTED")
    logger.info(f"📱 Local Phone Controller: http://{SERVER_IP}:{PORT}")
    logger.info(f"🌐 Permanent Local Name:   http://tvhub.local:{PORT}")
    logger.info(f"📺 TV Web Receiver:        http://{SERVER_IP}:{PORT}/tv")
    logger.info("=" * 60)
    
    # Reload curated channels
    iptv_manager.load_default_playlist()

    scan_task = None
    monitor_task = None
    health_task = None
    mdns_zc = None

    # Ensure 24/7 Persistent Background DNS Ad-Blocker Daemon is active
    try:
        if not is_daemon_running():
            start_daemon()
        logger.info(f"🛡️ 24/7 Persistent DNS Ad-Blocker Daemon active on port 53 (Server IP: {SERVER_IP})")
    except Exception as e:
        logger.warning(f"DNS Daemon manager notice: {e}")

    if not NO_DEVICES:
        # Dynamic network discovery active
        device_manager._init_network_devices()

        # Start local mDNS broadcast (http://tvhub.local:8000)
        mdns_zc = start_mdns_broadcast(PORT)

        # Start public tunnel in background
        tunnel_manager.start()

        scan_task = asyncio.create_task(periodic_scan_task())
        monitor_task = asyncio.create_task(monitor_tv_status_loop())
        health_task = asyncio.create_task(periodic_stream_health_task())
    else:
        device_manager.selected_device_id = "web_receiver"

    yield
    # Shutdown
    if mdns_zc:
        try:
            mdns_zc.close()
        except Exception:
            pass
    if scan_task:
        scan_task.cancel()
    if monitor_task:
        monitor_task.cancel()
    if health_task:
        health_task.cancel()
    if not NO_DEVICES:
        tunnel_manager.stop(kill_process=False)

app = FastAPI(title="TV Hub", lifespan=lifespan)

# Allow CORS for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication / Local Network check dependency
def verify_local_network(request: Request):
    # Allow requests routed through secure public tunnel
    host = request.headers.get("host", "")
    if "trycloudflare.com" in host or "cf-ray" in request.headers:
        return "Public Tunnel Client"

    client_ip = request.client.host if request.client else "127.0.0.1"
    if not is_local_network(client_ip):
        logger.warning(f"Unauthorized external access attempt from {client_ip}")
        raise HTTPException(status_code=403, detail="Access denied: You must be connected to the same local Wi-Fi network or use the verified public link.")
    return client_ip

# --- Models ---
class CastRequest(BaseModel):
    url: str
    title: Optional[str] = "Live Stream"
    mime_type: Optional[str] = "video/mp4"
    use_proxy: Optional[bool] = False
    device_id: Optional[str] = None
    channel_id: Optional[str] = None
    logo: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    source_index: Optional[int] = 0

class PlaybackActionRequest(BaseModel):
    action: str  # play, pause, stop, seek, speed, rate, subtitles, quality
    value: Optional[str] = None
    lang: Optional[str] = None
    url: Optional[str] = None
    is_absolute: Optional[bool] = False
    device_id: Optional[str] = None

class VolumeRequest(BaseModel):
    volume: Optional[int] = None
    delta: Optional[int] = None
    mute: Optional[bool] = None
    device_id: Optional[str] = None

class RemoteKeyRequest(BaseModel):
    key: str
    device_id: Optional[str] = None

class GlobalAdblockRequest(BaseModel):
    enabled: bool

class DeviceAdblockRequest(BaseModel):
    enabled: bool

class RouterAutoConfigRequest(BaseModel):
    router_ip: Optional[str] = None
    username: Optional[str] = 'admin'
    password: str

class DeviceSelectRequest(BaseModel):
    device_id: str

class ManualDeviceRequest(BaseModel):
    ip: str
    port: Optional[int] = 38400
    name: Optional[str] = "Smart TV"

class AddChannelRequest(BaseModel):
    name: str
    url: str
    group: Optional[str] = "Custom"
    logo: Optional[str] = ""

class ImportPlaylistRequest(BaseModel):
    url: Optional[str] = None
    content: Optional[str] = None
    append: Optional[bool] = True

# --- Stream Health & Failover Management ---
STREAM_HEALTH_FILE = BASE_DIR / "backend" / ".stream_health.json"
_stream_health_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}  # url -> (result, timestamp)
_last_good_sources: Dict[str, str] = {}  # channel_id -> url

def _load_stream_health():
    global _last_good_sources
    if STREAM_HEALTH_FILE.exists():
        try:
            _last_good_sources = json.loads(STREAM_HEALTH_FILE.read_text(encoding="utf-8"))
        except Exception:
            _last_good_sources = {}

def _save_stream_health():
    try:
        STREAM_HEALTH_FILE.write_text(json.dumps(_last_good_sources, indent=2), encoding="utf-8")
    except Exception:
        pass

async def probe_stream_health(url: str, timeout: float = 2.5) -> Dict[str, Any]:
    now = time.time()
    if url in _stream_health_cache:
        cached, ts = _stream_health_cache[url]
        if now - ts < 60.0:
            return cached

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Range": "bytes=0-2048",
        "Accept": "*/*"
    }
    t0 = time.perf_counter()
    ok = False
    status_code = 0
    ttfb_ms = 0.0

    try:
        async with httpx.AsyncClient(verify=False, timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            ttfb_ms = round((time.perf_counter() - t0) * 1000, 2)
            status_code = resp.status_code
            ok = resp.status_code in [200, 206]
    except Exception as e:
        ttfb_ms = round((time.perf_counter() - t0) * 1000, 2)
        status_code = 504 if "timeout" in str(e).lower() else 502
        ok = False

    result = {
        "ok": ok,
        "http": status_code,
        "ttfb_ms": ttfb_ms,
        "url": url
    }
    _stream_health_cache[url] = (result, now)
    return result

async def periodic_stream_health_task():
    """Background task running periodically to probe channels and revive them without triggering 429s."""
    _load_stream_health()
    await asyncio.sleep(30.0)  # Wait for startup
    while True:
        try:
            from urllib.parse import urlparse
            active_stream = session_manager._latest_stream_url
            active_domain = urlparse(active_stream).netloc if active_stream else ""

            for ch in iptv_manager.channels:
                cid = ch.get("id")
                sources = ch.get("sources", [])
                for s in sources:
                    s_url = s.get("url")
                    if not s_url:
                        continue
                    s_domain = urlparse(s_url).netloc
                    # CRITICAL: Never probe the domain currently streaming to the TV!
                    if active_domain and s_domain == active_domain:
                        continue
                    probe = await probe_stream_health(s_url, timeout=3.0)
                    if probe.get("ok"):
                        if cid and cid not in _last_good_sources:
                            _last_good_sources[cid] = s_url
                        break
                await asyncio.sleep(12.0)  # gentle 12s spacing so we never exhaust upstream rate limit
            _save_stream_health()
            await asyncio.sleep(600.0)  # Every ~10 mins
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Periodic stream health probe notice: {e}")
            await asyncio.sleep(60.0)

# --- API Endpoints ---

@app.get("/api/auth/status")
async def get_auth_status(request: Request, client_ip: str = Depends(verify_local_network)):
    """Verify client is connected and return network info."""
    return {
        "authenticated": True,
        "client_ip": client_ip,
        "server_ip": SERVER_IP,
        "port": PORT,
        "network": "Verified Connection",
        "public_url": tunnel_manager.get_url(),
        "short_url": tunnel_manager.get_short_url()
    }

@app.get("/api/devices")
async def get_devices():
    devices = device_manager.get_devices()
    web_rec = {
        "id": "web_receiver",
        "name": f"TV Web Receiver (Browser at /tv)",
        "ip": SERVER_IP,
        "type": "browser",
        "manufacturer": "TV Hub",
        "model": "HTML5 Web Receiver",
        "is_hisense": False,
        "is_active": len(ws_manager.receivers) > 0
    }
    # Physical TVs appear first so user's actual Smart TVs are immediately accessible
    full_list = (devices + [web_rec]) if devices else [web_rec]
    selected_id = device_manager.selected_device_id
    if not selected_id or (selected_id == "web_receiver" and len(devices) > 0):
        saved_id = device_manager._load_selected_device()
        if saved_id and any(d["id"] == saved_id for d in devices):
            selected_id = saved_id
        else:
            hisense_match = next((d["id"] for d in devices if d.get("is_hisense")), None)
            selected_id = hisense_match or devices[0]["id"]
        device_manager.selected_device_id = selected_id
    return {
        "devices": full_list,
        "selected_device_id": selected_id or "web_receiver"
    }

@app.post("/api/devices/scan")
async def scan_devices():
    discovered = await device_manager.scan(timeout=3.0)
    return {"status": "ok", "count": len(discovered), "devices": discovered}

@app.post("/api/devices/select")
async def select_device(req: DeviceSelectRequest):
    success = device_manager.select_device(req.device_id)
    if success:
        dev = device_manager.get_device(req.device_id)
        name = dev["name"] if dev else ("TV Web Receiver" if req.device_id == "web_receiver" else req.device_id)
        ip = dev["ip"] if dev else SERVER_IP
        
        # Immediate status probe for newly selected TV so UI updates instantly
        updates = {"selected_tv_name": name, "selected_tv_ip": ip}
        if dev and dev.get("is_google_tv"):
            try:
                cast_status = await asyncio.to_thread(google_cast_controller.get_status, dev["ip"])
                updates.update({
                    "tv_online": cast_status.get("tv_online", False),
                    "state": cast_status.get("state", "IDLE"),
                    "status_text": cast_status.get("status_text", f"{name} Ready"),
                    "volume": cast_status.get("volume", 20),
                    "muted": cast_status.get("muted", False)
                })
            except Exception:
                pass
        elif dev and dev.get("av_transport_url"):
            try:
                transport = await dlna_controller.get_transport_info(dev["av_transport_url"])
                raw_state = transport.get("state", "STANDBY")
                is_online = raw_state not in ["STANDBY", "UNKNOWN", "ERROR"]
                updates.update({
                    "tv_online": is_online,
                    "state": "IDLE" if raw_state in ["STOPPED", "NO_MEDIA_PRESENT"] else raw_state,
                    "status_text": f"{name} Ready" if is_online else f"{name} is in Standby"
                })
            except Exception:
                updates.update({
                    "tv_online": False,
                    "state": "STANDBY",
                    "status_text": f"{name} is in Standby"
                })

        ws_manager.update_state(updates)
        await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)
        await ws_manager.broadcast_to_controllers("tv_selected", {"device_id": req.device_id, "name": name, "ip": ip})
        return {"status": "ok", "selected_device_id": req.device_id, "name": name}
    raise HTTPException(status_code=404, detail="Device not found")

@app.post("/api/devices/manual")
async def add_manual_device(req: ManualDeviceRequest):
    dev = device_manager.add_manual_device(req.ip, req.port, req.name)
    return {"status": "ok", "device": dev}

# --- Network Devices & Enterprise DNS Ad-Blocker Endpoints ---

@app.get("/api/network/devices")
async def get_network_devices(request: Request):
    client_ip = request.client.host if request.client else None
    devices = device_scanner.scan(client_ip=client_ip, force_refresh=False)
    return {
        "status": "ok",
        "devices": devices,
        "count": len(devices),
        "client_ip": client_ip,
        "dns_ip": SERVER_IP
    }

@app.post("/api/network/scan")
async def scan_network(request: Request):
    client_ip = request.client.host if request.client else None
    devices = device_scanner.scan(client_ip=client_ip, force_refresh=True)
    return {
        "status": "ok",
        "devices": devices,
        "count": len(devices),
        "client_ip": client_ip
    }

@app.get("/api/adblock/status")
async def get_adblock_status():
    return get_dns_service_status()

@app.post("/api/adblock/toggle")
async def toggle_global_adblock(req: GlobalAdblockRequest):
    updated = set_global_no_ads(req.enabled)
    return {
        "status": "ok",
        "global_enabled": updated.get("global_enabled", req.enabled),
        "adblock_status": get_dns_service_status()
    }

@app.post("/api/network/device/{ip}/adblock")
async def set_device_adblock(ip: str, req: DeviceAdblockRequest):
    updated = set_device_no_ads(ip, req.enabled)
    return {
        "status": "ok",
        "ip": ip,
        "enabled": req.enabled,
        "device_rules": updated.get("device_rules", {})
    }


@app.get("/api/adblock/repositories")
async def get_adblock_repositories():
    try:
        from .blocklist_manager import blocklist_manager
        return {"status": "ok", "repositories": blocklist_manager.meta}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/adblock/stats/reset")
async def reset_adblock_stats():
    from .dns_service_manager import reset_stats
    reset_stats()
    return {"status": "ok", "message": "Ad-block statistics reset successfully"}

@app.post("/api/adblock/repositories/sync")
async def sync_adblock_repositories():
    try:
        from .blocklist_manager import blocklist_manager
        meta = blocklist_manager.update_sources()
        return {"status": "ok", "message": f"Synchronized {meta.get('total_domains', 0):,} domains from Pi-hole & AdGuard", "repositories": meta}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/router/status")
async def get_router_status():
    from .config import get_default_gateway
    gw_ip = get_default_gateway()
    reach = asus_router_controller.check_reachability(gw_ip)
    cfg = asus_router_controller.get_router_status()
    return {
        "status": "ok",
        "reachability": reach,
        "config": cfg,
        "router_ip": gw_ip,
        "dns_ip": SERVER_IP
    }

@app.post("/api/router/auto_configure")
async def auto_configure_router(req: RouterAutoConfigRequest):
    from .config import get_default_gateway
    gw_ip = req.router_ip or get_default_gateway()
    result = asus_router_controller.auto_configure(
        router_ip=gw_ip,
        username=req.username or "admin",
        password=req.password,
        dns_server_ip=SERVER_IP
    )
    return result

@app.post("/api/router/forget")
async def forget_router():
    state_file = BASE_DIR / "data" / "router_config.json"
    if os.path.exists(state_file):
        try:
            os.remove(state_file)
        except Exception:
            pass
    return {"status": "ok", "message": "Router configuration state reset"}

@app.post("/api/adblock/protect_this_pc")
async def protect_this_pc():
    bat_path = os.path.join(BASE_DIR, "protect_this_pc.bat")
    try:
        if sys.platform == "win32":
            subprocess.Popen(["powershell", "-NoProfile", "-Command", f"Start-Process '{bat_path}' -Verb RunAs"])
            return {"status": "ok", "message": "UAC prompt launched! Click 'Yes' to enable ad-blocking on this PC."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Only available on Windows host"}

@app.get("/api/youtube/search")
async def search_youtube_endpoint(q: str):
    from .media_resolver import media_resolver
    items = await media_resolver.search_youtube(q, limit=8)
    return {"status": "ok", "query": q, "results": items}

@app.get("/api/media/subtitle")
async def proxy_subtitle(url: str):
    """Proxies remote WebVTT subtitle track with proper CORS and MIME headers."""
    try:
        async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                vtt_text = resp.text
                if not vtt_text.startswith("WEBVTT"):
                    vtt_text = "WEBVTT\n\n" + vtt_text
                return Response(
                    content=vtt_text.encode("utf-8"),
                    media_type="text/vtt; charset=utf-8",
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "text/vtt; charset=utf-8",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
    except Exception as e:
        logger.warning(f"Subtitle proxy error: {e}")
    return Response(content="WEBVTT\n\n", media_type="text/vtt")

@app.get("/api/media/resolve")
async def resolve_media_url(url: str):
    from .media_resolver import media_resolver
    return await media_resolver.resolve(url)

@app.post("/api/cast")
async def cast_media(req: CastRequest, request: Request, client_ip: str = Depends(verify_local_network)):
    device_id = req.device_id or device_manager.selected_device_id
    raw_stream_url = req.url.strip()
    title = req.title or "Live Stream"

    # Universal Ad-Free Media Resolver:
    # Automatically extracts clean, ad-free direct streams from YouTube, movie platforms & web players
    try:
        from .media_resolver import media_resolver
        preferred_title = req.title if req.title not in ("Live Stream", "Video Stream") else None
        resolved = await media_resolver.resolve(raw_stream_url, preferred_title=preferred_title)
        if resolved.get("resolved") and resolved.get("stream_url"):
            logger.info(f"Resolved clean stream for {resolved.get('source_type')}: {resolved.get('title')}")
            raw_stream_url = resolved["stream_url"]
            if not req.title or req.title in ("Video Stream", "Live Stream"):
                title = resolved.get("title") or title
            if resolved.get("mime_type"):
                req.mime_type = resolved["mime_type"]
        elif not media_resolver.is_direct_stream(raw_stream_url):
            logger.warning(f"Could not extract video stream from webpage: {raw_stream_url}")
            return {
                "status": "error",
                "message": resolved.get("error") or "Could not extract video from this webpage. Please paste the direct video or embed player link."
            }
    except Exception as e:
        logger.warning(f"Media resolution notice: {e}")

    dev = device_manager.get_device(device_id) if device_id != "web_receiver" else None

    # Step 1: Compute version & update state BEFORE any await to guarantee atomic monotonicity
    my_version = ws_manager.next_version()
    is_stale = lambda: my_version != ws_manager.cast_version

    target_tv_ip = dev.get("ip") if dev else None
    custom_headers = resolved.get("headers") if ('resolved' in locals() and isinstance(resolved, dict)) else None
    active_sid = session_manager.start_session(target_tv_ip, raw_stream_url, headers=custom_headers)

    # Proxied URLs:
    relative_proxy_url = f"/api/stream/proxy?url={quote(raw_stream_url, safe='')}&sid={active_sid}"
    lan_proxy_url = f"http://{SERVER_IP}:{PORT}/api/stream/proxy?url={quote(raw_stream_url, safe='')}&sid={active_sid}"

    # For Google TV / Android TV, direct Google video & HTTPS MP4 play natively with zero proxy latency
    if dev and dev.get("is_google_tv") and ("googlevideo.com" in raw_stream_url or not req.use_proxy):
        tv_stream_url = raw_stream_url
    elif req.use_proxy or (raw_stream_url.startswith("https://") and device_id != "web_receiver"):
        tv_stream_url = lan_proxy_url if (dev and (dev.get("av_transport_url") or dev.get("is_google_tv"))) else relative_proxy_url
    else:
        tv_stream_url = raw_stream_url

    web_stream_url = relative_proxy_url if req.use_proxy else raw_stream_url

    # Ensure all channel sources are properly proxied with active_sid for seamless client failover
    proxied_sources = []
    for s in (req.sources or []):
        s_url = s.get("url") if isinstance(s, dict) else s
        if s_url:
            p_url = f"/api/stream/proxy?url={quote(s_url, safe='')}&sid={active_sid}" if req.use_proxy else s_url
            proxied_sources.append({"url": p_url, "type": "hls"})
    if not proxied_sources and web_stream_url:
        proxied_sources = [{"url": web_stream_url, "type": "hls"}]

    # Single output path determination
    mode = "google_tv" if (dev and dev.get("is_google_tv")) else ("dlna" if (dev and dev.get("av_transport_url")) else "web_receiver")

    # Update state immediately at entry (BEFORE any await)
    state_payload = {
        "channel_id": req.channel_id,
        "url": web_stream_url,
        "title": title,
        "logo": req.logo or "",
        "sources": proxied_sources,
        "source_index": req.source_index or 0,
        "version": my_version,
        "state": "PLAYING"
    }
    if 'resolved' in locals() and isinstance(resolved, dict):
        if resolved.get("duration"):
            state_payload["duration"] = resolved["duration"]
            state_payload["duration_str"] = resolved.get("duration_str", "Live")
        if resolved.get("thumbnail"):
            state_payload["thumbnail"] = resolved["thumbnail"]
        if resolved.get("subtitles"):
            state_payload["subtitles"] = resolved["subtitles"]
        if resolved.get("qualities"):
            state_payload["qualities"] = resolved["qualities"]
        if resolved.get("quality_urls"):
            state_payload["quality_urls"] = resolved["quality_urls"]
    ws_manager.update_state(state_payload)

    # Clear old prefetched chunks so channel switch is 100% clean with zero overlap
    segment_engine.clear_for_channel_switch()

    # Fire-and-forget prewarm (do NOT await, preventing channel switch delays)
    prewarm_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    if "televizia" in raw_stream_url or "televiziebi" in raw_stream_url:
        prewarm_headers["Referer"] = "https://www.televizia.org/"
        prewarm_headers["Origin"] = "https://www.televizia.org"
    asyncio.create_task(segment_engine.prewarm_channel(raw_stream_url, prewarm_headers))

    # Path A: Web Receiver ONLY (Never touch DLNA/hardware)
    if mode == "web_receiver":
        await ws_manager.send_to_receivers("play", {
            "url": web_stream_url,
            "title": title,
            "channel_id": req.channel_id,
            "logo": req.logo or "",
            "sources": proxied_sources,
            "source_index": req.source_index or 0,
            "sources_total": len(proxied_sources),
            "version": my_version
        })
        await ws_manager.broadcast_to_controllers("playback_update", ws_manager.current_state)
        return {
            "status": "ok",
            "mode": "web_receiver",
            "version": my_version,
            "tv_online": True,
            "title": title,
            "url": web_stream_url,
            "duration": resolved.get("duration", 0) if ('resolved' in locals() and isinstance(resolved, dict)) else 0,
            "duration_str": resolved.get("duration_str", "") if ('resolved' in locals() and isinstance(resolved, dict)) else "",
            "thumbnail": resolved.get("thumbnail", "") if ('resolved' in locals() and isinstance(resolved, dict)) else "",
            "subtitles": resolved.get("subtitles", []) if ('resolved' in locals() and isinstance(resolved, dict)) else [],
            "qualities": resolved.get("qualities", ["Auto"]) if ('resolved' in locals() and isinstance(resolved, dict)) else ["Auto"],
            "quality_urls": resolved.get("quality_urls", {}) if ('resolved' in locals() and isinstance(resolved, dict)) else {}
        }

    # Path B: Physical TV (DLNA / Google TV) - Serialized with Lock & Staleness guards
    tv_is_active = True
    async with ws_manager.cast_lock:
        if is_stale():
            logger.info(f"Cast v{my_version} superseded by v{ws_manager.cast_version} before acquisition")
            return {"status": "superseded", "version": my_version, "mode": mode}

        if mode == "google_tv":
            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}
            first_sub = (resolved.get("subtitles") or [{}])[0].get("url") if ('resolved' in locals() and isinstance(resolved, dict)) else None
            is_live = False
            if req.channel_id or ("iptv" in raw_stream_url.lower()) or (isinstance(resolved, dict) and resolved.get("source_type") == "iptv"):
                is_live = True
            cast_stream_type = "LIVE" if is_live else "BUFFERED"
            ok = await asyncio.to_thread(google_cast_controller.cast_media, dev["ip"], tv_stream_url, title, req.mime_type or "video/mp4", first_sub, stream_type=cast_stream_type)
            tv_is_active = ok
            if not ok:
                logger.warning(f"Google Cast to {dev['name']} at {dev['ip']} returned false")

        elif mode == "dlna":
            av_url = dev["av_transport_url"]
            tv_ip = dev.get("ip")
            tv_port = dev.get("port", 38400)

            # Fast Pre-flight reachability probe (0.45s max)
            # Instantly detects if the TV is in standby or sleeping so we don't stall the user for 15 seconds
            tv_reachable = True
            if tv_ip:
                try:
                    _, writer = await asyncio.wait_for(asyncio.open_connection(tv_ip, tv_port), timeout=0.45)
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    tv_reachable = False

            if not tv_reachable:
                logger.info(f"DLNA TV {dev['name']} ({tv_ip}) is in standby/unreachable. Broadcasting WoL...")
                send_wake_on_lan(["d4:ab:cd:50:e5:d3", "18:30:0c:9e:7e:fc"])
                ws_manager.update_state({
                    "tv_online": False,
                    "state": "STANDBY",
                    "title": title,
                    "status_text": f"{dev['name']} is in Standby"
                })
                await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)
                return {
                    "status": "waking",
                    "mode": mode,
                    "version": my_version,
                    "tv_online": False,
                    "title": title,
                    "url": web_stream_url,
                    "message": f"TV '{dev['name']}' is in Standby or turned off. Wake signal sent! Turn on TV or select TCL TV / TV Web Receiver from the dropdown."
                }

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            # Clean Hardware TV Pipeline Transition:
            # Check if TV is actively playing a stream from a previous channel
            try:
                cur_info = await dlna_controller.get_transport_info(av_url)
                cur_state = cur_info.get("state", "STOPPED")
            except Exception:
                cur_state = "STOPPED"

            # If TV is currently PLAYING, TRANSITIONING or PAUSED from a previous channel,
            # cleanly stop it and wait for STOPPED state (up to 1.2s) so the TV's GStreamer demuxer
            # and hardware decoder ring buffers are 100% flushed.
            # This completely eliminates channel switching oscillation and audio/video desync.
            if cur_state in ("PLAYING", "TRANSITIONING", "PAUSED_PLAYBACK"):
                try:
                    await dlna_controller.stop(av_url)
                    for _ in range(8):
                        await asyncio.sleep(0.12)
                        if is_stale():
                            return {"status": "superseded", "version": my_version, "mode": mode}
                        chk = await dlna_controller.get_transport_info(av_url)
                        if chk.get("state") in ("STOPPED", "NO_MEDIA_PRESENT"):
                            break
                except Exception as e:
                    logger.debug(f"DLNA clean stop notice: {e}")

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)
            if not set_ok:
                try:
                    await dlna_controller.stop(av_url)
                    await asyncio.sleep(0.2)
                except Exception as e:
                    logger.debug(f"DLNA stop notice: {e}")

                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            if set_ok:
                tv_is_active = True
                await asyncio.sleep(0.12)
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                await dlna_controller.play(av_url)
            else:
                tv_online = ws_manager.current_state.get("tv_online", True)
                if not tv_online:
                    logger.info(f"TV {dev['name']} is in standby/offline. Sending WoL...")
                    send_wake_on_lan(["d4:ab:cd:50:e5:d3", "18:30:0c:9e:7e:fc"])
                tv_is_active = False

    if not tv_is_active:
        ws_manager.update_state({
            "tv_online": False,
            "state": "STANDBY",
            "title": title,
            "status_text": f"{dev['name']} is in Standby (Wake packet sent)"
        })
        await ws_manager.broadcast_to_controllers("tv_status_sync", ws_manager.current_state)
        return {
            "status": "waking",
            "mode": mode,
            "version": my_version,
            "tv_online": False,
            "title": title,
            "url": web_stream_url,
            "message": f"TV '{dev['name']}' is currently in Standby or unreachable. Wake signal broadcasted. Please turn on your TV or select another active device from the dropdown."
        }

    # Update state and broadcast
    ws_manager.update_state({
        "tv_online": True,
        "state": "PLAYING",
        "title": title,
        "url": web_stream_url,
        "version": my_version
    })
    await ws_manager.broadcast_to_controllers("playback_update", ws_manager.current_state)

    res_payload = {
        "status": "ok",
        "mode": mode,
        "version": my_version,
        "tv_online": True,
        "title": title,
        "url": web_stream_url
    }
    if 'resolved' in locals() and isinstance(resolved, dict):
        res_payload["duration"] = resolved.get("duration", 0)
        res_payload["duration_str"] = resolved.get("duration_str", "")
        res_payload["thumbnail"] = resolved.get("thumbnail", "")
        res_payload["subtitles"] = resolved.get("subtitles", [])
        res_payload["qualities"] = resolved.get("qualities", ["Auto"])
        res_payload["quality_urls"] = resolved.get("quality_urls", {})
    return res_payload

@app.post("/api/playback/action")
async def playback_action(req: PlaybackActionRequest):
    device_id = req.device_id or device_manager.selected_device_id
    dev = device_manager.get_device(device_id) if device_id != "web_receiver" else None
    action = req.action.lower()

    if dev and dev.get("is_google_tv"):
        if action == "play":
            await asyncio.to_thread(google_cast_controller.play, dev["ip"])
            ws_manager.update_state({"state": "PLAYING"})
        elif action == "pause":
            await asyncio.to_thread(google_cast_controller.pause, dev["ip"])
            ws_manager.update_state({"state": "PAUSED"})
        elif action == "stop":
            await asyncio.to_thread(google_cast_controller.stop, dev["ip"])
            ws_manager.update_state({"state": "STOPPED"})
        elif action == "seek" and req.value:
            try:
                sec = float(req.value)
                await asyncio.to_thread(google_cast_controller.seek, dev["ip"], sec, req.is_absolute or False)
            except Exception:
                pass
        elif action in ("speed", "rate") and req.value:
            try:
                rate = float(req.value)
                await asyncio.to_thread(google_cast_controller.set_playback_rate, dev["ip"], rate)
                ws_manager.update_state({"speed": rate})
            except Exception:
                pass
        elif action == "subtitles":
            try:
                if req.value == "off":
                    await asyncio.to_thread(google_cast_controller.disable_subtitles, dev["ip"])
                else:
                    await asyncio.to_thread(google_cast_controller.enable_subtitles, dev["ip"])
            except Exception:
                pass
        elif action == "quality":
            target_q_url = req.url or (req.value if req.value and req.value.startswith("http") else None)
            if target_q_url:
                try:
                    await asyncio.to_thread(google_cast_controller.cast_media, dev["ip"], target_q_url, ws_manager.current_state.get("title", "Video"))
                except Exception:
                    pass

    elif dev and dev.get("av_transport_url"):
        av_url = dev["av_transport_url"]
        if action == "play":
            speed_val = req.value if req.value else "1"
            await dlna_controller.play(av_url, speed=speed_val)
            ws_manager.update_state({"state": "PLAYING"})
        elif action == "pause":
            await dlna_controller.pause(av_url)
            ws_manager.update_state({"state": "PAUSED"})
        elif action == "stop":
            await dlna_controller.stop(av_url)
            ws_manager.update_state({"state": "STOPPED"})
        elif action == "seek" and req.value:
            await dlna_controller.seek(av_url, req.value)
        elif action in ("speed", "rate") and req.value:
            await dlna_controller.play(av_url, speed=str(req.value))
            ws_manager.update_state({"speed": float(req.value)})
        elif action == "quality":
            target_q_url = req.url or (req.value if req.value and req.value.startswith("http") else None)
            if target_q_url:
                try:
                    await dlna_controller.set_av_transport_uri(av_url, target_q_url, ws_manager.current_state.get("title", "Stream"))
                    await dlna_controller.play(av_url)
                except Exception:
                    pass

    # Forward to Web Receiver & Controller WebSockets
    payload = {
        "value": req.value,
        "lang": req.lang,
        "url": req.url,
        "is_absolute": req.is_absolute
    }
    await ws_manager.send_to_receivers(action, payload)
    await ws_manager.broadcast_to_controllers("playback_action", {"action": action, **payload})

    if action in ("speed", "rate") and req.value:
        try:
            ws_manager.update_state({"speed": float(req.value)})
        except Exception:
            pass

    return {"status": "ok", "action": action, "value": req.value}

@app.post("/api/playback/volume")
async def adjust_volume(req: VolumeRequest):
    device_id = req.device_id or device_manager.selected_device_id
    dev = device_manager.get_device(device_id) if device_id != "web_receiver" else None
    current_vol = ws_manager.current_state.get("volume", 20)

    new_vol = current_vol
    if req.volume is not None:
        new_vol = max(0, min(100, req.volume))
    elif req.delta is not None:
        new_vol = max(0, min(100, current_vol + req.delta))

    if dev and dev.get("is_google_tv"):
        if req.mute is not None:
            await asyncio.to_thread(google_cast_controller.set_mute, dev["ip"], req.mute)
            ws_manager.update_state({"muted": req.mute})
        else:
            await asyncio.to_thread(google_cast_controller.set_volume, dev["ip"], new_vol)
            ws_manager.update_state({"volume": new_vol, "muted": False})

    elif dev and dev.get("rendering_control_url"):
        rc_url = dev["rendering_control_url"]
        if req.mute is not None:
            await dlna_controller.set_mute(rc_url, req.mute)
            ws_manager.update_state({"muted": req.mute})
        else:
            await dlna_controller.set_volume(rc_url, new_vol)
            ws_manager.update_state({"volume": new_vol, "muted": False})

    # Forward to Web Receiver
    await ws_manager.send_to_receivers("volume", {"volume": new_vol, "mute": req.mute})
    await ws_manager.broadcast_to_controllers("volume_update", {"volume": new_vol, "muted": ws_manager.current_state.get("muted", False)})

    return {"status": "ok", "volume": new_vol, "muted": ws_manager.current_state.get("muted", False)}

@app.post("/api/remote/key")
async def send_remote_key(req: RemoteKeyRequest):
    device_id = req.device_id or device_manager.selected_device_id
    dev = device_manager.get_device(device_id) if device_id != "web_receiver" else None
    key = req.key.lower()

    # Handle volume keys directly
    if key in ["vol_up", "volume_up"]:
        return await adjust_volume(VolumeRequest(delta=3))
    elif key in ["vol_down", "volume_down"]:
        return await adjust_volume(VolumeRequest(delta=-3))
    elif key in ["mute"]:
        current_mute = ws_manager.current_state.get("muted", False)
        return await adjust_volume(VolumeRequest(mute=not current_mute))

    # Handle playback keys directly
    if key in ["play", "pause", "stop"]:
        return await playback_action(PlaybackActionRequest(action=key))

    # For Google TV, handle back / home / exit by closing active cast receiver
    if dev and dev.get("is_google_tv"):
        if key in ["back", "exit", "home"]:
            await asyncio.to_thread(google_cast_controller.quit_app, dev["ip"])
            ws_manager.update_state({"state": "IDLE"})

    # Send key via Hisense MQTT Remote
    if dev and dev.get("is_hisense"):
        remote = get_hisense_remote(dev["ip"])
        await remote.send_key(key)

    # Also dispatch to web receiver navigation
    await ws_manager.send_to_receivers("key", {"key": key})
    return {"status": "ok", "key": key}

@app.post("/api/tv/wake")
async def wake_tv():
    """Send Wake-on-LAN magic packets to power on TV."""
    send_wake_on_lan(["d4:ab:cd:50:e5:d3", "18:30:0c:9e:7e:fc"])
    dev = device_manager.get_device(device_manager.selected_device_id)
    if dev and dev.get("is_hisense"):
        remote = get_hisense_remote(dev["ip"])
        asyncio.create_task(remote.connect())
    return {"status": "ok", "message": "Wake-on-LAN packets broadcasted"}

# --- IPTV Endpoints ---

@app.get("/api/iptv/channels")
async def get_channels(
    language: Optional[str] = None,
    genre: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "popularity"
):
    # Support both category and genre/language for backwards compatibility
    lang = language or (category if category in ["Georgian", "Russian", "English"] else None)
    gnr = genre or (category if category not in ["Georgian", "Russian", "English", "All"] else None)
    channels = iptv_manager.get_channels(lang, gnr, search, sort_by or "popularity")
    return {"channels": channels, "total": len(channels)}

@app.get("/api/iptv/genres")
async def get_genres():
    return {"genres": iptv_manager.genres}

@app.get("/api/iptv/languages")
async def get_languages():
    return {"languages": iptv_manager.languages}

@app.get("/api/iptv/categories")
async def get_categories():
    return {"categories": ["All", "Georgian", "Russian", "English"] + [g for g in iptv_manager.genres if g != "All"]}

@app.get("/api/stream/health")
async def get_stream_health(
    channel_id: Optional[str] = None,
    url: Optional[str] = None
):
    """
    Probes manifest health (TTFB, HTTP status, reachability).
    Caches results for 60s to prevent spamming upstream servers.
    Remembers last known good source for automatic failover.
    """
    target_url = url
    if not target_url and channel_id:
        ch = iptv_manager.get_channel_by_id(channel_id)
        if ch:
            target_url = _last_good_sources.get(channel_id) or ch.get("url")
    if not target_url:
        raise HTTPException(status_code=400, detail="Must provide url or channel_id")

    res = await probe_stream_health(target_url)
    res["channel_id"] = channel_id

    if res.get("ok") and channel_id:
        _last_good_sources[channel_id] = target_url
        _save_stream_health()

    return res

@app.get("/api/state/current")
async def get_current_state():
    """Returns current playback state including channel_id, url, title, sources, and version with zero side-effects."""
    return ws_manager.current_state

@app.get("/api/debug/receivers")
async def get_debug_receivers():
    """Returns active WebSocket receiver count, cast_version and client metadata."""
    return {
        "count": len(ws_manager.receivers),
        "cast_version": ws_manager.cast_version,
        "receivers": ws_manager.get_receivers_debug_info()
    }

@app.post("/api/iptv/cast/{channel_id}")
async def cast_channel(
    channel_id: str,
    request: Request,
    device_id: Optional[str] = None,
    client_ip: str = Depends(verify_local_network)
):
    channel = iptv_manager.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    ws_manager.update_state({"channel_id": channel_id})
    sources = channel.get("sources", [])
    active_url = channel["url"]
    active_idx = 0
    last_good = _last_good_sources.get(channel_id)
    if last_good and sources:
        for idx, s in enumerate(sources):
            if s.get("url") == last_good:
                active_url = last_good
                active_idx = idx
                break

    return await cast_media(
        CastRequest(
            url=active_url,
            title=channel["name"],
            use_proxy=True,
            channel_id=channel_id,
            logo=channel.get("logo", ""),
            sources=sources,
            source_index=active_idx,
            device_id=device_id
        ),
        request=request,
        client_ip=client_ip
    )

@app.post("/api/iptv/add")
async def add_channel(req: AddChannelRequest):
    ch = iptv_manager.add_channel(req.name, req.url, req.group, req.logo)
    return {"status": "ok", "channel": ch}

@app.post("/api/iptv/import")
async def import_playlist(req: ImportPlaylistRequest):
    if req.url:
        count = iptv_manager.import_playlist_url(req.url, req.append or False)
    elif req.content:
        count = iptv_manager.import_playlist_text(req.content, req.append or False)
    else:
        raise HTTPException(status_code=400, detail="Provide 'url' or 'content'")
    return {"status": "ok", "channels_imported": count}

@app.get("/api/logo/proxy")
async def logo_proxy_endpoint(url: str):
    """
    Rock-solid logo proxy:
    - Bypasses hotlink protection, bot filters, and CORS
    - Serves from local static/logos if file exists
    - Caches responses with 30-day Cache-Control
    """
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")

    # If it is a relative static url, serve directly
    if url.startswith("/static/"):
        rel_path = url.lstrip("/")
        local_f = BASE_DIR / rel_path
        if local_f.exists():
            return FileResponse(local_f, media_type="image/png", headers={"Cache-Control": "public, max-age=2592000, immutable"})

    # Check local static/logos by channel_id or url hash
    import hashlib
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    cached_path = BASE_DIR / "static" / "logos" / f"{url_hash}.png"
    if cached_path.exists() and cached_path.stat().st_size > 200:
        return FileResponse(cached_path, media_type="image/png", headers={"Cache-Control": "public, max-age=2592000, immutable"})

    # Fetch with browser User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    client = segment_engine.get_client()
    try:
        req = client.build_request("GET", url, headers=headers)
        resp = await client.send(req)
        if resp.status_code == 200 and len(resp.content) > 100:
            content_type = resp.headers.get("content-type", "image/png")
            try:
                cached_path.write_bytes(resp.content)
            except Exception:
                pass
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=2592000, immutable",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        logger.debug(f"Logo proxy fetch error: {e}")

    raise HTTPException(status_code=404, detail="Logo not found")

# --- Live Sports Streaming Aggregator (FBStream Integration) ---

@app.get("/api/sports/categories")
async def get_sports_categories():
    """Returns the list of sports categories with icons."""
    return {"categories": CATEGORIES}

@app.get("/api/sports/events")
async def get_sports_events(
    category: Optional[str] = "all",
    filter: Optional[str] = "all",
    q: Optional[str] = None
):
    """
    Returns live and scheduled sports events converted to Tbilisi Local Time (Asia/Tbilisi, UTC+4).
    Supports category filtering and live/upcoming status filtering.
    """
    all_events = await sports_scraper.get_all_events()

    # Filter by category
    if category and category != "all":
        all_events = [e for e in all_events if e.get("cat_slug") == category]

    # Filter by status: all, live, upcoming
    if filter == "live":
        all_events = [e for e in all_events if e.get("is_live")]
    elif filter == "upcoming":
        all_events = [e for e in all_events if not e.get("is_live")]

    # Search filter
    if q:
        query_lower = q.lower().strip()
        all_events = [
            e for e in all_events
            if query_lower in e.get("title", "").lower()
            or query_lower in e.get("category", "").lower()
            or query_lower in e.get("icon", "").lower()
        ]

    return {
        "status": "ok",
        "category": category,
        "filter": filter,
        "total": len(all_events),
        "live_count": sum(1 for e in all_events if e.get("is_live")),
        "events": all_events
    }

@app.get("/api/sports/match/{slug}")
async def get_sports_match(slug: str):
    """Returns available stream options for a specific match, plus matched TV channels."""
    res = await sports_scraper.get_match_stream_options(slug)

    # Find matched native TV sports channels for instant 1-tap TV casting
    matched_channels = []
    slug_tokens = set(re.split(r'[-_\s]+', slug.lower()))
    for ch in iptv_manager.get_channels():
        ch_name_lower = ch.get("name", "").lower()
        ch_group = ch.get("group", "").lower()
        if "sport" in ch_group or "sport" in ch_name_lower or "rugby" in ch_name_lower or "silk" in ch_name_lower:
            matched_channels.append({
                "id": ch.get("id"),
                "name": ch.get("name"),
                "group": ch.get("group"),
                "logo": ch.get("logo"),
                "url": ch.get("url")
            })

    res["matched_tv_channels"] = matched_channels[:6]
    return res

@app.get("/api/sports/player/{stream_slug}", response_class=HTMLResponse)
async def get_sports_player(stream_slug: str):
    """Returns an ad-free, sanitized HTML5 player for the stream slug."""
    html = await sports_scraper.get_sanitized_player_html(stream_slug)
    return HTMLResponse(content=html)

# --- Media Upload & Streaming ---

@app.get("/api/media/files")
async def list_media_files():
    files = []
    for f in MEDIA_DIR.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "url": f"http://{SERVER_IP}:{PORT}/api/media/stream/{f.name}"
            })
    return {"files": files}

@app.post("/api/media/upload")
async def upload_media(file: UploadFile = File(...), client_ip: str = Depends(verify_local_network)):
    target_path = MEDIA_DIR / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "status": "ok",
        "filename": file.filename,
        "url": f"http://{SERVER_IP}:{PORT}/api/media/stream/{file.filename}"
    }

@app.get("/api/media/stream/{filename}")
async def stream_media_file(filename: str, request: Request):
    file_path = MEDIA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file with range support for seeking on TV
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4"
    )

@app.post("/api/media/cast/{filename}")
async def cast_local_file(filename: str, request: Request, client_ip: str = Depends(verify_local_network)):
    file_path = MEDIA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    stream_url = f"http://{SERVER_IP}:{PORT}/api/media/stream/{filename}"
    return await cast_media(
        CastRequest(
            url=stream_url,
            title=filename,
            use_proxy=False
        ),
        request=request,
        client_ip=client_ip
    )

# --- Stream Proxy (Same-origin relative & alias support) ---

@app.get("/proxy")
@app.get("/api/stream/proxy")
async def proxy_endpoint(url: str, request: Request):
    host_header = request.headers.get("host") or f"{SERVER_IP}:{PORT}"
    return await proxy_stream(url, request, host_header)

# --- WebSockets ---

@app.websocket("/ws/controller")
async def websocket_controller(websocket: WebSocket):
    await ws_manager.connect_controller(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming commands from smartphone controller
            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect_controller(websocket)
    except Exception as e:
        logger.debug(f"Controller WebSocket error: {e}")
        ws_manager.disconnect_controller(websocket)

@app.websocket("/ws/receiver")
async def websocket_receiver(websocket: WebSocket):
    await ws_manager.connect_receiver(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Receiver report status (e.g. video time, ended, error)
            action = data.get("action")
            if action == "timeupdate":
                ws_manager.update_state({
                    "position": data.get("position", "00:00:00"),
                    "duration": data.get("duration", "00:00:00")
                })
            elif action == "state":
                ws_manager.update_state({"state": data.get("state", "PLAYING")})
                await ws_manager.broadcast_to_controllers("playback_update", ws_manager.current_state)
    except WebSocketDisconnect:
        ws_manager.disconnect_receiver(websocket)
    except Exception as e:
        logger.debug(f"Receiver WebSocket error: {e}")
        ws_manager.disconnect_receiver(websocket)

# --- Web Pages & Endpoints ---

@app.get("/endpoint.json")
@app.get("/api/endpoint")
async def get_endpoint_info():
    endpoint_file = BASE_DIR / "endpoint.json"
    if endpoint_file.exists():
        try:
            return json.loads(endpoint_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "hub_url": tunnel_manager.public_url or f"http://{SERVER_IP}:{PORT}",
        "local_url": f"http://{SERVER_IP}:{PORT}",
        "local_ip": SERVER_IP,
        "port": PORT,
        "github_pages_url": "https://anania39.github.io/Home-TV/",
        "status": "online"
    }

@app.get("/", response_class=HTMLResponse)
async def serve_smartphone_controller(request: Request):
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        index_file = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.get("/tv", response_class=HTMLResponse)
async def serve_tv_receiver(request: Request):
    tv_file = BASE_DIR / "tv.html"
    if not tv_file.exists():
        tv_file = STATIC_DIR / "tv.html"
    return HTMLResponse(content=tv_file.read_text(encoding="utf-8"))

# Mount static assets and playlists
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
playlists_dir = BASE_DIR / "playlists"
if playlists_dir.exists():
    app.mount("/playlists", StaticFiles(directory=str(playlists_dir)), name="playlists")
