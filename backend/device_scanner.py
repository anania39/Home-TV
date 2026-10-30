import subprocess
import socket
import re
import time
import logging
from typing import Dict, List, Optional
from .config import SERVER_IP, get_subnet_prefix, get_default_gateway

logger = logging.getLogger("device_scanner")

class DeviceScanner:
    def __init__(self):
        self._cached_devices: List[Dict] = []
        self._last_scan: float = 0.0

    def _infer_device_metadata(self, ip: str, mac: str, hostname: str) -> Dict:
        h_lower = (hostname or "").lower()
        m_lower = (mac or "").lower()
        gw_ip = get_default_gateway()

        # Type detection
        dev_type = "other"
        icon = "wifi"
        vendor = "Network Client"

        if ip == gw_ip or ip.endswith(".1") or "router" in h_lower or "gateway" in h_lower:
            dev_type = "router"
            icon = "router"
            vendor = "Router Gateway"
        elif "tv" in h_lower or "hisense" in h_lower or "vidaa" in h_lower or "tcl" in h_lower or "xiaomi" in h_lower or "roku" in h_lower or "vizio" in h_lower or "bravia" in h_lower:
            dev_type = "tv"
            icon = "tv"
            vendor = "Smart TV"
        elif "iphone" in h_lower or "ipad" in h_lower or "galaxy" in h_lower or "android" in h_lower or "pixel" in h_lower or "phone" in h_lower:
            dev_type = "phone"
            icon = "smartphone"
            vendor = "Mobile Device"
        elif "desktop" in h_lower or "pc" in h_lower or "laptop" in h_lower or "thinkpad" in h_lower or "macbook" in h_lower:
            dev_type = "laptop"
            icon = "laptop"
            vendor = "Computer"

        # Vendor inference from MAC prefix
        if m_lower.startswith(("c8:7f:54", "04:42:1a", "2c:fd:a1")):
            vendor = "ASUSTeK Computer"
            if dev_type == "other": dev_type = "router"; icon = "router"
        elif m_lower.startswith(("9c:c3:94", "ac:bc:32", "f0:18:98", "38:f9:d3", "b8:78:2e")):
            vendor = "Apple Inc."
            if dev_type == "other": dev_type = "phone"; icon = "smartphone"
        elif m_lower.startswith(("a6:cd:46", "30:07:4d", "50:8f:4c", "84:25:19")):
            vendor = "Samsung Electronics"
            if dev_type == "other": dev_type = "phone"; icon = "smartphone"
        elif m_lower.startswith(("12:0a:9b", "7c:49:eb")):
            vendor = "Xiaomi Communications"
            if dev_type == "other": dev_type = "tv"; icon = "tv"
        elif m_lower.startswith(("3c:c5:dd", "f4:f5:e8")):
            vendor = "TCL Electronics"
            if dev_type == "other": dev_type = "tv"; icon = "tv"
        elif m_lower.startswith(("d4:ab:cd", "18:30:0c", "a0:68:5b")):
            vendor = "Hisense Electric"
            if dev_type == "other": dev_type = "tv"; icon = "tv"
        elif m_lower.startswith(("9c:2a:70", "58:11:22", "80:fa:5b")):
            vendor = "Intel / PC Manufacturer"
            if dev_type == "other": dev_type = "desktop"; icon = "monitor"

        if ip == SERVER_IP:
            friendly_name = f"TV Hub Host ({ip})"
            dev_type = "laptop"
            icon = "laptop"
            vendor = "Host System"
        elif ip == gw_ip:
            friendly_name = f"Router Gateway ({ip})"
        else:
            friendly_name = hostname if (hostname and hostname != "Unknown") else f"Device ({ip})"

        return {
            "name": friendly_name,
            "type": dev_type,
            "vendor": vendor,
            "icon": icon
        }

    def scan(self, client_ip: Optional[str] = None, force_refresh: bool = False) -> List[Dict]:
        now = time.time()
        if not force_refresh and self._cached_devices and (now - self._last_scan < 12.0):
            return self._enrich_devices(self._cached_devices, client_ip)

        prefix = get_subnet_prefix()
        gw_ip = get_default_gateway()
        devices_map = {}

        # 1. Read ARP table for devices on active subnet
        try:
            p = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
            arp_output = p.stdout
        except Exception as e:
            logger.debug(f"ARP read notice: {e}")
            arp_output = ""

        for line in arp_output.splitlines():
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+(\w+)", line)
            if match:
                ip, mac_raw, _ = match.groups()
                if not ip.startswith(prefix):
                    continue
                if ip.endswith(".255") or ip == "255.255.255.255":
                    continue
                mac = mac_raw.lower().replace("-", ":")

                host = None
                try:
                    host, _, _ = socket.gethostbyaddr(ip)
                except Exception:
                    pass

                # Check if this IP is a dynamically discovered TV in device_manager
                tv_name = None
                try:
                    from .discovery import device_manager
                    discovered_dev = device_manager.get_device(ip)
                    if discovered_dev:
                        tv_name = discovered_dev.get("name")
                except Exception:
                    pass

                inferred = self._infer_device_metadata(ip, mac, host or "")
                name = tv_name or inferred["name"]
                dev_type = "tv" if tv_name else inferred["type"]
                vendor = inferred["vendor"]
                icon = "tv" if tv_name else inferred["icon"]

                devices_map[ip] = {
                    "ip": ip,
                    "mac": mac,
                    "hostname": host or "Unknown",
                    "name": name,
                    "type": dev_type,
                    "vendor": vendor,
                    "icon": icon,
                    "online": True
                }

        # Ensure TV Hub host PC is present
        if SERVER_IP not in devices_map and SERVER_IP != "127.0.0.1":
            devices_map[SERVER_IP] = {
                "ip": SERVER_IP,
                "mac": "local-host",
                "hostname": socket.gethostname() or "TV-Hub-Host",
                "name": f"TV Hub Host ({SERVER_IP})",
                "type": "laptop",
                "vendor": "Host System",
                "icon": "laptop",
                "online": True
            }

        # Ensure Gateway Router is present
        if gw_ip and gw_ip not in devices_map:
            devices_map[gw_ip] = {
                "ip": gw_ip,
                "mac": "gateway",
                "hostname": "Router-Gateway",
                "name": f"Router Gateway ({gw_ip})",
                "type": "router",
                "vendor": "Network Gateway",
                "icon": "router",
                "online": True
            }

        # Sort order: Router first, then TVs, then Phones, then Computers, then others
        type_priority = {"router": 0, "tv": 1, "phone": 2, "smartphone": 2, "laptop": 3, "desktop": 3, "other": 4}
        sorted_list = sorted(devices_map.values(), key=lambda d: (type_priority.get(d["type"], 5), d["ip"]))

        self._cached_devices = sorted_list
        self._last_scan = now

        return self._enrich_devices(sorted_list, client_ip)

    def _enrich_devices(self, devices: List[Dict], client_ip: Optional[str]) -> List[Dict]:
        from backend.dns_service_manager import read_state
        state = read_state()
        global_enabled = state.get('global_enabled', True)
        device_rules = state.get('device_rules', {})
        enriched = []
        for d in devices:
            d_copy = dict(d)
            d_copy["is_current_device"] = bool(client_ip and (d["ip"] == client_ip or (client_ip in ("127.0.0.1", "localhost") and d["ip"] == SERVER_IP)))
            d_copy["adblock_enabled"] = device_rules.get(d["ip"], global_enabled)
            enriched.append(d_copy)
        return enriched

device_scanner = DeviceScanner()
