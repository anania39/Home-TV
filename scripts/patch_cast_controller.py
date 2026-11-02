import re

cast_file = r"backend/google_cast_controller.py"
with open(cast_file, "r", encoding="utf-8") as f:
    text = f.read()

# Normalize CRLF to LF for matching
crlf = "\r\n" in text
text_lf = text.replace("\r\n", "\n")

target1 = """            # If Default Media Receiver is not active, destination missing, media namespace missing,
            # previous video has finished/ended (leaving the video hardware decoder surface detached),
            # OR casting a YouTube demuxed stream:
            # We force-launch CC1AD845 so a completely fresh web receiver and hardware video decoder surface are created.
            need_fresh_launch = (cur_app != "CC1AD845" or not has_dest or not has_media_ns or is_idle_or_finished or is_youtube_stream)
            if need_fresh_launch:
                logger.info(f"Launching clean CC1AD845 instance on {ip} (app={cur_app}, dest={has_dest}, ns={has_media_ns}, idle_or_finished={is_idle_or_finished}, youtube={is_youtube_stream})...")
                try:
                    cast.socket_client.receiver_controller.launch_app("CC1AD845", force_launch=True)
                    for _ in range(28):
                        time.sleep(0.12)
                        c_app = getattr(cast, "app_id", None) or (cast.status.app_id if cast.status else None)
                        c_dest = bool(cast.socket_client and cast.socket_client.destination_id)
                        c_ns = bool(cast.socket_client and ("urn:x-cast:com.google.cast.media" in cast.socket_client.app_namespaces))
                        if c_app == "CC1AD845" and c_dest and c_ns:
                            logger.info(f"CC1AD845 media namespace ready on {ip} (dest={cast.socket_client.destination_id})")
                            break
                except Exception as ex:
                    logger.debug(f"launch_app CC1AD845 notice: {ex}")
            else:
                # If a media session was already actively playing, cleanly stop it first before loading new stream
                try:
                    mc.stop()
                    time.sleep(0.1)
                except Exception:
                    pass"""

replacement1 = """            # If Default Media Receiver is not the active app (e.g. YouTube app 2C6A6E3D, Netflix, or Home screen),
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
                # Receiver is already running. If a media stream was actively playing, stop it cleanly
                try:
                    if mc.status and mc.status.player_state in ("PLAYING", "PAUSED", "BUFFERING"):
                        mc.stop()
                        time.sleep(0.12)
                except Exception:
                    pass"""

target2 = """            if is_m3u8:
                if is_youtube:
                    # For YouTube HLS: NEVER pass hlsSegmentFormat="aac" as it triggers audio-only playback!
                    media_info.pop("hlsSegmentFormat", None)
                    media_info.setdefault("hlsVideoSegmentFormat", "mpeg2_ts")
                else:
                    media_info.setdefault("hlsSegmentFormat", "ts")
                    media_info.setdefault("hlsVideoSegmentFormat", "mpeg2_ts")"""

replacement2 = """            # Remove any segment format overrides that trigger audio-only mode on Google TV
            media_info.pop("hlsSegmentFormat", None)
            media_info.pop("hlsVideoSegmentFormat", None)"""

assert target1 in text_lf, "target1 not found in text_lf"
assert target2 in text_lf, "target2 not found in text_lf"

text_lf = text_lf.replace(target1, replacement1).replace(target2, replacement2)
if crlf:
    text_lf = text_lf.replace("\n", "\r\n")

with open(cast_file, "w", encoding="utf-8") as f:
    f.write(text_lf)

print("Successfully updated backend/google_cast_controller.py!")
