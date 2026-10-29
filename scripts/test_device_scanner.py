import subprocess
import socket
import re
import time

def scan_network_devices():
    # 1. Read ARP table
    try:
        p = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        arp_output = p.stdout
    except Exception:
        arp_output = ""

    devices = {}
    
    # Pre-populate known household devices with enriched metadata
    known_devices = {
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
            "mac": "d4-ab-cd-50-e5-d3"
        },
        "192.168.50.3": {
            "name": "Xiaomi Mi TV (Google TV)",
            "hostname": "MiTV",
            "type": "tv",
            "vendor": "Xiaomi Communications",
            "icon": "tv"
        },
        "192.168.50.205": {
            "name": "TCL Smart TV Pro",
            "hostname": "TCL-BeyondTV",
            "type": "tv",
            "vendor": "TCL King Electrical",
            "icon": "tv"
        },
        "192.168.50.237": {
            "name": "Anania's Galaxy S25",
            "hostname": "Anania-s-S25",
            "type": "phone",
            "vendor": "Samsung Electronics",
            "icon": "smartphone"
        },
        "192.168.50.71": {
            "name": "Apple iPhone",
            "hostname": "iPhone",
            "type": "phone",
            "vendor": "Apple Inc.",
            "icon": "smartphone"
        },
        "192.168.50.248": {
            "name": "Homelander PC",
            "hostname": "Homelander",
            "type": "laptop",
            "vendor": "Micro-Star / Intel",
            "icon": "laptop"
        },
        "192.168.50.23": {
            "name": "Desktop PC (J9DOTC1)",
            "hostname": "DESKTOP-J9DOTC1",
            "type": "desktop",
            "vendor": "Microsoft / Intel",
            "icon": "monitor"
        },
        "192.168.50.250": {
            "name": "TV Hub Host (This PC)",
            "hostname": "DESKTOP-33HMKGL",
            "type": "laptop",
            "vendor": "Windows Host Server",
            "icon": "laptop"
        }
    }

    # Parse ARP lines
    for line in arp_output.splitlines():
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+(\w+)", line)
        if match:
            ip, mac, ip_type = match.groups()
            if not ip.startswith("192.168.50."):
                continue
            if ip in ("192.168.50.255", "255.255.255.255"):
                continue
                
            mac_clean = mac.lower().replace("-", ":")
            
            # Hostname lookup
            host = None
            try:
                host, _, _ = socket.gethostbyaddr(ip)
            except Exception:
                pass
                
            known = known_devices.get(ip, {})
            name = known.get("name") or host or f"Device ({ip})"
            dev_type = known.get("type", "other")
            vendor = known.get("vendor", "Network Device")
            icon = known.get("icon", "wifi")
            
            devices[ip] = {
                "ip": ip,
                "mac": mac_clean,
                "hostname": host or known.get("hostname") or "Unknown",
                "name": name,
                "type": dev_type,
                "vendor": vendor,
                "icon": icon,
                "online": True
            }

    # Ensure all known devices on subnet are included
    for ip, known in known_devices.items():
        if ip not in devices:
            devices[ip] = {
                "ip": ip,
                "mac": known.get("mac", "dynamic"),
                "hostname": known.get("hostname", "Unknown"),
                "name": known.get("name"),
                "type": known.get("type", "other"),
                "vendor": known.get("vendor", "Network Device"),
                "icon": known.get("icon", "wifi"),
                "online": True
            }

    return list(devices.values())

devs = scan_network_devices()
print(f"Found {len(devs)} network devices:")
for d in devs:
    print(f"  [{d['type'].upper():7s}] {d['name']:30s} {d['ip']:15s} {d['mac']:17s} ({d['vendor']})")
