import re

# 1. Update backend/app.py
with open("backend/app.py", "r", encoding="utf-8") as f:
    app_content = f.read()

old_app_block = """            # Step 1: Seamlessly set new URI directly (avoids Hisense VIDAA exiting DLNA app to HDMI 1)
            set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)
            if not set_ok:
                # If TV renderer requires STOP transition first, stop and retry
                try:
                    await dlna_controller.stop(av_url)
                    await asyncio.sleep(0.15)
                except Exception as e:
                    logger.debug(f"DLNA stop notice: {e}")

                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            if set_ok:
                tv_is_active = True
                await asyncio.sleep(0.08)
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                await dlna_controller.play(av_url)"""

new_app_block = """            # Clean Hardware TV Pipeline Transition:
            # Check if TV is actively playing a stream from a previous channel
            try:
                cur_info = await dlna_controller.get_transport_info(av_url)
                cur_state = cur_info.get("state", "STOPPED")
            except Exception:
                cur_state = "STOPPED"

            # If TV is currently PLAYING, TRANSITIONING or PAUSED from a previous channel,
            # cleanly stop it and wait for STOPPED state (up to 1.2s) so the TV's GStreamer demuxer
            # and hardware decoder ring buffers are 100% flushed.
            # This completely eliminates channel switching oscillation and audio/video desync.
            if cur_state in ("PLAYING", "TRANSITIONING", "PAUSED_PLAYBACK"):
                try:
                    await dlna_controller.stop(av_url)
                    for _ in range(8):
                        await asyncio.sleep(0.12)
                        if is_stale():
                            return {"status": "superseded", "version": my_version, "mode": mode}
                        chk = await dlna_controller.get_transport_info(av_url)
                        if chk.get("state") in ("STOPPED", "NO_MEDIA_PRESENT"):
                            break
                except Exception as e:
                    logger.debug(f"DLNA clean stop notice: {e}")

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)
            if not set_ok:
                try:
                    await dlna_controller.stop(av_url)
                    await asyncio.sleep(0.2)
                except Exception as e:
                    logger.debug(f"DLNA stop notice: {e}")

                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            if set_ok:
                tv_is_active = True
                await asyncio.sleep(0.12)
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                await dlna_controller.play(av_url)"""

if old_app_block in app_content:
    app_content = app_content.replace(old_app_block, new_app_block)
    with open("backend/app.py", "w", encoding="utf-8") as f:
        f.write(app_content)
    print("backend/app.py updated successfully!")
else:
    # Try normalizing newlines
    normalized_content = app_content.replace("\r\n", "\n")
    if old_app_block.replace("\r\n", "\n") in normalized_content:
        normalized_content = normalized_content.replace(old_app_block.replace("\r\n", "\n"), new_app_block.replace("\r\n", "\n"))
        with open("backend/app.py", "w", encoding="utf-8") as f:
            f.write(normalized_content)
        print("backend/app.py updated successfully (with normalized newlines)!")
    else:
        print("ERROR: old_app_block not found in backend/app.py")

# 2. Update backend/stream_proxy.py
with open("backend/stream_proxy.py", "r", encoding="utf-8") as f:
    sp_content = f.read()

old_sp_manifest_head = """    if url_clean.endswith(".m3u8") or "mpegurl" in request.headers.get("accept", "").lower():
        # 1. RFC 8216 Manifest Cache (2.0s - 2.5s TTL): Serve immediately from RAM to prevent TV spin-locking
        cached_m3u8 = segment_engine.get_manifest(url, min_ttl=2.0)
        if cached_m3u8 is not None:
            return Response(
                content=cached_m3u8,
                status_code=200,
                headers={
                    "Content-Type": "application/vnd.apple.mpegurl",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=2, stale-while-revalidate=2",
                    "Pragma": "no-cache",
                    "X-Cache": "HIT"
                }
            )

        # 2. Upstream 429/5xx Circuit Breaker: If domain is in backoff, serve cached manifest without hammering upstream
        if segment_engine.is_domain_in_backoff(domain):
            last_good = segment_engine.get_last_manifest(url)
            if last_good is not None:
                segment_engine.put_manifest(url, last_good)
                return Response(
                    content=last_good,
                    status_code=200,
                    headers={
                        "Content-Type": "application/vnd.apple.mpegurl",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Cache-Control": "public, max-age=3, stale-while-revalidate=3",
                        "Pragma": "no-cache",
                        "X-Cache": "BACKOFF-SHIELD-200"
                    }
                )"""

new_sp_manifest_head = """    is_m3u8_target = url_clean.endswith(".m3u8") or "mpegurl" in request.headers.get("accept", "").lower()
    if is_m3u8_target:
        # Debounce hyper-aggressive TV manifest polling (prevents spin loops and upstream 429)
        now_ts = time.time()
        client_key = f"{client_ip}:{url_clean}"
        last_poll = _client_manifest_poll.get(client_key, 0.0)
        time_since_last = now_ts - last_poll
        if time_since_last < 0.75:
            # TV client is polling faster than 750ms; gentle sleep throttles GStreamer/CE-HTML spin loop
            await asyncio.sleep(0.75 - time_since_last)
        _client_manifest_poll[client_key] = time.time()

        # 1. RFC 8216 Manifest Cache (2.0s - 2.5s TTL): Serve immediately from RAM
        cached_m3u8 = segment_engine.get_manifest(url, min_ttl=2.0)
        if cached_m3u8 is not None:
            return Response(
                content=cached_m3u8,
                status_code=200,
                headers={
                    "Content-Type": "application/vnd.apple.mpegurl",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=2, stale-while-revalidate=2",
                    "Accept-Ranges": "bytes",
                    "Connection": "keep-alive",
                    "X-Cache": "HIT"
                }
            )

        # 2. Upstream 429/5xx Circuit Breaker: If domain is in backoff, serve cached manifest without hammering upstream
        if segment_engine.is_domain_in_backoff(domain):
            last_good = segment_engine.get_last_manifest(url)
            if last_good is not None:
                segment_engine.put_manifest(url, last_good)
                return Response(
                    content=last_good,
                    status_code=200,
                    headers={
                        "Content-Type": "application/vnd.apple.mpegurl",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Cache-Control": "public, max-age=3, stale-while-revalidate=3",
                        "Accept-Ranges": "bytes",
                        "Connection": "keep-alive",
                        "X-Cache": "BACKOFF-SHIELD-200"
                    }
                )"""

if old_sp_manifest_head.replace("\r\n", "\n") in sp_content.replace("\r\n", "\n"):
    sp_content = sp_content.replace("\r\n", "\n").replace(old_sp_manifest_head.replace("\r\n", "\n"), new_sp_manifest_head.replace("\r\n", "\n"))
    with open("backend/stream_proxy.py", "w", encoding="utf-8") as f:
        f.write(sp_content)
    print("backend/stream_proxy.py updated successfully!")
else:
    print("ERROR: old_sp_manifest_head not found in backend/stream_proxy.py")
