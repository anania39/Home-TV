import subprocess
import socket
import re
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("device_scanner")

class DeviceScanner:
    def __init__(self):
        self._cached_devices: List[Dict] = []
        self._last_scan: float = 0.0
        
        # Household device knowledge base
        self._known_devices = {
            "192.168.50.1": {
                "name": "ASUS RT-AX1800U Router",
                "hostname": "RT-AX1800U-C258",
                "type": "router",
                "vendor": "ASUSTeK Computer",
                "icon": "router"
            },
            "192.168.50.249": {
                "name": "Hisense VIDAA TV (Living Room)",
                "hostname": "Hisense-SmartTV",
                "type": "tv",
                "vendor": "Hisense Electric",
                "icon": "tv",
                "mac": "d4:ab:cd:50:e5:d3"
            },
            "192.168.50.3": {
                "name": "Xiaomi Mi TV (Google TV)",
                "hostname": "MiTV",
                "type": "tv",
                "vendor": "Xiaomi Communications",
                "icon": "tv",
                "mac": "12:0a:9b:85:78:0b"
            },
            "192.168.50.205": {
                "name": "TCL Smart TV Pro",
                "hostname": "TCL-BeyondTV",
                "type": "tv",
                "vendor": "TCL King Electrical",
                "icon": "tv",
                "mac": "3c:c5:dd:a2:c2:ee"
            },
            "192.168.50.237": {
                "name": "Anania's Galaxy S25",
                "hostname": "Anania-s-S25",
                "type": "phone",
                "vendor": "Samsung Electronics",
                "icon": "smartphone",
                "mac": "a6:cd:46:87:5c:88"
            },
            "192.168.50.71": {
                "name": "Apple iPhone",
                "hostname": "iPhone",
                "type": "phone",
                "vendor": "Apple Inc.",
                "icon": "smartphone",
                "mac": "9c:c3:94:9d:cd:66"
            },
            "192.168.50.248": {
                "name": "Homelander PC",
                "hostname": "Homelander",
                "type": "laptop",
                "vendor": "Micro-Star / Intel",
                "icon": "laptop",
                "mac": "58:11:22:af:60:32"
            },
            "192.168.50.23": {
                "name": "Desktop PC (J9DOTC1)",
                "hostname": "DESKTOP-J9DOTC1",
                "type": "desktop",
                "vendor": "Microsoft / Intel",
                "icon": "monitor",
                "mac": "9c:2a:70:54:12:7f"
            },
            "192.168.50.250": {
                "name": "TV Hub Host (This PC)",
                "hostname": "DESKTOP-33HMKGL",
                "type": "laptop",
                "vendor": "Windows Host Server",
                "icon": "laptop",
                "mac": "Local Host"
            }
        }

    def _infer_device_metadata(self, ip: str, mac: str, hostname: str) -> Dict:
        h_lower = (hostname or "").lower()
        m_lower = (mac or "").lower()

        # Type detection
        dev_type = "other"
        icon = "wifi"
        vendor = "Network Client"

        if "router" in h_lower or ip.endswith(".1"):
            dev_type = "router"
            icon = "router"
            vendor = "Router Gateway"
        elif "tv" in h_lower or "hisense" in h_lower or "vidaa" in h_lower or "tcl" in h_lower or "xiaomi" in h_lower:
            dev_type = "tv"
            icon = "tv"
            vendor = "Smart TV"
        elif "iphone" in h_lower or "ipad" in h_lower or "galaxy" in h_lower or "s25" in h_lower or "android" in h_lower or "pixel" in h_lower:
            dev_type = "phone"
            icon = "smartphone"
            vendor = "Mobile Device"
        elif "desktop" in h_lower or "pc" in h_lower or "homelander" in h_lower or "laptop" in h_lower or "thinkpad" in h_lower:
            dev_type = "laptop"
            icon = "laptop"
            vendor = "Computer"

        # Vendor inference from MAC prefix
        if m_lower.startswith(("c8:7f:54", "04:42:1a", "2c:fd:a1")):
            vendor = "ASUSTeK Computer"
            if dev_type == "other": dev_type = "router"; icon = "router"
        elif m_lower.startswith(("9c:c3:94", "ac:bc:32", "f0:18:98", "38:f9:d3")):
            vendor = "Apple Inc."
            if dev_type == "other": dev_type = "phone"; icon = "smartphone"
        elif m_lower.startswith(("a6:cd:46", "30:07:4d", "50:8f:4c")):
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
            # Return cached with current client indicator
            return self._enrich_devices(self._cached_devices, client_ip)

        devices_map = {}

        # 1. Read ARP table
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
                if not ip.startswith("192.168.50."):
                    continue
                if ip in ("192.168.50.255", "255.255.255.255"):
                    continue
                mac = mac_raw.lower().replace("-", ":")

                host = None
                try:
                    host, _, _ = socket.gethostbyaddr(ip)
                except Exception:
                    pass

                known = self._known_devices.get(ip, {})
                if known:
                    name = known["name"]
                    dev_type = known["type"]
                    vendor = known["vendor"]
                    icon = known["icon"]
                    hostname = known.get("hostname") or host or "Unknown"
                else:
                    inferred = self._infer_device_metadata(ip, mac, host or "")
                    name = inferred["name"]
                    dev_type = inferred["type"]
                    vendor = inferred["vendor"]
                    icon = inferred["icon"]
                    hostname = host or "Unknown"

                devices_map[ip] = {
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "name": name,
                    "type": dev_type,
                    "vendor": vendor,
                    "icon": icon,
                    "online": True
                }

        # 2. Merge known household devices
        for ip, known in self._known_devices.items():
            if ip not in devices_map:
                devices_map[ip] = {
                    "ip": ip,
                    "mac": known.get("mac", "dynamic"),
                    "hostname": known.get("hostname", "Unknown"),
                    "name": known.get("name"),
                    "type": known.get("type", "other"),
                    "vendor": known.get("vendor", "Network Device"),
                    "icon": known.get("icon", "wifi"),
                    "online": True
                }

        # Sort order: Router first, then TVs, then Phones, then Computers
        type_priority = {"router": 0, "tv": 1, "phone": 2, "smartphone": 2, "laptop": 3, "desktop": 3, "other": 4}
        sorted_list = sorted(devices_map.values(), key=lambda d: (type_priority.get(d["type"], 5), d["ip"]))

        self._cached_devices = sorted_list
        self._last_scan = now

        return self._enrich_devices(sorted_list, client_ip)

    def _enrich_devices(self, devices: List[Dict], client_ip: Optional[str]) -> List[Dict]:
        from backend.dns_adblocker import dns_adblocker
        enriched = []
        for d in devices:
            d_copy = dict(d)
            d_copy["is_current_device"] = (client_ip and (d["ip"] == client_ip or (client_ip in ("127.0.0.1", "localhost") and d["ip"] == "192.168.50.250")))
            d_copy["adblock_enabled"] = dns_adblocker.is_blocking_enabled_for_ip(d["ip"])
            enriched.append(d_copy)
        return enriched

device_scanner = DeviceScanner()
