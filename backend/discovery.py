import asyncio
import socket
import select
import subprocess
import re
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import urllib.parse
import httpx
import logging
from typing import Dict, Any, List
from .config import SERVER_IP, NO_DEVICES, get_subnet_prefix

logger = logging.getLogger("discovery")

# Known network profiles keyed by subnet prefix (e.g. "192.168.50.")
# This guarantees that home TVs are immediately available when on home Wi-Fi,
# while completely separating foreign subnets (e.g. office Wi-Fi) so home TVs never appear elsewhere.
KNOWN_NETWORK_PROFILES = {
    "192.168.50.": [
        {
            "ip": "192.168.50.249",
            "name": "Hisense VIDAA TV (Living Room)",
            "dev_type": "hisense",
            "manufacturer": "Hisense",
            "model": "VIDAA 43A6101EE",
            "port": 38400,
            "av_transport_url": "http://192.168.50.249:38400/upnp/control/mingusavtr",
            "rendering_control_url": "http://192.168.50.249:38400/upnp/control/mingusrcr",
            "mqtt_port": 36669,
            "is_hisense": True,
            "is_google_tv": False
        },
        {
            "ip": "192.168.50.3",
            "name": "Xiaomi Mi TV (Google TV)",
            "dev_type": "google_tv",
            "manufacturer": "Xiaomi",
            "model": "MiTV-MZTU0",
            "port": 8009,
            "location": "http://192.168.50.3:8008/ssdp/device-desc.xml",
            "cast_port": 8009,
            "is_hisense": False,
            "is_google_tv": True
        },
        {
            "ip": "192.168.50.205",
            "name": "TCL Smart TV Pro (Google TV)",
            "dev_type": "google_tv",
            "manufacturer": "TCL",
            "model": "Smart TV Pro",
            "port": 8009,
            "location": "http://192.168.50.205:8008/ssdp/device-desc.xml",
            "cast_port": 8009,
            "is_hisense": False,
            "is_google_tv": True
        }
    ]
}

