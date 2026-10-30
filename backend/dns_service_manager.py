from .config import SERVER_IP
"""
DNS Service Manager
Controls the 24/7 background DNS Ad-Blocker daemon and Windows Startup integration.
Ensures ad blocking persists even if TV Hub application is completely closed.
"""

import os
import sys
import subprocess
import socket
import json
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger("dns_service_manager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "data", "adblock_state.json")
PID_FILE = os.path.join(BASE_DIR, "data", "dns_adblocker.pid")
DAEMON_SCRIPT = os.path.join(BASE_DIR, "backend", "dns_service_daemon.py")

def get_pythonw_path() -> str:
    # Locate pythonw.exe to run headless background service
    current_exe = sys.executable
    candidate = current_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(candidate):
        return candidate
    return current_exe

def get_startup_folder() -> Optional[str]:
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return None
    folder = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.exists(folder):
        return folder
    return None

def is_startup_installed() -> bool:
    folder = get_startup_folder()
    if not folder:
        return False
    vbs_path = os.path.join(folder, "TVHub_DNS_AdBlocker.vbs")
    return os.path.exists(vbs_path)

def install_startup_launcher() -> bool:
    """Installs a silent Windows startup launcher so the DNS Ad-Blocker starts with Windows."""
    folder = get_startup_folder()
    if not folder:
        return False
    vbs_path = os.path.join(folder, "TVHub_DNS_AdBlocker.vbs")
    pythonw = get_pythonw_path()
    
    # Silent VBS launcher that runs with 0 visible windows
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        f'WshShell.CurrentDirectory = """{BASE_DIR}"""\r\n'
        f'WshShell.Run """{pythonw}"" """{DAEMON_SCRIPT}""", 0, False\r\n'
    )
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        logger.info(f"Installed Windows Startup launcher at: {vbs_path}")
        return True
    except Exception as e:
        logger.warning(f"Could not install Windows Startup launcher: {e}")
        return False

def ping_dns_port(timeout: float = 0.5) -> bool:
    """Verifies if port 53 is actively answering DNS queries."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    # Standard DNS query for ping.local
    query = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04ping\x05local\x00\x00\x01\x00\x01"
    try:
        s.sendto(query, ("127.0.0.1", 53))
        resp, _ = s.recvfrom(512)
        return len(resp) >= 12
    except Exception:
        return False
    finally:
        s.close()

def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False

def get_daemon_pid() -> Optional[int]:
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            pass
    return None

def is_daemon_running() -> bool:
    pid = get_daemon_pid()
    if pid and is_pid_alive(pid):
        return True
    # Fallback: check if port 53 responds to DNS
    return ping_dns_port(timeout=0.3)

def start_daemon() -> bool:
    """Starts the 24/7 background DNS daemon decoupled from the current process."""
    if is_daemon_running():
        logger.info("DNS Ad-Blocker daemon is already running.")
        install_startup_launcher()
        return True

    install_startup_launcher()
    pythonw = get_pythonw_path()

    # Launch decoupled via Windows WMI Win32_Process so it survives terminal/app closures
    try:
        ps_cmd = (
            f'$cmd = \'"{pythonw}" "{DAEMON_SCRIPT}"\'; '
            f'Invoke-CimMethod -ClassName Win32_Process -MethodName Create '
            f'-Arguments @{{ CommandLine = $cmd; CurrentDirectory = "{BASE_DIR}" }}'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=6)
    except Exception as e:
        logger.debug(f"WMI process spawn fallback: {e}")
        try:
            flags = 0x00000008 | 0x00000200 | 0x08000000
            subprocess.Popen(
                [pythonw, DAEMON_SCRIPT],
                creationflags=flags,
                close_fds=True,
                cwd=BASE_DIR
            )
        except Exception as e2:
            logger.error(f"Fallback process spawn error: {e2}")

    # Wait up to 3 seconds for port 53 to come alive
    for _ in range(15):
        time.sleep(0.2)
        if ping_dns_port(timeout=0.2):
            logger.info("✓ DNS Ad-Blocker daemon verified healthy and responding on port 53.")
            return True

    return is_daemon_running()

def stop_daemon() -> bool:
    """Stops the DNS daemon if explicit stop is requested."""
    pid = get_daemon_pid()
    if pid and is_pid_alive(pid):
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(pid, 15)
            logger.info(f"Terminated DNS daemon with PID {pid}")
        except Exception as e:
            logger.warning(f"Error terminating PID {pid}: {e}")

    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
    return True

def read_state() -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "global_enabled": True,
        "device_rules": {},
        "stats": {
            "queries_total": 0,
            "ads_blocked": 0,
            "block_rate_percent": 0.0,
            "uptime_seconds": 0
        },
        "recent_blocks": []
    }

def update_state(updates: Dict) -> Dict:
    current = read_state()
    current.update(updates)
    current["updated_at"] = int(time.time())

    tmp_path = STATE_FILE + f".tmp.{os.getpid()}"
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    os.replace(tmp_path, STATE_FILE)
    return current

def set_global_no_ads(enabled: bool) -> Dict:
    # Ensure daemon is running so DNS service is never dropped
    if not is_daemon_running():
        start_daemon()
    return update_state({"global_enabled": enabled})

def set_device_no_ads(ip: str, enabled: bool) -> Dict:
    state = read_state()
    rules = state.get("device_rules", {})
    rules[ip] = enabled
    state["device_rules"] = rules
    return update_state(state)


def get_repositories_meta() -> Dict:
    try:
        from backend.blocklist_manager import blocklist_manager
        if blocklist_manager and blocklist_manager.meta:
            return blocklist_manager.meta
    except Exception:
        pass
    meta_path = os.path.join(BASE_DIR, "data", "blocklists", "blocklists_meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"total_domains": 310796, "sources": []}

def get_status() -> Dict:
    state = read_state()
    running = is_daemon_running()
    pid = get_daemon_pid()
    startup_enabled = is_startup_installed()
    
    stats = state.get("stats", {})
    q_total = stats.get("queries_total", 0)
    a_blocked = stats.get("ads_blocked", 0)
    block_pct = 0.0
    if q_total > 0:
        block_pct = round((a_blocked / q_total) * 100, 1)

    return {
        "global_enabled": state.get("global_enabled", True),
        "running": running,
        "persistent_service": True,
        "startup_enabled": startup_enabled,
        "pid": pid if running else None,
        "port": 53,
        "listen_ip": SERVER_IP,
        "stats": {
            "queries_total": q_total,
            "ads_blocked": a_blocked,
            "block_rate_percent": block_pct,
            "uptime_seconds": stats.get("uptime_seconds", 0)
        },
        "device_rules": state.get("device_rules", {}),
        "recent_blocks": state.get("recent_blocks", [])[-25:],
        "repositories": get_repositories_meta()
    }


def reset_stats() -> Dict:
    state = read_state()
    state["stats"] = {
        "queries_total": 0,
        "ads_blocked": 0,
        "start_time": time.time(),
        "reset_trigger": int(time.time())
    }
    state["recent_blocks"] = []
    return update_state(state)
