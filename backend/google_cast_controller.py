import time
import re
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
                time.sleep(0.08)
            except Exception:
                pass

            cur_app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
            has_dest = bool(cast.socket_client and cast.socket_client.destination_id)
            has_media_ns = bool(cast.socket_client and ("urn:x-cast:com.google.cast.media" in cast.socket_client.app_namespaces))

            mc = cast.media_controller
            mc.supporting_app_id = "CC1AD845"

            # Check if media controller has an active media session or if it's finished/idle
            try:
                mc.send_message_nocheck({"type": "GET_STATUS"}, inc_session_id=True)
                time.sleep(0.08)
            except Exception:
                pass

            is_idle_or_finished = (
                not mc.status
                or mc.status.player_state in ("IDLE", "UNKNOWN")
                or mc.status.idle_reason in ("FINISHED", "CANCELLED", "ERROR")
                or getattr(mc.status, "media_session_id", None) is None
            )

            is_youtube_stream = ("googlevideo.com" in url.lower() or "youtube" in url.lower() or "youtu.be" in url.lower()
                                 or (media_info and (media_info.get("source_type") == "youtube" or media_info.get("customData", {}).get("source_type") == "youtube")))

            # Check for YouTube video ID to launch official native YouTube app receiver (233637DE)
            yt_id = None
            yt_m = re.search(r"(?:youtu\.be/|v/|u/\w/|embed/|watch\?v=|&v=)([^#&?]{11})", url)
            if yt_m:
                yt_id = yt_m.group(1)
            elif media_info and media_info.get("youtube_id"):
                yt_id = media_info.get("youtube_id")
            elif media_info and media_info.get("customData", {}).get("youtube_id"):
                yt_id = media_info.get("customData", {}).get("youtube_id")

            if yt_id:
                logger.info(f"Using official native YouTube app receiver (233637DE) for video {yt_id} on {ip}...")
                # 1. Check if 233637DE is active and try Lounge command
                if cur_app == "233637DE":
                    play_params = {
                        "videoId": yt_id,
                        "currentTime": "0",
                        "currentIndex": "-1",
                        "audioOnly": "false",
                        "listId": ""
                    }
                    if self._send_lounge_command(ip, "setPlaylist", play_params):
                        logger.info(f"Instantly loaded YouTube video {yt_id} via active Lounge session on {ip}")
                        return True

                # 2. Direct TLS launch of 233637DE + Lounge bind
                yt_success = self._launch_and_play_youtube(ip, yt_id)
                if yt_success:
                    logger.info(f"Successfully launched and started YouTube {yt_id} on {ip}")
                    return True

                # 3. Retry once after 600ms
                time.sleep(0.6)
                if self._launch_and_play_youtube(ip, yt_id):
                    logger.info(f"Successfully started YouTube {yt_id} on {ip} on retry")
                    return True

                logger.warning(f"YouTube launch on {ip} did not complete; maintaining TV state without CC1AD845 disruption")
                return False

            # If Default Media Receiver is not the active app (e.g. YouTube app 2C6A6E3D, Netflix, or Home screen),
            # launch CC1AD845 and wait for the media namespace to be established.
            # If CC1AD845 is ALREADY running, NEVER force-relaunch it! Relaunching an already running
            # receiver causes a race condition where the hardware video decoder surface is detached,
            # leaving only audio playing while the screen stays on the backdrop splash.
            if cur_app != "CC1AD845" or not has_dest or not has_media_ns:
                logger.info(f"Switching TV {cast.name} ({ip}) from {cur_app} to CC1AD845...")
                try:
                    cast.socket_client.receiver_controller.launch_app("CC1AD845")
                    for _ in range(30):
                        time.sleep(0.15)
                        c_app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                        c_dest = bool(cast.socket_client and cast.socket_client.destination_id)
                        c_ns = bool(cast.socket_client and ("urn:x-cast:com.google.cast.media" in cast.socket_client.app_namespaces))
                        if c_app == "CC1AD845" and c_dest and c_ns:
                            logger.info(f"CC1AD845 media namespace ready on {ip} (dest={cast.socket_client.destination_id})")
                            break
                except Exception as ex:
                    logger.debug(f"launch_app CC1AD845 notice: {ex}")
            else:
                # Receiver is already running. NEVER call mc.stop()!
                # mc.play_media smoothly replaces media without detaching the video decoder surface.
                pass

            is_m3u8 = ".m3u8" in url or "mpegurl" in mime_type.lower()
            content_type = "application/x-mpegurl" if is_m3u8 else (mime_type or "video/mp4")
            
            # VOD / YouTube / Movies MUST be BUFFERED so speedup, pause and seeking work properly
            if stream_type:
                final_stream_type = stream_type
            else:
                final_stream_type = "LIVE" if ("iptv" in url.lower() or "live" in url.lower()) and not ("vod" in url.lower() or "movie" in url.lower() or "youtube" in url.lower() or "googlevideo" in url.lower()) else "BUFFERED"

            clean_title = title if title and not (title.startswith("http") or "proxy?url=" in title or "%2F" in title or "googlevideo.com" in title) else "Video Stream"

            media_info = dict(media_info or {})
            is_youtube = ("googlevideo.com" in url.lower() or "youtube" in url.lower() or "youtu.be" in url.lower()
                          or media_info.get("source_type") == "youtube"
                          or media_info.get("customData", {}).get("source_type") == "youtube")
            # Clean up internal source_type so CAF payload only carries valid standard media keys
            media_info.pop("source_type", None)
            # Remove any segment format overrides that trigger audio-only mode on Google TV
            media_info.pop("hlsSegmentFormat", None)
            media_info.pop("hlsVideoSegmentFormat", None)

            # Enforce max 8 tracks to prevent exceeding Google Cast 64KB TLS packet buffer
            if "tracks" in media_info and len(media_info["tracks"]) > 8:
                media_info["tracks"] = media_info["tracks"][:8]

            logger.info(f"Casting to {cast.name} ({ip}): {clean_title} [{content_type}] (stream_type={final_stream_type}, subtitles={bool(subtitles)}, hlsSegmentFormat={media_info.get('hlsSegmentFormat')})")
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

    def _launch_and_play_youtube(self, ip: str, video_id: str) -> bool:
        """Direct TLS launch of 233637DE and Lounge MDX token binding without CC1AD845 fallthrough."""
        s = None
        try:
            import ssl, socket, struct, requests, re
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(socket.socket())
            s.settimeout(6.0)
            s.connect((ip, 8009))

            def send_msg(sock, src, dst, ns, payload):
                b_src = src.encode('utf-8')
                b_dst = dst.encode('utf-8')
                b_ns = ns.encode('utf-8')
                b_pl = payload.encode('utf-8')
                def varint(n):
                    res = bytearray()
                    while (n & ~0x7F) != 0:
                        res.append((n & 0x7F) | 0x80)
                        n >>= 7
                    res.append(n)
                    return bytes(res)
                msg = bytearray()
                msg += b'\x08\x00'
                msg += b'\x12' + varint(len(b_src)) + b_src
                msg += b'\x1a' + varint(len(b_dst)) + b_dst
                msg += b'\x22' + varint(len(b_ns)) + b_ns
                msg += b'\x28\x00'
                msg += b'\x32' + varint(len(b_pl)) + b_pl
                sock.sendall(struct.pack('>I', len(msg)) + bytes(msg))

            def read_msg(sock):
                raw_len = sock.recv(4)
                if not raw_len: return None, None
                l = struct.unpack('>I', raw_len)[0]
                data = b''
                while len(data) < l:
                    chunk = sock.recv(l - len(data))
                    if not chunk: break
                    data += chunk
                idx = 0
                pl = None
                ns = None
                while idx < len(data):
                    tag = data[idx]
                    idx += 1
                    fn = tag >> 3
                    wt = tag & 0x07
                    if wt == 0:
                        while data[idx] & 0x80: idx += 1
                        idx += 1
                    elif wt == 2:
                        l_val = 0
                        shift = 0
                        while True:
                            b = data[idx]
                            idx += 1
                            l_val |= (b & 0x7F) << shift
                            shift += 7
                            if not (b & 0x80): break
                        val = data[idx:idx+l_val]
                        idx += l_val
                        if fn == 4: ns = val.decode('utf-8', 'ignore')
                        elif fn == 6: pl = val.decode('utf-8', 'ignore')
                return ns, pl

            send_msg(s, 'sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.tp.connection', '{"type":"CONNECT"}')
            send_msg(s, 'sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.receiver', '{"type":"LAUNCH","appId":"233637DE","requestId":1}')

            transport_id = None
            start = time.time()
            while time.time() - start < 8.0:
                try:
                    ns, pl = read_msg(s)
                    if pl and '233637DE' in pl:
                        d = json.loads(pl)
                        for a in d.get('status', {}).get('applications', []):
                            if a.get('appId') == '233637DE':
                                transport_id = a.get('transportId')
                                break
                    if transport_id: break
                except Exception:
                    break

            if not transport_id:
                s.close()
                return False

            send_msg(s, 'sender-0', transport_id, 'urn:x-cast:com.google.cast.tp.connection', '{"type":"CONNECT"}')
            send_msg(s, 'sender-0', transport_id, 'urn:x-cast:com.google.youtube.mdx', '{"type":"getMdxSessionStatus"}')

            screen_id = None
            start = time.time()
            while time.time() - start < 5.0:
                try:
                    ns, pl = read_msg(s)
                    if pl and 'screenId' in pl:
                        m = re.search(r'"screenId":"([^"]+)"', pl)
                        if m: screen_id = m.group(1); break
                except Exception:
                    break

            s.close()
            s = None

            if not screen_id:
                return False

            headers = {'Origin': 'https://www.youtube.com', 'Content-Type': 'application/x-www-form-urlencoded'}
            r = requests.post('https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch', data={'screen_ids': screen_id}, headers=headers, timeout=5)
            if r.status_code != 200 or not r.json().get('screens'):
                return False
            lounge_token = r.json()['screens'][0]['loungeToken']

            bind_headers = dict(headers)
            bind_headers['X-YouTube-LoungeId-Token'] = lounge_token
            bind_data = {
                'device': 'REMOTE_CONTROL',
                'id': 'tvhubbackend_cast',
                'name': 'Android',
                'mdx-version': 3,
                'pairing_type': 'cast',
                'app': 'android-phone-13.14.55'
            }
            r2 = requests.post('https://www.youtube.com/api/lounge/bc/bind', params={'RID': 0, 'VER': 8, 'CVER': 1}, data=bind_data, headers=bind_headers, timeout=5)
            m_sid = re.search(r'"c","(.*?)","', r2.text)
            m_gsid = re.search(r'"S","(.*?)"\]', r2.text)
            if not m_sid or not m_gsid:
                return False
            sid = m_sid.group(1)
            gsessionid = m_gsid.group(1)

            play_data = {
                'count': 1,
                'req0__sc': 'setPlaylist',
                'req0_videoId': video_id,
                'req0_currentTime': '0',
                'req0_currentIndex': '-1',
                'req0_audioOnly': 'false',
                'req0_listId': ''
            }
            r_play = requests.post(
                'https://www.youtube.com/api/lounge/bc/bind',
                params={'SID': sid, 'gsessionid': gsessionid, 'RID': 1, 'VER': 8, 'CVER': 1},
                data=play_data,
                headers=bind_headers,
                timeout=5
            )
            return r_play.status_code == 200
        except Exception as e:
            logger.debug(f"_launch_and_play_youtube notice on {ip}: {e}")
            return False
        finally:
            if s:
                try: s.close()
                except Exception: pass

    def _send_lounge_command(self, ip: str, sc: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Send YouTube Lounge MDX command for instant playback/speed/seek control on official YouTube TV app."""
        try:
            cast = self.get_cast(ip)
            if not cast:
                return False
            from pychromecast.controllers.youtube import YouTubeController
            yt_ctrl = None
            for h in cast.custom_controllers:
                if isinstance(h, YouTubeController):
                    yt_ctrl = h
                    break
            if not yt_ctrl:
                yt_ctrl = YouTubeController()
                cast.register_handler(yt_ctrl)

            if not getattr(yt_ctrl, "_screen_id", None):
                yt_ctrl.update_screen_id()

            screen_id = getattr(yt_ctrl, "_screen_id", None)
            if not screen_id:
                return False

            import requests
            headers = {'Origin': 'https://www.youtube.com', 'Content-Type': 'application/x-www-form-urlencoded'}
            r = requests.post('https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch', data={'screen_ids': screen_id}, headers=headers, timeout=4)
            if r.status_code != 200 or not r.json().get('screens'):
                return False
            lounge_token = r.json()['screens'][0]['loungeToken']

            bind_headers = dict(headers)
            bind_headers['X-YouTube-LoungeId-Token'] = lounge_token
            bind_data = {
                'device': 'REMOTE_CONTROL',
                'id': 'tvhubbackend_ctrl',
                'name': 'Android',
                'mdx-version': 3,
                'pairing_type': 'cast',
                'app': 'android-phone-13.14.55'
            }
            r2 = requests.post('https://www.youtube.com/api/lounge/bc/bind', params={'RID': 0, 'VER': 8, 'CVER': 1}, data=bind_data, headers=bind_headers, timeout=4)
            m_sid = re.search(r'"c","(.*?)","', r2.text)
            m_gsid = re.search(r'"S","(.*?)"\]', r2.text)
            if not m_sid or not m_gsid:
                return False
            sid = m_sid.group(1)
            gsessionid = m_gsid.group(1)

            body = {'count': 1, 'req0__sc': sc}
            if params:
                for k, v in params.items():
                    body[f'req0_{k}'] = str(v)

            r_cmd = requests.post(
                'https://www.youtube.com/api/lounge/bc/bind',
                params={'SID': sid, 'gsessionid': gsessionid, 'RID': 1, 'VER': 8, 'CVER': 1},
                data=body,
                headers=bind_headers,
                timeout=4
            )
            logger.info(f"YouTube Lounge command '{sc}' dispatched to {ip}: {r_cmd.status_code}")
            return r_cmd.status_code == 200
        except Exception as e:
            logger.warning(f"YouTube Lounge command notice on {ip}: {e}")
            return False

    def play(self, ip: str) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast:
                app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                if app == "233637DE":
                    return self._send_lounge_command(ip, "playVideo")
            if cast and cast.media_controller:
                cast.media_controller.play()
                return True
        except Exception as e:
            logger.debug(f"Google Cast play failed on {ip}: {e}")
        return False

    def pause(self, ip: str) -> bool:
        try:
            cast = self.get_cast(ip)
            if cast:
                app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                if app == "233637DE":
                    return self._send_lounge_command(ip, "pauseVideo")
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
            if cast:
                app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                if app == "233637DE":
                    target_time = max(0.0, float(seconds))
                    return self._send_lounge_command(ip, "seekTo", {"newTime": str(int(target_time))})
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
            if cast:
                app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                if app == "233637DE":
                    p = {
                        "playbackRate": str(rate),
                        "rate": str(rate),
                        "playbackSpeed": str(rate),
                        "speed": str(rate)
                    }
                    self._send_lounge_command(ip, "setPlaybackRate", p)
                    self._send_lounge_command(ip, "setPlaybackSpeed", p)
                    return True
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