class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.selected_device_id: str | None = None
        self._scanning = False
        self._init_network_devices()

    def _save_selected_device(self):
        try:
            config_file = Path(__file__).parent / ".selected_device.json"
            config_file.write_text(json.dumps({"selected_device_id": self.selected_device_id}), encoding="utf-8")
        except Exception as e:
            logger.debug(f"Could not save selected device: {e}")

    def _load_selected_device(self) -> str | None:
        try:
            config_file = Path(__file__).parent / ".selected_device.json"
            if config_file.exists():
                data = json.loads(config_file.read_text(encoding="utf-8"))
                return data.get("selected_device_id")
        except Exception:
            pass
        return None

    def _init_network_devices(self):
        """Initialize known devices matching the active network interface."""
        if NO_DEVICES:
            self.selected_device_id = "web_receiver"
            return
        prefix = get_subnet_prefix()
        profile = KNOWN_NETWORK_PROFILES.get(prefix, [])
        for dev_info in profile:
            self.add_or_update_device(**dev_info)

        valid = self.get_devices()
        saved_id = self._load_selected_device()
        if saved_id and (saved_id == "web_receiver" or any(d["id"] == saved_id for d in valid)):
            self.selected_device_id = saved_id
        elif valid:
            hisense_id = "tv_192_168_50_249"
            if any(d["id"] == hisense_id for d in valid):
                self.selected_device_id = hisense_id
            else:
                self.selected_device_id = valid[0]["id"]
        else:
            self.selected_device_id = "web_receiver"

    def get_devices(self) -> List[Dict[str, Any]]:
        """Return unique devices discovered on the active network subnet."""
        prefix = get_subnet_prefix()
        valid_devices = [d for d in self.devices.values() if d.get("ip", "").startswith(prefix)]
        return valid_devices

    def get_device(self, device_id: str) -> Dict[str, Any] | None:
        if not device_id:
            return None
        for dev in self.get_devices():
            if dev.get("id") == device_id or dev.get("ip") == device_id:
                return dev
        return None

    def select_device(self, device_id: str) -> bool:
        if device_id == "web_receiver":
            self.selected_device_id = "web_receiver"
            self._save_selected_device()
            return True
        dev = self.get_device(device_id)
        if dev:
            self.selected_device_id = dev["id"]
            self._save_selected_device()
            return True
        return False

    def add_or_update_device(self, ip: str, name: str, dev_type: str = "dlna", **kwargs) -> Dict[str, Any]:
        """Insert or update a device keyed strictly by its physical IP."""
        clean_id = f"tv_{ip.replace('.', '_')}"
        existing = self.devices.get(ip, {})

        device = {
            "id": clean_id,
            "name": existing.get("name") or name,
            "ip": ip,
            "type": dev_type,
            "manufacturer": kwargs.get("manufacturer") or existing.get("manufacturer") or "Smart TV",
            "model": kwargs.get("model") or existing.get("model") or "TV",
            "port": kwargs.get("port") or existing.get("port") or 38400,
            "location": kwargs.get("location") or existing.get("location") or "",
            "av_transport_url": kwargs.get("av_transport_url") or existing.get("av_transport_url"),
            "rendering_control_url": kwargs.get("rendering_control_url") or existing.get("rendering_control_url"),
            "mqtt_port": kwargs.get("mqtt_port") or existing.get("mqtt_port"),
            "cast_port": kwargs.get("cast_port") or existing.get("cast_port") or 8009,
            "is_hisense": kwargs.get("is_hisense", existing.get("is_hisense", False)),
            "is_google_tv": kwargs.get("is_google_tv", existing.get("is_google_tv", False))
        }

        self.devices[ip] = device
        
        if not self.selected_device_id or self.selected_device_id == "web_receiver":
            self.selected_device_id = clean_id

        return device

    def add_manual_device(self, ip: str, port: int = 38400, name: str = "Smart TV") -> Dict[str, Any]:
        """Manually add or connect a device by IP."""
        is_hisense = port == 38400 or "hisense" in name.lower() or "vidaa" in name.lower()
        dev_type = "hisense" if is_hisense else "dlna"
        return self.add_or_update_device(
            ip=ip,
            name=name,
            dev_type=dev_type,
            port=port,
            av_transport_url=f"http://{ip}:{port}/upnp/control/mingusavtr" if is_hisense else None,
            rendering_control_url=f"http://{ip}:{port}/upnp/control/mingusrcr" if is_hisense else None,
            mqtt_port=36669 if is_hisense else None,
            is_hisense=is_hisense
        )

    async def scan(self, timeout: float = 3.0) -> List[Dict[str, Any]]:
        """
        Dynamic multi-layer network discovery:
        1. Multicast SSDP scan (discovers UPnP / DLNA Renderers on active Wi-Fi).
        2. Dynamic Unicast ARP & Subnet probe (probes Google Cast & DLNA on active subnet).
        """
        if NO_DEVICES or self._scanning:
            return self.get_devices()

        self._scanning = True
        try:
            loop = asyncio.get_running_loop()
            
            # Step 1: Multicast SSDP
            discovered = await loop.run_in_executor(None, self._sync_ssdp_scan, timeout)
            for dev in discovered:
                await self._resolve_device(dev)

            # Step 2: Unicast ARP & Subnet probe
            await self._unicast_subnet_probe()

        except Exception as e:
            logger.error(f"Error during network scan: {e}")
        finally:
            self._scanning = False

        return self.get_devices()

    async def _unicast_subnet_probe(self):
        """Probe active devices on the current local subnet directly over TCP/HTTP."""
        prefix = get_subnet_prefix()
        candidate_ips = set()

        # Include known device IPs for this subnet so standby/sleeping TVs are always probed
        profile = KNOWN_NETWORK_PROFILES.get(prefix, [])
        for dev in profile:
            candidate_ips.add(dev["ip"])

        try:
            # Query ARP table for devices on active subnet
            out = subprocess.check_output("arp -a", shell=True).decode("utf-8", errors="ignore")
            for match in re.finditer(r"(\d+\.\d+\.\d+\.\d+)", out):
                ip = match.group(1)
                if ip.startswith(prefix) and not ip.endswith(".255") and not ip.endswith(".1"):
                    candidate_ips.add(ip)
        except Exception:
            pass

        async with httpx.AsyncClient(timeout=1.2, verify=False) as client:
            for ip in candidate_ips:
                # 1. Probe Google Cast / DIAL on port 8008
                try:
                    r = await client.get(f"http://{ip}:8008/ssdp/device-desc.xml")
                    if r.status_code == 200 and "<device>" in r.text:
                        root = ET.fromstring(r.text)
                        for elem in root.iter():
                            if '}' in elem.tag: elem.tag = elem.tag.split('}', 1)[1]
                        fn = root.findtext(".//friendlyName", default="Smart TV").strip()
                        man = root.findtext(".//manufacturer", default="Google TV").strip()
                        mod = root.findtext(".//modelName", default="Android TV").strip()
                        
                        display_name = f"{man} {fn} (Google TV)" if man.lower() not in fn.lower() else f"{fn} (Google TV)"
                        self.add_or_update_device(
                            ip=ip,
                            name=display_name,
                            dev_type="google_tv",
                            manufacturer=man,
                            model=mod,
                            port=8009,
                            location=f"http://{ip}:8008/ssdp/device-desc.xml",
                            cast_port=8009,
                            is_hisense=False,
                            is_google_tv=True
                        )
                        logger.info(f"Unicast probe found Google TV: {display_name} at {ip}")
                        continue
                except Exception:
                    pass

                # 2. Probe Hisense VIDAA DLNA on port 38400
                try:
                    r = await client.get(f"http://{ip}:38400/MediaServer/rendererdevicedesc.xml")
                    if r.status_code == 200 and "<device>" in r.text:
                        root = ET.fromstring(r.text)
                        for elem in root.iter():
                            if '}' in elem.tag: elem.tag = elem.tag.split('}', 1)[1]
                        fn = root.findtext(".//friendlyName", default="Hisense VIDAA TV").strip()
                        man = root.findtext(".//manufacturer", default="Hisense").strip()
                        mod = root.findtext(".//modelName", default="VIDAA TV").strip()
                        self.add_or_update_device(
                            ip=ip,
                            name=fn,
                            dev_type="hisense",
                            manufacturer=man,
                            model=mod,
                            port=38400,
                            av_transport_url=f"http://{ip}:38400/upnp/control/mingusavtr",
                            rendering_control_url=f"http://{ip}:38400/upnp/control/mingusrcr",
                            mqtt_port=36669,
                            is_hisense=True,
                            is_google_tv=False
                        )
                        logger.info(f"Unicast probe found VIDAA TV: {fn} at {ip}")
                        continue
                except Exception:
                    pass

                # 3. Probe standard UPnP / DLNA on standard ports
                for port in (8080, 7676, 49152):
                    try:
                        r = await client.get(f"http://{ip}:{port}/description.xml")
                        if r.status_code == 200 and "<device>" in r.text:
                            root = ET.fromstring(r.text)
                            for elem in root.iter():
                                if '}' in elem.tag: elem.tag = elem.tag.split('}', 1)[1]
                            fn = root.findtext(".//friendlyName", default=f"Smart TV ({ip})").strip()
                            man = root.findtext(".//manufacturer", default="Smart TV").strip()
                            mod = root.findtext(".//modelName", default="DLNA TV").strip()
                            self.add_or_update_device(
                                ip=ip,
                                name=fn,
                                dev_type="dlna",
                                manufacturer=man,
                                model=mod,
                                port=port,
                                location=f"http://{ip}:{port}/description.xml",
                                is_hisense=False,
                                is_google_tv=False
                            )
                            logger.info(f"Unicast probe found DLNA TV: {fn} at {ip}")
                            break
                    except Exception:
                        pass

    def _sync_ssdp_scan(self, timeout: float = 3.0) -> List[Dict[str, Any]]:
        """Synchronous UDP multicast SSDP discovery with network interface binding."""
        MSEARCH = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST: 239.255.255.250:1900\r\n'
            'MAN: "ssdp:discover"\r\n'
            'MX: 2\r\n'
            'ST: ssdp:all\r\n'
            '\r\n'
        ).encode('utf-8')

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((SERVER_IP, 0))
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(SERVER_IP))
        except Exception as e:
            logger.warning(f"Failed to bind to interface {SERVER_IP}: {e}")

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(timeout)

        discovered = []
        seen_locations = set()

        try:
            sock.sendto(MSEARCH, ('239.255.255.250', 1900))
            while True:
                ready = select.select([sock], [], [], 0.8)
                if not ready[0]:
                    break
                data, addr = sock.recvfrom(4096)
                text = data.decode('utf-8', errors='ignore')
                headers = {}
                for line in text.split('\r\n')[1:]:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        headers[k.strip().upper()] = v.strip()

                loc = headers.get('LOCATION', '')
                if loc and loc not in seen_locations:
                    seen_locations.add(loc)
                    discovered.append({
                        "ip": addr[0],
                        "location": loc,
                        "server": headers.get("SERVER", ""),
                        "st": headers.get("ST", "")
                    })
        except Exception as e:
            logger.debug(f"SSDP scan receive error: {e}")
        finally:
            sock.close()

        return discovered

    async def _resolve_device(self, info: Dict[str, Any]):
        """Fetch and parse device XML to discover control endpoints and metadata."""
        location = info["location"]
        ip = info["ip"]
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                resp = await client.get(location)
                if resp.status_code != 200:
                    return

                xml_text = resp.text
                root = ET.fromstring(xml_text)
                
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]

                friendly_name = root.findtext(".//friendlyName", default="").strip()
                manufacturer = root.findtext(".//manufacturer", default="").strip()
                model_name = root.findtext(".//modelName", default="").strip()
                model_desc = root.findtext(".//modelDescription", default="").strip()
                device_type = root.findtext(".//deviceType", default="").strip()

                is_renderer = "MediaRenderer" in device_type or "renderer" in location.lower()
                is_hisense = "hisense" in friendly_name.lower() or "hisense" in manufacturer.lower() or "vidaa" in friendly_name.lower() or "36669" in model_desc
                is_google_tv = "dial" in device_type.lower() or "chromecast" in info.get("server", "").lower() or "xiaomi" in manufacturer.lower()

                av_transport_url = None
                rendering_control_url = None

                for service in root.iter("service"):
                    stype = service.findtext("serviceType", default="")
                    curl = service.findtext("controlURL", default="")
                    if curl:
                        full_curl = urllib.parse.urljoin(location, curl)
                        if "AVTransport" in stype:
                            av_transport_url = full_curl
                        elif "RenderingControl" in stype:
                            rendering_control_url = full_curl

                if is_hisense:
                    self.add_or_update_device(
                        ip=ip,
                        name=friendly_name or f"Hisense VIDAA TV ({ip})",
                        dev_type="hisense",
                        manufacturer=manufacturer or "Hisense",
                        model=model_name or "VIDAA TV",
                        port=38400,
                        location=location,
                        av_transport_url=av_transport_url or f"http://{ip}:38400/upnp/control/mingusavtr",
                        rendering_control_url=rendering_control_url or f"http://{ip}:38400/upnp/control/mingusrcr",
                        mqtt_port=36669,
                        is_hisense=True,
                        is_google_tv=False
                    )
                elif is_google_tv or "8008" in location:
                    display_name = f"{manufacturer} {friendly_name} (Google TV)" if manufacturer.lower() not in friendly_name.lower() else f"{friendly_name} (Google TV)"
                    self.add_or_update_device(
                        ip=ip,
                        name=display_name,
                        dev_type="google_tv",
                        manufacturer=manufacturer or "Google TV",
                        model=model_name or "Android TV",
                        port=8009,
                        location=location,
                        cast_port=8009,
                        is_hisense=False,
                        is_google_tv=True
                    )
                elif is_renderer or av_transport_url:
                    self.add_or_update_device(
                        ip=ip,
                        name=friendly_name or f"Smart TV ({ip})",
                        dev_type="dlna",
                        manufacturer=manufacturer or "Smart TV",
                        model=model_name or "DLNA",
                        location=location,
                        av_transport_url=av_transport_url,
                        rendering_control_url=rendering_control_url,
                        is_hisense=False,
                        is_google_tv=False
                    )

        except Exception as e:
            logger.debug(f"Failed to resolve device at {location}: {e}")

device_manager = DeviceManager()
