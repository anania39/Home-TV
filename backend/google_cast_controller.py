import time
import logging
from typing import Dict, Any, Optional
import pychromecast

logger = logging.getLogger("google_cast")

class GoogleCastController:
    def __init__(self):
        self._casts: Dict[str, pychromecast.Chromecast] = {}

    def get_cast(self, ip: str, name: str = "Google TV") -> Optional[pychromecast.Chromecast]:
        """Retrieve an active Chromecast connection or establish a new one."""
        try:
            if ip in self._casts:
                cast = self._casts[ip]
                if cast.socket_client and cast.socket_client.is_connected:
                    return cast

            logger.info(f"Connecting to Google TV / Chromecast at {ip}:8009...")
            cast = pychromecast.get_chromecast_from_host((ip, 8009, None, None, name))
            cast.start()
            cast.wait(timeout=4.0)
            self._casts[ip] = cast
            return cast
        except Exception as e:
            logger.warning(f"Failed to connect to Google TV at {ip}: {e}")
            return None

    def cast_media(self, ip: str, url: str, title: str = "Live Stream", mime_type: str = "video/mp4") -> bool:
        """Cast media stream to Android TV / Google TV."""
        try:
            cast = self.get_cast(ip)
            if not cast:
                return False

            mc = cast.media_controller
            is_m3u8 = ".m3u8" in url or "mpegurl" in mime_type.lower()
            content_type = "application/x-mpegurl" if is_m3u8 else (mime_type or "video/mp4")
            stream_type = "LIVE" if is_m3u8 else "BUFFERED"

            logger.info(f"Casting to {cast.name} ({ip}): {title} [{content_type}]")
            mc.play_media(
                url=url,
                content_type=content_type,
                title=title,
                autoplay=True,
                stream_type=stream_type
            )
            return True
        except Exception as e:
            logger.error(f"Google Cast play_media failed on {ip}: {e}")
            return False

    def play(self, ip: str) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                cast.media_controller.play()
                return True
        except Exception as e:
            logger.debug(f"Google Cast play failed on {ip}: {e}")
        return False

    def pause(self, ip: str) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                cast.media_controller.pause()
                return True
        except Exception as e:
            logger.debug(f"Google Cast pause failed on {ip}: {e}")
        return False

    def stop(self, ip: str) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                cast.media_controller.stop()
                return True
        except Exception as e:
            logger.debug(f"Google Cast stop failed on {ip}: {e}")
        return False

    def quit_app(self, ip: str) -> bool:
        """Quit the active receiver application on Google TV / Chromecast."""
        try:
            cast = self.get_cast(ip)
            if cast:
                cast.quit_app()
                return True
        except Exception as e:
            logger.debug(f"Google Cast quit_app failed on {ip}: {e}")
        return False

    def seek(self, ip: str, seconds: float) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                mc = cast.media_controller
                curr = mc.status.current_time or 0
                mc.seek(max(0, curr + seconds))
                return True
        except Exception as e:
            logger.debug(f"Google Cast seek failed on {ip}: {e}")
        return False

    def set_volume(self, ip: str, volume_percent: int) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast:
                vol = max(0.0, min(1.0, volume_percent / 100.0))
                cast.set_volume(vol)
                return True
        except Exception as e:
            logger.debug(f"Google Cast set_volume failed on {ip}: {e}")
        return False

    def set_mute(self, ip: str, mute: bool) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast:
                cast.set_volume_muted(mute)
                return True
        except Exception as e:
            logger.debug(f"Google Cast set_mute failed on {ip}: {e}")
        return False

    def get_status(self, ip: str) -> Dict[str, Any]:
        """Query real status from Google TV / Android TV."""
        try:
            cast = self.get_cast(ip)
            if not cast or not cast.status:
                return {"tv_online": False, "state": "STANDBY", "volume": 20, "muted": False, "title": ""}

            is_standby = getattr(cast.status, "is_stand_by", False)
            if is_standby:
                return {
                    "tv_online": False,
                    "state": "STANDBY",
                    "status_text": f"{cast.name} is in Standby",
                    "volume": int(round((cast.status.volume_level or 0.2) * 100)),
                    "muted": getattr(cast.status, "volume_muted", False),
                    "title": ""
                }

            mc = cast.media_controller
            p_state = "IDLE"
            title = ""
            if mc and mc.status:
                raw_state = mc.status.player_state
                if raw_state == "PLAYING":
                    p_state = "PLAYING"
                elif raw_state == "PAUSED":
                    p_state = "PAUSED"
                elif raw_state in ["BUFFERING", "LOADING"]:
                    p_state = "BUFFERING"
                title = mc.status.title or ""

            vol = int(round((cast.status.volume_level or 0.2) * 100))
            muted = getattr(cast.status, "volume_muted", False)

            return {
                "tv_online": True,
                "state": p_state,
                "status_text": f"Playing: {title}" if p_state == "PLAYING" and title else f"{cast.name} Ready",
                "volume": vol,
                "muted": muted,
                "title": title
            }
        except Exception as e:
            logger.debug(f"Google Cast get_status error for {ip}: {e}")
            return {"tv_online": False, "state": "STANDBY", "volume": 20, "muted": False, "title": ""}

google_cast_controller = GoogleCastController()
