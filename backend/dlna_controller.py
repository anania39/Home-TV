import httpx
import xml.etree.ElementTree as ET
import html
import logging
from typing import Dict, Any

logger = logging.getLogger("dlna")

def build_didl_metadata(title: str, uri: str, mime_type: str = "video/mp4") -> str:
    """Generate DIDL-Lite metadata XML with proper DLNA protocolInfo for HLS and MP4."""
    is_hls = ".m3u8" in uri or "mpegurl" in (mime_type or "").lower()
    if is_hls:
        protocol_info = "http-get:*:application/vnd.apple.mpegurl:DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000"
    else:
        protocol_info = f"http-get:*:{mime_type}:*"

    didl = (
        '<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">'
        f'<item id="1" parentID="0" restricted="1">'
        f'<dc:title>{html.escape(title)}</dc:title>'
        f'<upnp:class>object.item.videoItem</upnp:class>'
        f'<res protocolInfo="{protocol_info}">{html.escape(uri)}</res>'
        f'</item></DIDL-Lite>'
    )
    return html.escape(didl)

class DLNAController:
    def __init__(self, timeout: float = 2.5):
        self.timeout = timeout

    async def _send_soap(self, control_url: str, service_type: str, action: str, body_args: str) -> str:
        soap_envelope = (
            '<?xml version="1.0" encoding="utf-8"?>\r\n'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\r\n'
            '  <s:Body>\r\n'
            f'    <u:{action} xmlns:u="{service_type}">\r\n'
            f'      {body_args}\r\n'
            f'    </u:{action}>\r\n'
            '  </s:Body>\r\n'
            '</s:Envelope>'
        )

        headers = {
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction': f'"{service_type}#{action}"'
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(control_url, content=soap_envelope.encode('utf-8'), headers=headers)
                if resp.status_code >= 400:
                    logger.warning(f"SOAP {action} error {resp.status_code}: {resp.text[:200]}")
                return resp.text
        except httpx.TimeoutException:
            logger.debug(f"TV at {control_url} timed out (may be asleep/standby).")
            return ""
        except (httpx.ConnectError, httpx.NetworkError) as e:
            logger.debug(f"TV at {control_url} is unreachable (offline or standby).")
            return ""

    # --- AVTransport Actions ---

    async def set_av_transport_uri(self, control_url: str, uri: str, title: str = "Stream", mime_type: str = "video/mp4") -> bool:
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        if ".m3u8" in uri:
            mime_type = "application/vnd.apple.mpegurl"
        metadata = build_didl_metadata(title, uri, mime_type)
        body = (
            f'<InstanceID>0</InstanceID>'
            f'<CurrentURI>{html.escape(uri)}</CurrentURI>'
            f'<CurrentURIMetaData>{metadata}</CurrentURIMetaData>'
        )
        try:
            resp = await self._send_soap(control_url, service, "SetAVTransportURI", body)
            return "SetAVTransportURIResponse" in resp
        except Exception as e:
            logger.error(f"SetAVTransportURI failed: {e}")
            return False

    async def play(self, control_url: str) -> bool:
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        body = '<InstanceID>0</InstanceID><Speed>1</Speed>'
        try:
            resp = await self._send_soap(control_url, service, "Play", body)
            return "PlayResponse" in resp
        except Exception as e:
            logger.error(f"Play failed: {e}")
            return False

    async def pause(self, control_url: str) -> bool:
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        body = '<InstanceID>0</InstanceID>'
        try:
            resp = await self._send_soap(control_url, service, "Pause", body)
            return "PauseResponse" in resp
        except Exception as e:
            logger.error(f"Pause failed: {e}")
            return False

    async def stop(self, control_url: str) -> bool:
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        body = '<InstanceID>0</InstanceID>'
        try:
            resp = await self._send_soap(control_url, service, "Stop", body)
            return "StopResponse" in resp
        except Exception as e:
            logger.error(f"Stop failed: {e}")
            return False

    async def seek(self, control_url: str, target_time: str) -> bool:
        """Seek to target_time in HH:MM:SS format."""
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        body = (
            f'<InstanceID>0</InstanceID>'
            f'<Unit>REL_TIME</Unit>'
            f'<Target>{target_time}</Target>'
        )
        try:
            resp = await self._send_soap(control_url, service, "Seek", body)
            return "SeekResponse" in resp
        except Exception as e:
            logger.error(f"Seek failed: {e}")
            return False

    async def get_transport_info(self, control_url: str) -> Dict[str, Any]:
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        body = '<InstanceID>0</InstanceID>'
        try:
            resp = await self._send_soap(control_url, service, "GetTransportInfo", body)
            if not resp or not resp.strip() or "GetTransportInfoResponse" not in resp:
                return {"state": "STANDBY", "status": "OFFLINE"}
            root = ET.fromstring(resp)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            state = root.findtext(".//CurrentTransportState", default="UNKNOWN")
            status = root.findtext(".//CurrentTransportStatus", default="OK")
            return {"state": state, "status": status}
        except Exception as e:
            logger.debug(f"GetTransportInfo standby/offline: {e}")
            return {"state": "STANDBY", "status": "OFFLINE"}

    async def get_position_info(self, control_url: str) -> Dict[str, Any]:
        service = "urn:schemas-upnp-org:service:AVTransport:1"
        body = '<InstanceID>0</InstanceID>'
        try:
            resp = await self._send_soap(control_url, service, "GetPositionInfo", body)
            if not resp or not resp.strip() or "GetPositionInfoResponse" not in resp:
                return {"duration": "00:00:00", "position": "00:00:00", "uri": ""}
            root = ET.fromstring(resp)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            track_duration = root.findtext(".//TrackDuration", default="00:00:00")
            rel_time = root.findtext(".//RelTime", default="00:00:00")
            track_uri = root.findtext(".//TrackURI", default="")
            return {
                "duration": track_duration,
                "position": rel_time,
                "uri": track_uri
            }
        except Exception as e:
            logger.debug(f"GetPositionInfo offline: {e}")
            return {"duration": "00:00:00", "position": "00:00:00", "uri": ""}

    # --- RenderingControl Actions (Volume / Mute) ---

    async def get_volume(self, control_url: str) -> int:
        service = "urn:schemas-upnp-org:service:RenderingControl:1"
        body = '<InstanceID>0</InstanceID><Channel>Master</Channel>'
        try:
            resp = await self._send_soap(control_url, service, "GetVolume", body)
            if not resp or not resp.strip() or "GetVolumeResponse" not in resp:
                return -1
            root = ET.fromstring(resp)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            vol_str = root.findtext(".//CurrentVolume", default="0")
            return int(vol_str)
        except Exception as e:
            logger.debug(f"GetVolume offline: {e}")
            return -1

    async def set_volume(self, control_url: str, volume: int) -> bool:
        service = "urn:schemas-upnp-org:service:RenderingControl:1"
        volume = max(0, min(100, volume))
        body = f'<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredVolume>{volume}</DesiredVolume>'
        try:
            resp = await self._send_soap(control_url, service, "SetVolume", body)
            return "SetVolumeResponse" in resp
        except Exception as e:
            logger.error(f"SetVolume failed: {e}")
            return False

    async def set_mute(self, control_url: str, mute: bool) -> bool:
        service = "urn:schemas-upnp-org:service:RenderingControl:1"
        val = "1" if mute else "0"
        body = f'<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredMute>{val}</DesiredMute>'
        try:
            resp = await self._send_soap(control_url, service, "SetMute", body)
            return "SetMuteResponse" in resp
        except Exception as e:
            logger.error(f"SetMute failed: {e}")
            return False

dlna_controller = DLNAController()
