import ssl
import json
import uuid
import socket
import logging
import asyncio
import paho.mqtt.client as mqtt
from typing import Optional, Dict

logger = logging.getLogger("hisense_remote")

# Standard Hisense VIDAA key codes
KEY_CODES = {
    "up": "KEY_UP",
    "down": "KEY_DOWN",
    "left": "KEY_LEFT",
    "right": "KEY_RIGHT",
    "ok": "KEY_OK",
    "enter": "KEY_OK",
    "back": "KEY_RETURNS",
    "returns": "KEY_RETURNS",
    "home": "KEY_HOME",
    "menu": "KEY_MENU",
    "power": "KEY_POWER",
    "volume_up": "KEY_VOLUMEUP",
    "volume_down": "KEY_VOLUMEDOWN",
    "mute": "KEY_MUTE",
    "channel_up": "KEY_CHANNELUP",
    "channel_down": "KEY_CHANNELDOWN",
    "play": "KEY_PLAY",
    "pause": "KEY_PAUSE",
    "stop": "KEY_STOP",
    "fast_forward": "KEY_FASTFORWARD",
    "rewind": "KEY_REWIND",
    "source": "KEY_SOURCE",
    "input": "KEY_SOURCE",
    "subtitles": "KEY_SUBTITLE",
    "info": "KEY_INFO",
    "exit": "KEY_EXIT"
}

def send_wake_on_lan(mac_addresses: list[str]):
    """Send Wake-on-LAN magic packet to turn TV on from standby."""
    for mac in mac_addresses:
        try:
            clean_mac = mac.replace(":", "").replace("-", "")
            mac_bytes = bytes.fromhex(clean_mac)
            magic_packet = b'\xff' * 6 + mac_bytes * 16
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, ('255.255.255.255', 9))
            sock.sendto(magic_packet, ('192.168.50.255', 9))
            sock.close()
            logger.info(f"Sent Wake-on-LAN packet to MAC {mac}")
        except Exception as e:
            logger.debug(f"Wake-on-LAN error for {mac}: {e}")

class HisenseRemote:
    def __init__(self, tv_ip: str, tv_mac: str = "18300c9e7efc", port: int = 36669):
        self.tv_ip = tv_ip
        self.tv_mac = tv_mac.replace(":", "").lower()
        self.port = port
        self.client_id = f"tvhub_{uuid.uuid4().hex[:8]}"
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self._lock = asyncio.Lock()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to Hisense VIDAA TV MQTT at {self.tv_ip}:{self.port}")
        else:
            self.connected = False
            logger.debug(f"Failed to connect to Hisense TV MQTT, rc={rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.connected = False

    async def connect(self) -> bool:
        """Connect to Hisense TV MQTT broker with SSL."""
        async with self._lock:
            if self.connected and self.client:
                return True

            try:
                try:
                    self.client = mqtt.Client(
                        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                        client_id=self.client_id
                    )
                except AttributeError:
                    self.client = mqtt.Client(client_id=self.client_id)

                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect

                # Hisense uses self-signed SSL on port 36669
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                self.client.tls_set_context(ssl_ctx)

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: self.client.connect(self.tv_ip, self.port, keepalive=60))
                self.client.loop_start()

                # Wait briefly for connection
                for _ in range(10):
                    if self.connected:
                        break
                    await asyncio.sleep(0.1)

                return self.connected
            except Exception as e:
                logger.debug(f"Hisense MQTT connection to {self.tv_ip} unavailable: {e}")
                self.connected = False
                return False

    async def send_key(self, key_name: str) -> bool:
        """Send a navigation or action key to Hisense TV."""
        normalized_key = KEY_CODES.get(key_name.lower(), key_name.upper())

        # If user presses power, always broadcast Wake-on-LAN as well
        if normalized_key == "KEY_POWER":
            send_wake_on_lan(["d4:ab:cd:50:e5:d3", "18:30:0c:9e:7e:fc"])

        if not self.connected:
            await self.connect()

        if not self.connected or not self.client:
            return False

        payload = json.dumps({"action": "key", "key": normalized_key})
        topics = [
            f"hisense/ui_service/{self.tv_mac}/action",
            f"/remoteapp/mobile/{self.client_id}/ui_service/action",
            "hisense/remote/key"
        ]

        success = False
        for topic in topics:
            try:
                info = self.client.publish(topic, payload, qos=0)
                info.wait_for_publish(timeout=0.3)
                success = True
            except Exception:
                pass

        return success

    def disconnect(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            self.connected = False

_remote_cache: Dict[str, HisenseRemote] = {}

def get_hisense_remote(tv_ip: str, tv_mac: str = "18300c9e7efc") -> HisenseRemote:
    if tv_ip not in _remote_cache:
        _remote_cache[tv_ip] = HisenseRemote(tv_ip, tv_mac)
    return _remote_cache[tv_ip]
