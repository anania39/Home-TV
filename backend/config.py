import socket
import ipaddress
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PLAYLISTS_DIR = BASE_DIR / "playlists"
MEDIA_DIR = BASE_DIR / "media"

# Ensure directories exist
PLAYLISTS_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)

PORT = int(os.environ.get("TVHUB_PORT", os.environ.get("PORT", 8000)))
NO_DEVICES = os.environ.get("TVHUB_NO_DEVICES", "0") == "1"

def get_local_ip() -> str:
    """Detect the active local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external address to get routing IP (no packet actually sent)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

SERVER_IP = get_local_ip()

def get_default_gateway() -> str:
    """Detect the default gateway (router IP) dynamically on any network."""
    try:
        import subprocess
        import re
        out = subprocess.check_output("route print 0.0.0.0", shell=True).decode("utf-8", errors="ignore")
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                gw = parts[2]
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", gw) and not gw.startswith("127."):
                    return gw
    except Exception:
        pass
    lip = get_local_ip()
    if lip and "." in lip and lip != "127.0.0.1":
        return lip.rsplit(".", 1)[0] + ".1"
    return "192.168.1.1"

def get_subnet_prefix() -> str:
    """Get the /24 prefix for the active network interface (e.g. '192.168.1.')."""
    lip = get_local_ip()
    if lip and "." in lip and lip != "127.0.0.1":
        return lip.rsplit(".", 1)[0] + "."
    return "192.168.1."

# Stream Proxy URL Mode:
# Default (False) emits same-origin relative URLs (/api/stream/proxy?url=...).
# If True, forces absolute LAN IP URLs (http://192.168.50.250:8000/...).
FORCE_ABSOLUTE_LAN_URL = os.environ.get("FORCE_ABSOLUTE_LAN_URL", "false").lower() in ("true", "1", "yes")

def is_local_network(ip_str: str) -> bool:
    """
    Check if the client IP is on the same local Wi-Fi / private subnet.
    Allows loopback and RFC 1918 private IPv4 networks:
    10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, or local link 169.254.0.0/16.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False
