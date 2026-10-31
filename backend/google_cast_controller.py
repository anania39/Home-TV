import time
import logging
from typing import Dict, Any, Optional
import pychromecast

logger = logging.getLogger("google_cast")

class GoogleCastController:
    def __init__(self):
        self._casts: Dict[str, pychromecast.Chromecast] = {}

    def get_cast(self, ip: str, name: str = "Google TV", force_refresh: bool = False) -> Optional[pychromecast.Chromecast]:
        """Retrieve an active Chromecast connection or establish a new one."""
        try:
            if not force_refresh and ip in self._casts:
                cast = self._casts[ip]
                if cast.socket_client and cast.socket_client.is_connected and not getattr(cast.socket_client, "connecting", False) and not getattr(cast.socket_client, "_force_recon", False):
                    return cast
                else:
                    logger.info(f"Existing Cast connection for {ip} was disconnected/stale. Reconnecting...")
                    try:
                        cast.disconnect(blocking=False)
                    except Exception:
                        pass
                    self._casts.pop(ip, None)

            logger.info(f"Connecting to Google TV / Chromecast at {ip}:8009...")
            cast = pychromecast.get_chromecast_from_host((ip, 8009, None, None, name))
            cast.start()
            cast.wait(timeout=4.0)
            self._casts[ip] = cast
            return cast
        except Exception as e:
            logger.warning(f"Failed to connect to Google TV at {ip}: {e}")
            return None

    def cast_media(self, ip: str, url: str, title: str = "Live Stream", mime_type: str = "video/mp4", subtitles: Optional[str] = None, stream_type: Optional[str] = None, media_info: Optional[Dict[str, Any]] = None) -> bool:
        """Cast media stream to Android TV / Google TV with dead-session recovery and app preemption."""
        try:
            cast = self.get_cast(ip)
            if not cast:
                return False

            # Verify connection health; if reconnecting or broken, refresh connection
            if not cast.socket_client or not cast.socket_client.is_connected or getattr(cast.socket_client, "_force_recon", False):
                logger.info(f"Refreshing socket connection to {ip}...")
                cast = self.get_cast(ip, force_refresh=True)
                if not cast:
                    return False

            # Refresh receiver status
            try:
                cast.socket_client.receiver_controller.update_status()
                time.sleep(0.1)
            except Exception:
                pass

            cur_app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
            has_dest = bool(cast.socket_client and cast.socket_client.destination_id)
            has_media_ns = bool(cast.socket_client and ("urn:x-cast:com.google.cast.media" in cast.socket_client.app_namespaces))

            # If TV is on screensaver/backdrop (app=None), running 3rd-party app (e.g. YouTube 233637DE), or media ns missing:
            # Launch Default Media Receiver CC1AD845 and wait until destination_id and media namespace are fully connected
            if cur_app != "CC1AD845" or not has_dest or not has_media_ns:
                logger.info(f"Default Media Receiver not active on {ip} (app={cur_app}, dest={has_dest}, ns={has_media_ns}). Launching CC1AD845...")
                try:
                    cast.socket_client.receiver_controller.launch_app("CC1AD845")
                    for _ in range(28):
                        time.sleep(0.15)
                        c_app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                        c_dest = bool(cast.socket_client and cast.socket_client.destination_id)
                        c_ns = bool(cast.socket_client and ("urn:x-cast:com.google.cast.media" in cast.socket_client.app_namespaces))
                        if c_app == "CC1AD845" and c_dest and c_ns:
                            logger.info(f"CC1AD845 media namespace ready on {ip} (dest={cast.socket_client.destination_id})")
                            break
                except Exception as ex:
                    logger.debug(f"launch_app CC1AD845 notice: {ex}")

            mc = cast.media_controller
            mc.supporting_app_id = "CC1AD845"

            # Fast status probe
            try:
                mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                time.sleep(0.08)
            except Exception:
                pass

            is_m3u8 = ".m3u8" in url or "mpegurl" in mime_type.lower()
            content_type = "application/x-mpegurl" if is_m3u8 else (mime_type or "video/mp4")
            
            # VOD / YouTube / Movies MUST be BUFFERED so speedup, pause and seeking work properly
            if stream_type:
                final_stream_type = stream_type
            else:
                final_stream_type = "LIVE" if ("iptv" in url.lower() or "live" in url.lower()) and not ("vod" in url.lower() or "movie" in url.lower() or "youtube" in url.lower() or "googlevideo" in url.lower()) else "BUFFERED"

            clean_title = title if title and not (title.startswith("http") or "proxy?url=" in title or "%2F" in title or "googlevideo.com" in title) else "Video Stream"

            # Enforce max 8 tracks to prevent exceeding Google Cast 64KB TLS packet buffer
            if media_info and "tracks" in media_info and len(media_info["tracks"]) > 8:
                media_info = dict(media_info)
                media_info["tracks"] = media_info["tracks"][:8]

            logger.info(f"Casting to {cast.name} ({ip}): {clean_title} [{content_type}] (stream_type={final_stream_type}, subtitles={bool(subtitles)})")
            mc.play_media(
                url=url,
                content_type=content_type,
                title=clean_title,
                autoplay=True,
                stream_type=final_stream_type,
                subtitles=subtitles,
                media_info=media_info
            )

            # Probe status non-blocking so player state transitions smoothly through BUFFERING to PLAYING
            time.sleep(0.3)
            try:
                mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
            except Exception:
                pass

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
                mc = cast.media_controller
                sess_id = mc.status.media_session_id if mc.status else None
                if not sess_id:
                    mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                    time.sleep(0.1)
                    sess_id = mc.status.media_session_id if mc.status else None
                if sess_id:
                    mc.send_message_nocheck({"type": "STOP", "mediaSessionId": sess_id}, inc_session_id=True)
                else:
                    mc.stop()
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

    def seek(self, ip: str, seconds: float = 0.0, is_absolute: bool = False, delta: Optional[float] = None) -> bool:
        """Non-blocking, instant rewind/forward and absolute seek on Google Cast."""
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                mc = cast.media_controller
                mc.supporting_app_id = None
                if not mc.status or not mc.status.media_session_id:
                    mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                    for _ in range(6):
                        if mc.status and mc.status.media_session_id:
                            break
                        time.sleep(0.05)

                # Calculate target position
                if delta is not None:
                    curr = float(mc.status.current_time or 0.0) if mc.status else 0.0
                    target_time = max(0.0, curr + float(delta))
                elif is_absolute:
                    target_time = max(0.0, float(seconds))
                else:
                    curr = float(mc.status.current_time or 0.0) if mc.status else 0.0
                    target_time = max(0.0, curr + float(seconds))

                sess_id = mc.status.media_session_id if mc.status else None
                if not sess_id:
                    try:
                        mc.seek(target_time)
                        logger.info(f"Dispatched fallback mc.seek to {target_time:.1f}s on {cast.name} ({ip})")
                        return True
                    except Exception as e2:
                        logger.warning(f"No active media session and fallback seek failed on {ip}: {e2}")
                        return False

                # Non-blocking direct dispatch to active session
                cmd = {
                    "type": "SEEK",
                    "currentTime": target_time,
                    "resumeState": "PLAYBACK_START",
                    "mediaSessionId": sess_id
                }
                mc.send_message_nocheck(cmd, inc_session_id=True)
                logger.info(f"Dispatched non-blocking SEEK to {target_time:.1f}s on {cast.name} ({ip}) [sess={sess_id}]")
                return True
        except Exception as e:
            logger.warning(f"Google Cast seek failed on {ip}: {e}")
            return False
        return False

    def enable_subtitles(self, ip: str, track_id: int = 1) -> bool:
        """Enable specific subtitle track via non-blocking EDIT_TRACKS_INFO."""
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                mc = cast.media_controller
                mc.supporting_app_id = None
                sess_id = mc.status.media_session_id if mc.status else None
                if not sess_id:
                    mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                    time.sleep(0.1)
                    sess_id = mc.status.media_session_id if mc.status else None
                if sess_id:
                    cmd = {
                        "type": "EDIT_TRACKS_INFO",
                        "activeTrackIds": [int(track_id)],
                        "textTrackStyle": {
                            "backgroundColor": "#00000080",
                            "foregroundColor": "#FFFFFFFF",
                            "edgeType": "OUTLINE",
                            "edgeColor": "#000000FF",
                            "fontScale": 1.1
                        },
                        "mediaSessionId": sess_id
                    }
                    mc.send_message_nocheck(cmd, inc_session_id=True)
                    logger.info(f"Enabled subtitle track {track_id} on {cast.name} ({ip}) [sess={sess_id}]")
                    return True
        except Exception as e:
            logger.debug(f"Google Cast enable_subtitles failed on {ip}: {e}")
        return False

    def disable_subtitles(self, ip: str) -> bool:
        """Turn off all subtitles via non-blocking EDIT_TRACKS_INFO (activeTrackIds=[])."""
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                mc = cast.media_controller
                mc.supporting_app_id = None
                sess_id = mc.status.media_session_id if mc.status else None
                if not sess_id:
                    mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                    time.sleep(0.1)
                    sess_id = mc.status.media_session_id if mc.status else None
                if sess_id:
                    cmd = {
                        "type": "EDIT_TRACKS_INFO",
                        "activeTrackIds": [],
                        "mediaSessionId": sess_id
                    }
                    mc.send_message_nocheck(cmd, inc_session_id=True)
                    logger.info(f"Disabled subtitles (activeTrackIds=[]) on {cast.name} ({ip}) [sess={sess_id}]")
                    return True
        except Exception as e:
            logger.debug(f"Google Cast disable_subtitles failed on {ip}: {e}")
        return False

    def set_playback_rate(self, ip: str, rate: float) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast and cast.media_controller:
                mc = cast.media_controller
                mc.supporting_app_id = None

                # Safely refresh status without ever triggering self.launch()
                if not mc.status or not mc.status.media_session_id:
                    mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                    for _ in range(6):
                        if mc.status and mc.status.media_session_id:
                            break
                        time.sleep(0.08)

                sess_id = mc.status.media_session_id if mc.status else None
                if sess_id:
                    # Non-blocking direct dispatch to active session
                    # This guarantees the video is NEVER stopped or killed
                    cmd = {
                        "type": "SET_PLAYBACK_RATE",
                        "playbackRate": float(rate),
                        "mediaSessionId": sess_id
                    }
                    mc.send_message_nocheck(cmd, inc_session_id=True)
                    logger.info(f"Dispatched SET_PLAYBACK_RATE {rate}x to session {sess_id} on {cast.name} ({ip})")
                    return True
                else:
                    logger.info(f"No active media session on {cast.name} ({ip}) to set playback rate")
                    return True
        except Exception as e:
            logger.warning(f"Google Cast set_playback_rate notice on {ip}: {e}")
            return False
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
            if not cast or not cast.status or not cast.socket_client or not cast.socket_client.is_connected:
                return {"tv_online": False, "state": "STANDBY", "volume": 20, "muted": False, "title": "", "current_time": 0.0, "duration": 0.0}

            mc = cast.media_controller
            p_state = "IDLE"
            raw_title = ""
            current_time = 0.0
            duration = 0.0
            if mc:
                try:
                    mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                except Exception:
                    pass
                if mc.status:
                    raw_state = mc.status.player_state
                    if raw_state == "PLAYING":
                        p_state = "PLAYING"
                    elif raw_state == "PAUSED":
                        p_state = "PAUSED"
                    elif raw_state in ["BUFFERING", "LOADING"]:
                        p_state = "BUFFERING"
                    raw_title = mc.status.title or ""
                    current_time = float(mc.status.current_time or 0.0)
                    duration = float(mc.status.duration or 0.0)

            # Sanitize: never allow raw URLs or proxy queries to leak into user status banner
            if raw_title.startswith("http://") or raw_title.startswith("https://") or "proxy?url=" in raw_title or "%2F" in raw_title or "googlevideo.com" in raw_title:
                raw_title = ""

            vol = int(round((cast.status.volume_level or 0.2) * 100))
            muted = getattr(cast.status, "volume_muted", False)

            if p_state == "PLAYING":
                status_text = f"Playing: {raw_title}" if raw_title else f"{cast.name} Playing"
            elif p_state == "PAUSED":
                status_text = f"Paused: {raw_title}" if raw_title else f"{cast.name} Paused"
            else:
                status_text = f"{cast.name} Ready"

            return {
                "tv_online": True,
                "state": p_state,
                "status_text": status_text,
                "volume": vol,
                "muted": muted,
                "title": raw_title,
                "current_time": current_time,
                "duration": duration
            }
        except Exception as e:
            logger.debug(f"Google Cast get_status error for {ip}: {e}")
            return {"tv_online": False, "state": "STANDBY", "volume": 20, "muted": False, "title": "", "current_time": 0.0, "duration": 0.0}

google_cast_controller = GoogleCastController()
