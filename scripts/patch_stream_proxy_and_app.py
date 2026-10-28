import sys
import re
from pathlib import Path
import py_compile

def patch_stream_proxy():
    path = Path("backend/stream_proxy.py")
    code = path.read_text(encoding="utf-8")

    # 1. Ensure urlsplit is imported
    if "urlsplit" not in code:
        code = code.replace("from urllib.parse import urljoin, quote", "from urllib.parse import urljoin, quote, urlsplit")

    # 2. Add _domain_backoff and backoff helper methods to SegmentCache
    cache_init_pattern = r"(\s+self\._manifest_cache:\s*Dict\[[^\]]+\]\s*=\s*\{\})"
    backoff_init = r"""\1
        # Upstream rate limit circuit breaker: domain -> backoff_until_timestamp
        self._domain_backoff: Dict[str, float] = {}"""
    if "self._domain_backoff" not in code:
        code = re.sub(cache_init_pattern, backoff_init, code, count=1)

    # 3. Add backoff methods right before get_client
    backoff_methods = """    def is_domain_in_backoff(self, domain: str) -> bool:
        if not domain:
            return False
        return time.time() < self._domain_backoff.get(domain, 0.0)

    def set_domain_backoff(self, domain: str, duration: float = 4.5):
        if domain:
            self._domain_backoff[domain] = time.time() + duration
            logger.warning(f"Upstream domain {domain} backoff active for {duration:.1f}s (shielding from 429)")

    def get_client"""
    if "def is_domain_in_backoff" not in code:
        code = code.replace("    def get_client", backoff_methods, 1)

    # 4. In clear_for_channel_switch, clear _domain_backoff
    clear_pat = "self._manifest_cache.clear()"
    if "self._domain_backoff.clear()" not in code:
        code = code.replace(clear_pat, "self._manifest_cache.clear()\n        self._domain_backoff.clear()", 1)

    # 5. Update get_manifest to RFC 8216 target_dur / 2
    old_get_manifest = """    def get_manifest(self, url: str) -> Optional[bytes]:
        \"\"\"Debounce rapid manifest polls within 0.5s (eliminates duplicate concurrent network requests).\"\"\"
        now = time.time()
        if url in self._manifest_cache:
            data, ts = self._manifest_cache[url]
            if now - ts < 0.5:
                return data
        return None"""

    new_get_manifest = """    def get_manifest(self, url: str, min_ttl: float = 2.0) -> Optional[bytes]:
        \"\"\"
        RFC 8216 Section 6.3.4 compliant debounce cache.
        Caches rewritten manifests for half of target duration (min 2.0s).
        Eliminates TV client spin loops (10+ req/sec) and protects upstream from HTTP 429.
        \"\"\"
        now = time.time()
        if url in self._manifest_cache:
            entry = self._manifest_cache[url]
            data = entry[0]
            ts = entry[1]
            target_dur = entry[2] if len(entry) > 2 else 5.0
            effective_ttl = max(min_ttl, min(target_dur / 2.0, 3.5))
            if now - ts < effective_ttl:
                return data
        return None"""
    if "effective_ttl" not in code:
        code = code.replace(old_get_manifest, new_get_manifest, 1)

    # 6. Update put_manifest to store target_duration
    old_put_manifest = """    def put_manifest(self, url: str, data: bytes):
        self._manifest_cache[url] = (data, time.time())"""

    new_put_manifest = """    def put_manifest(self, url: str, data: bytes, target_duration: float = 5.0):
        self._manifest_cache[url] = (data, time.time(), target_duration)"""
    if "target_duration: float = 5.0" not in code:
        code = code.replace(old_put_manifest, new_put_manifest, 1)

    # 7. In proxy_stream CASE 2: use min_ttl=2.0 and domain backoff check
    old_case2_check = """    # --- CASE 2: HLS Playlist Manifest (.m3u8) or Direct Stream ---
    requested_url = url
    if url_clean.endswith(".m3u8") or "mpegurl" in request.headers.get("accept", "").lower():
        # Check rapid-poll manifest debounce cache (0.5s deduplication to prevent double-fetches)
        cached_m3u8 = segment_engine.get_manifest(url)
        if cached_m3u8 is not None:
            return Response(
                content=cached_m3u8,
                status_code=200,
                headers={
                    "Content-Type": "application/vnd.apple.mpegurl",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Cache": "HIT"
                }
            )"""

    new_case2_check = """    # --- CASE 2: HLS Playlist Manifest (.m3u8) or Direct Stream ---
    requested_url = url
    domain = urlsplit(url).netloc

    if url_clean.endswith(".m3u8") or "mpegurl" in request.headers.get("accept", "").lower():
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
    if "RFC 8216 Manifest Cache" not in code:
        code = code.replace(old_case2_check, new_case2_check, 1)

    # 8. Update upstream 429 handler in proxy_stream
    old_429_handler = """            # 429 / 5xx Rate Limit Shield: If upstream is throttling or errored, shield TV player with cached manifest
            if upstream_resp.status_code in (429, 500, 502, 503, 504):
                last_good = segment_engine.get_last_manifest(url)
                if last_good is not None:
                    logger.warning(f"Upstream returned HTTP {upstream_resp.status_code} for {url}. Shielding TV player with cached manifest.")
                    return Response(
                        content=last_good,
                        status_code=200,
                        headers={
                            "Content-Type": "application/vnd.apple.mpegurl",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "*",
                            "Cache-Control": "no-store",
                            "Pragma": "no-cache",
                            "X-Cache": "SHIELD-200"
                        }
                    )"""

    new_429_handler = """            # 429 / 5xx Rate Limit Shield & Circuit Breaker:
            if upstream_resp.status_code in (429, 500, 502, 503, 504):
                segment_engine.set_domain_backoff(domain, duration=4.5)
                last_good = segment_engine.get_last_manifest(url)
                if last_good is not None:
                    logger.warning(f"Upstream returned HTTP {upstream_resp.status_code} for {url}. Shielding TV player with cached manifest (backoff 4.5s).")
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
                            "X-Cache": "SHIELD-200"
                        }
                    )"""
    if "Shielding TV player with cached manifest (backoff 4.5s)" not in code:
        code = code.replace(old_429_handler, new_429_handler, 1)

    # 9. Extract target duration from manifest lines
    extract_target_dur = """            # Extract target duration for RFC 8216 cache scheduling
            target_dur = 5.0
            for l in lines:
                if l.startswith("#EXT-X-TARGETDURATION:"):
                    try:
                        target_dur = float(l.split(":")[1].strip())
                    except Exception:
                        pass
                    break"""
    if "target_dur = 5.0" not in code:
        code = code.replace("            rewritten_lines = []", extract_target_dur + "\n            rewritten_lines = []", 1)

    # 10. Fix prefetch from oldest [:1] to newest [-1:]
    old_prefetch = "segment_engine.prefetch(segment_urls_for_prefetch[:1], headers)"
    new_prefetch = "segment_engine.prefetch(segment_urls_for_prefetch[-1:], headers)"
    code = code.replace(old_prefetch, new_prefetch)

    # 11. Put manifest with target_dur
    code = code.replace("segment_engine.put_manifest(requested_url, rewritten_body)", "segment_engine.put_manifest(requested_url, rewritten_body, target_dur)")
    code = code.replace("segment_engine.put_manifest(url, rewritten_body)", "segment_engine.put_manifest(url, rewritten_body, target_dur)")

    # 12. Return manifest with RFC 8216 Cache-Control max-age
    old_manifest_resp = """            return Response(
                content=rewritten_body,
                status_code=upstream_resp.status_code,
                headers={
                    "Content-Type": "application/vnd.apple.mpegurl",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Cache": "MISS"
                }
            )"""

    new_manifest_resp = """            max_age_val = max(1, int(target_dur / 2.0))
            return Response(
                content=rewritten_body,
                status_code=upstream_resp.status_code,
                headers={
                    "Content-Type": "application/vnd.apple.mpegurl",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": f"public, max-age={max_age_val}, stale-while-revalidate=2",
                    "Pragma": "no-cache",
                    "X-Cache": "MISS"
                }
            )"""
    if "max_age_val" not in code:
        code = code.replace(old_manifest_resp, new_manifest_resp, 1)

    path.write_text(code, encoding="utf-8")
    py_compile.compile(str(path), doraise=True)
    print("backend/stream_proxy.py successfully patched and verified!")

def patch_app():
    path = Path("backend/app.py")
    code = path.read_text(encoding="utf-8")

    # 1. Update periodic_stream_health_task to avoid probing active channel domain and space gently (12s)
    old_health_task = """async def periodic_stream_health_task():
    \"\"\"Background task running every 5-10 minutes to re-probe channels and revive them.\"\"\"
    _load_stream_health()
    await asyncio.sleep(15.0)  # Wait for startup
    while True:
        try:
            for ch in iptv_manager.channels:
                cid = ch.get("id")
                sources = ch.get("sources", [])
                for s in sources:
                    s_url = s.get("url")
                    if s_url:
                        probe = await probe_stream_health(s_url, timeout=3.0)
                        if probe.get("ok"):
                            if cid and cid not in _last_good_sources:
                                _last_good_sources[cid] = s_url
                            break
                await asyncio.sleep(2.0)  # gentle spacing
            _save_stream_health()
            await asyncio.sleep(400.0)  # Every ~6-7 mins"""

    new_health_task = """async def periodic_stream_health_task():
    \"\"\"Background task running periodically to probe channels and revive them without triggering 429s.\"\"\"
    _load_stream_health()
    await asyncio.sleep(30.0)  # Wait for startup
    while True:
        try:
            from urllib.parse import urlparse
            active_stream = session_manager._latest_stream_url
            active_domain = urlparse(active_stream).netloc if active_stream else ""

            for ch in iptv_manager.channels:
                cid = ch.get("id")
                sources = ch.get("sources", [])
                for s in sources:
                    s_url = s.get("url")
                    if not s_url:
                        continue
                    s_domain = urlparse(s_url).netloc
                    # CRITICAL: Never probe the domain currently streaming to the TV!
                    if active_domain and s_domain == active_domain:
                        continue
                    probe = await probe_stream_health(s_url, timeout=3.0)
                    if probe.get("ok"):
                        if cid and cid not in _last_good_sources:
                            _last_good_sources[cid] = s_url
                        break
                await asyncio.sleep(12.0)  # gentle 12s spacing so we never exhaust upstream rate limit
            _save_stream_health()
            await asyncio.sleep(600.0)  # Every ~10 mins"""
    if "active_domain" not in code:
        code = code.replace(old_health_task, new_health_task, 1)

    # 2. Update DLNA channel switch in cast_media: seamless SetAVTransportURI without blind Stop
    old_dlna_switch = """        elif mode == "dlna":
            av_url = dev["av_transport_url"]
            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            # Step 1: Explicitly STOP active media player on TV so Hisense VIDAA tears down
            # the previous player process and completely releases the hardware video decoder surface
            try:
                await dlna_controller.stop(av_url)
                await asyncio.sleep(0.12)
            except Exception as e:
                logger.debug(f"DLNA stop notice: {e}")

            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            # Step 2: SetAVTransportURI with the new channel stream
            set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)
            if not set_ok:
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                await asyncio.sleep(0.2)
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                set_ok = await dlna_controller.set_av_transport_uri(av_url, tv_stream_url, title, req.mime_type)

            tv_online = ws_manager.current_state.get("tv_online", True)
            if not set_ok:
                if not tv_online:
                    # TV is known to be in standby/offline from monitor loop: send WoL and return immediately
                    logger.info(f"TV {dev['name']} is in standby/offline. Sending WoL...")
                    send_wake_on_lan(["d4:ab:cd:50:e5:d3", "18:30:0c:9e:7e:fc"])
                    tv_is_active = False
                else:
                    tv_is_active = False
            else:
                tv_is_active = True
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                await asyncio.sleep(0.1)
                if is_stale():
                    return {"status": "superseded", "version": my_version, "mode": mode}
                await dlna_controller.play(av_url)"""

    new_dlna_switch = """        elif mode == "dlna":
            av_url = dev["av_transport_url"]
            if is_stale():
                return {"status": "superseded", "version": my_version, "mode": mode}

            # Step 1: Seamlessly set new URI directly (avoids Hisense VIDAA exiting DLNA app to HDMI 1)
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
                await dlna_controller.play(av_url)
            else:
                tv_online = ws_manager.current_state.get("tv_online", True)
                if not tv_online:
                    logger.info(f"TV {dev['name']} is in standby/offline. Sending WoL...")
                    send_wake_on_lan(["d4:ab:cd:50:e5:d3", "18:30:0c:9e:7e:fc"])
                tv_is_active = False"""
    if "Seamlessly set new URI directly" not in code:
        code = code.replace(old_dlna_switch, new_dlna_switch, 1)

    path.write_text(code, encoding="utf-8")
    py_compile.compile(str(path), doraise=True)
    print("backend/app.py successfully patched and verified!")

if __name__ == "__main__":
    patch_stream_proxy()
    patch_app()
