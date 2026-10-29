
AD_TAG_PREFIXES = (
    "#EXT-X-CUE-OUT",
    "#EXT-X-CUE-IN",
    "#EXT-X-CUE-OUT-CONT",
    "#EXT-OATCLS-SCTE35",
    "#EXT-X-SCTE35",
    "#EXT-X-SPLICEPOINT",
)

AD_URL_PATTERNS = (
    "/ad/", "/ads/", "/ad_", "/adv/", "/advert/", "/preroll/", "/midroll/",
    "ad-segment", "adserver", "adsystem", "doubleclick", "yandex.ru/ads",
    "googleads", "spotxchange", "smartadserver", "vidazoo", "springserve", "teads"
)

def is_ad_segment_or_tag(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if any(s.startswith(prefix) for prefix in AD_TAG_PREFIXES):
        return True
    if s.startswith("#EXT-X-DATERANGE:") and any(x in s.lower() for x in ("ad", "google", "scte")):
        return True
    if not s.startswith("#"):
        lower = s.lower()
        if any(pat in lower for pat in AD_URL_PATTERNS):
            return True
        try:
            from .blocklist_manager import blocklist_manager
            if blocklist_manager and blocklist_manager.blocked_domains:
                parsed = urlparse(s)
                host = parsed.netloc.lower().split(":")[0]
                if host in blocklist_manager.blocked_domains:
                    return True
                parts = host.split(".")
                for i in range(len(parts) - 1):
                    if ".".join(parts[i:]) in blocklist_manager.blocked_domains:
                        return True
        except Exception:
            pass
    return False

import asyncio
import time
import gzip
import re
import uuid
import httpx
from urllib.parse import urljoin, quote, urlsplit, urlparse
from starlette.responses import StreamingResponse, Response
from fastapi import Request
import logging
from typing import Dict, Optional, Tuple, Any
from .config import FORCE_ABSOLUTE_LAN_URL

logger = logging.getLogger("stream_proxy")

# ---------------------------------------------------------------------------
# Strict Channel Switch Isolation & Stream Session Manager
# ---------------------------------------------------------------------------

class ActiveStreamSessionManager:
    """
    Guarantees strict single-stream isolation per device/client IP.
    When a channel switch occurs, any background requests from the
    previous channel/session are instantly terminated with HTTP 410 (Gone).
    This forces the TV's hardware decoder and media player to immediately
    halt the old player process and prevent overlapping/interleaved playback.
    """
    def __init__(self):
        # Map client_ip -> {"sid": str, "stream_url": str, "timestamp": float, "headers": dict}
        self._device_sessions: Dict[str, Dict[str, Any]] = {}
        # Global latest session ID
        self._latest_sid: str = f"s_init_{int(time.time())}"
        self._latest_stream_url: str = ""
        self._previous_stream_url: str = ""
        self._invalidated_sids: set = set()
        self._obsolete_urls: set = set()
        self._channel_switch_time: float = 0.0
        self._sid_headers: Dict[str, Dict[str, str]] = {}
        self._latest_headers: Dict[str, str] = {}

    def start_session(self, target_ip: Optional[str], stream_url: str, headers: Optional[Dict[str, str]] = None) -> str:
        sid = f"s_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        clean_url = stream_url.split("?")[0]
        now = time.time()

        # Invalidate old session ID
        if self._latest_sid:
            self._invalidated_sids.add(self._latest_sid)
        if self._latest_stream_url and self._latest_stream_url != clean_url:
            self._obsolete_urls.add(self._latest_stream_url.lower())
            self._previous_stream_url = self._latest_stream_url

        # Keep sets bounded
        if len(self._invalidated_sids) > 200:
            self._invalidated_sids = set(list(self._invalidated_sids)[-100:])
        if len(self._obsolete_urls) > 100:
            self._obsolete_urls = set(list(self._obsolete_urls)[-50:])

        self._latest_sid = sid
        self._latest_stream_url = clean_url
        self._channel_switch_time = now
        custom_hdrs = headers or {}
        self._latest_headers = custom_hdrs
        self._sid_headers[sid] = custom_hdrs

        info = {
            "sid": sid,
            "stream_url": clean_url,
            "timestamp": now,
            "headers": custom_hdrs
        }
        if target_ip and target_ip != "web_receiver":
            old_dev_sid = self._device_sessions.get(target_ip, {}).get("sid")
            if old_dev_sid:
                self._invalidated_sids.add(old_dev_sid)
            self._device_sessions[target_ip] = info

        self._device_sessions["127.0.0.1"] = info
        self._device_sessions["localhost"] = info

        logger.info(f"Stream session started: sid={sid} target={target_ip} url={clean_url}")
        return sid

    def get_session_headers(self, sid: Optional[str] = None, client_ip: Optional[str] = None) -> Dict[str, str]:
        if sid and sid in self._sid_headers:
            return self._sid_headers[sid]
        if client_ip and client_ip in self._device_sessions:
            return self._device_sessions[client_ip].get("headers", {})
        return self._latest_headers

    def get_session_id_for_url(self, manifest_url: str, client_ip: str) -> str:
        dev_info = self._device_sessions.get(client_ip)
        if dev_info:
            return dev_info["sid"]
        return self._latest_sid

    def is_session_active(self, client_ip: str, request_sid: Optional[str], target_url: str) -> bool:
        # Check 1: If request carries an explicitly invalidated session ID, reject immediately
        if request_sid and request_sid in self._invalidated_sids:
            logger.info(f"Terminating invalidated channel session request from {client_ip} [sid={request_sid}]")
            return False

        dev_info = self._device_sessions.get(client_ip)
        active_sid = dev_info["sid"] if dev_info else self._latest_sid
        active_url = dev_info["stream_url"] if dev_info else self._latest_stream_url

        # Check 2: If request carries a sid, verify against active session OR latest session
        if request_sid:
            if request_sid == active_sid or request_sid == self._latest_sid:
                return True
            logger.info(f"Terminating stale channel request from {client_ip}: sid {request_sid} != active {active_sid}")
            return False

        # Check 3: If no sid was provided, reject if URL is in obsolete URLs set
        clean_target = target_url.split("?")[0].lower()
        if clean_target in self._obsolete_urls:
            logger.info(f"Terminating obsolete channel URL request {clean_target}")
            return False

        return True

session_manager = ActiveStreamSessionManager()

# ---------------------------------------------------------------------------
# High-Tech Adaptive Segment Ring-Buffer & Lookahead Prefetch Engine
# ---------------------------------------------------------------------------

class SegmentCache:
    """
    In-memory ring buffer cache & conveyor-belt lookahead prefetcher.
    Delivers 0ms local RAM playback for live IPTV streams,
    eliminating weak Wi-Fi packet drops, stutter, and buffer underruns.
    """
    def __init__(self, max_segments: int = 120, ttl_seconds: float = 120.0):
        self.max_segments = max_segments
        self.ttl_seconds = ttl_seconds
        # Key: segment_url -> (data: bytes, content_type: str, timestamp: float)
        self._cache: Dict[str, Tuple[bytes, str, float]] = {}
        # Key: manifest_url -> (rewritten_manifest: bytes, timestamp: float)
        self._manifest_cache: Dict[str, Tuple[bytes, float, float]] = {}
        # Upstream rate limit backoff: domain -> backoff_until_timestamp
        self._domain_backoff: Dict[str, float] = {}
        # Map: segment_url -> list of upcoming segment_urls for conveyor-belt prefetching
        self._next_segments: Dict[str, list[str]] = {}
        # In-flight download tasks: segment_url -> asyncio.Task
        self._in_flight: Dict[str, asyncio.Task] = {}
        self._client: Optional[httpx.AsyncClient] = None

    def is_domain_in_backoff(self, domain: str) -> bool:
        if not domain:
            return False
        return time.time() < self._domain_backoff.get(domain, 0.0)

    def set_domain_backoff(self, domain: str, duration: float = 4.5):
        if domain:
            self._domain_backoff[domain] = time.time() + duration
            logger.warning(f"Upstream domain {domain} backoff active for {duration:.1f}s (shielding from 429)")

    def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=15.0),
                limits=httpx.Limits(max_keepalive_connections=100, max_connections=200, keepalive_expiry=180.0),
                follow_redirects=True
            )
        return self._client

    def _prune(self):
        now = time.time()
        # Remove expired
        expired = [k for k, v in self._cache.items() if now - v[2] > self.ttl_seconds]
        for k in expired:
            self._cache.pop(k, None)

        # Remove oldest if over capacity
        if len(self._cache) > self.max_segments:
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][2])
            for k in sorted_keys[: len(self._cache) - self.max_segments]:
                self._cache.pop(k, None)

    def get_cached(self, url: str) -> Optional[Tuple[bytes, str]]:
        """Instant RAM hit if segment is already in memory."""
        self._prune()
        if url in self._cache:
            data, content_type, _ = self._cache[url]
            self._cache[url] = (data, content_type, time.time())
            return data, content_type
        return None

    def put_cache(self, url: str, data: bytes, content_type: str):
        """Store segment into ring buffer."""
        self._cache[url] = (data, content_type, time.time())
        self._prune()

    def register_playlist_sequence(self, segments: list[str]):
        """Map each segment to its single immediate successor for gentle lookahead."""
        for idx, seg in enumerate(segments):
            next_items = segments[idx + 1 : idx + 2]
            self._next_segments[seg] = next_items
            clean_key = seg.split("?")[0]
            if clean_key != seg:
                self._next_segments[clean_key] = next_items

    def trigger_lookahead(self, current_url: str, headers: dict):
        """When TV decodes segment N, prefetch only the very next segment N+1 ahead of time."""
        clean_url = current_url.split("?")[0]
        next_urls = self._next_segments.get(current_url) or self._next_segments.get(clean_url)
        if next_urls:
            self.prefetch(next_urls, headers)

    def clear_for_channel_switch(self):
        """Clear cache when user changes channels so old channel frames never bleed in."""
        self._cache.clear()
        self._manifest_cache.clear()
        self._domain_backoff.clear()
        self._next_segments.clear()
        _client_manifest_poll.clear()
        for task in list(self._in_flight.values()):
            if not task.done():
                task.cancel()
        self._in_flight.clear()

    def get_manifest(self, url: str, min_ttl: float = 2.0) -> Optional[bytes]:
        """
        RFC 8216 Section 6.3.4 compliant debounce cache.
        Caches rewritten manifests for half of target duration (min 2.0s).
        Eliminates TV client spin loops (10+ req/sec) and protects upstream from HTTP 429.
        """
        now = time.time()
        if url in self._manifest_cache:
            entry = self._manifest_cache[url]
            data = entry[0]
            ts = entry[1]
            target_dur = entry[2] if len(entry) > 2 else 5.0
            effective_ttl = max(min_ttl, min(target_dur / 2.0, 3.5))
            if now - ts < effective_ttl:
                return data
        return None

    def get_last_manifest(self, url: str) -> Optional[bytes]:
        """Get last known good manifest regardless of age (fallback shield for 429/5xx)."""
        if url in self._manifest_cache:
            return self._manifest_cache[url][0]
        return None

    def put_manifest(self, url: str, data: bytes, target_duration: float = 5.0):
        self._manifest_cache[url] = (data, time.time(), target_duration)

    async def get_or_fetch(self, url: str, headers: dict) -> Tuple[Optional[bytes], str]:
        """Fetch segment from cache or upstream with auto-retry and in-flight deduplication."""
        cached = self.get_cached(url)
        if cached:
            return cached

        # In-Flight Deduplication: Wait if already being prefetched
        if url in self._in_flight:
            try:
                task = self._in_flight[url]
                return await task
            except Exception:
                pass

        # Upstream Fetch with Retry
        task = asyncio.create_task(self._fetch_upstream(url, headers))
        self._in_flight[url] = task
        try:
            return await task
        finally:
            self._in_flight.pop(url, None)

    async def _fetch_upstream(self, url: str, headers: dict) -> Tuple[Optional[bytes], str]:
        client = self.get_client()
        for attempt in range(3):
            try:
                req = client.build_request("GET", url, headers=headers)
                resp = await client.send(req)
                if resp.status_code == 200:
                    data = resp.content
                    ctype = resp.headers.get("content-type", "video/mp2t")
                    self.put_cache(url, data, ctype)
                    return data, ctype
                elif resp.status_code in [403, 404]:
                    break
            except Exception as e:
                if attempt == 2:
                    logger.debug(f"Segment fetch error for {url}: {e}")
                await asyncio.sleep(0.1 * (attempt + 1))
        return None, "video/mp2t"

    def prefetch(self, urls: list[str], headers: dict):
        """Asynchronously prefetch only 1 upcoming segment without congesting local Wi-Fi."""
        for url in urls[:1]:
            if url not in self._cache and url not in self._in_flight:
                task = asyncio.create_task(self._fetch_upstream(url, headers))
                self._in_flight[url] = task

    async def prewarm_channel(self, url: str, headers: dict):
        """
        Runs in background during channel cast.
        Pre-downloads the manifest and buffers the initial video segments into RAM
        so that when the TV hardware decoder connects, it receives an instant 0ms RAM hit!
        """
        try:
            client = self.get_client()
            req = client.build_request("GET", url, headers=headers)
            resp = await client.send(req)
            if resp.status_code != 200:
                return

            body = resp.content
            if body.startswith(b"\x1f\x8b"):
                body = gzip.decompress(body)

            text = body.decode("utf-8", errors="ignore")
            lines = text.splitlines()

            # Check if this is a master playlist pointing to a sub-variant
            variant_url = None
            is_master = False

            # Intelligent HLS Stream-Level Ad Stripping (eliminates audio/video PTS desync)
            filtered_lines = []
            skip_ad_block = False
            for line in lines:
                s = line.strip()
                if not s:
                    continue
                if s.startswith(("#EXT-X-CUE-OUT", "#EXT-OATCLS-SCTE35", "#EXT-X-SCTE35")):
                    skip_ad_block = True
                    continue
                elif s.startswith("#EXT-X-CUE-IN"):
                    skip_ad_block = False
                    continue
                if skip_ad_block and not s.startswith("#"):
                    continue
                if is_ad_segment_or_tag(s):
                    continue
                filtered_lines.append(line)
            lines = filtered_lines

            for line in lines:
                if line.startswith("#EXT-X-STREAM-INF"):
                    is_master = True
                elif is_master and line.strip() and not line.startswith("#"):
                    variant_url = urljoin(url, line.strip())
                    break

            if variant_url:
                req_var = client.build_request("GET", variant_url, headers=headers)
                resp_var = await client.send(req_var)
                if resp_var.status_code == 200:
                    body_var = resp_var.content
                    if body_var.startswith(b"\x1f\x8b"):
                        body_var = gzip.decompress(body_var)
                    text_var = body_var.decode("utf-8", errors="ignore")
                    lines = text_var.splitlines()
                    url = variant_url

            # Extract first segments and prefetch gently (first 2 chunks)
            segments = []
            for line in lines:
                s = line.strip()
                if s and not s.startswith("#"):
                    full_seg = urljoin(url, s)
                    if any(full_seg.lower().endswith(ext) for ext in [".ts", ".m4s", ".aac"]):
                        segments.append(full_seg)

            if segments:
                self.register_playlist_sequence(segments)
                # Prefetch only first 2 segments sequentially to avoid saturating Wi-Fi
                for seg in segments[:2]:
                    if seg not in self._cache and seg not in self._in_flight:
                        await self._fetch_upstream(seg, headers)
        except Exception as e:
            logger.debug(f"Prewarm notice for {url}: {e}")

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

segment_engine = SegmentCache()

# Map client_ip -> last manifest poll timestamp to eliminate TV CPU spin-locking
_client_manifest_poll: Dict[str, float] = {}

# ---------------------------------------------------------------------------
# Proxy Stream Endpoint Handler
# ---------------------------------------------------------------------------

async def proxy_stream(url: str, request: Request, server_host: str):
    """
    Enterprise-grade stream proxy:
    - Bypasses CORS and SSL certificate errors
    - Automatic GZIP decompression for compressed IPTV streams (like mcquack)
    - Instant low-latency chunk streaming (First Byte < 40ms)
    - Background lookahead segment prefetching to absorb weak Wi-Fi/internet
    - Strict cache invalidation on manifests to prevent stale channel frames
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
    }
    if "range" in request.headers:
        headers["Range"] = request.headers["range"]
    # Specific referrers for protected feeds (Georgian Silk Universal, Rugby TV, etc.)
    if "televizia" in url or "televiziebi" in url:
        headers["Referer"] = "https://www.televizia.org/"
        headers["Origin"] = "https://www.televizia.org"
    elif "cinerama" in url:
        headers["Referer"] = "https://cinerama.uz/"

    # Forward custom headers from movie/stream session (e.g. embed referrers)
    req_sid = request.query_params.get("sid")
    client_addr = request.client.host if request.client else "127.0.0.1"
    session_custom_headers = session_manager.get_session_headers(req_sid, client_addr)
    if session_custom_headers:
        headers.update(session_custom_headers)

    # Check if request is for a TS segment or an M3U8 manifest
    url_clean = url.split("?")[0].lower()
    is_segment = url_clean.endswith(".ts") or url_clean.endswith(".aac") or url_clean.endswith(".m4s")

    request_sid = request.query_params.get("sid")
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Strict Channel Switch Isolation (Applies to Manifests AND Video Segments):
    # Instantly terminate any lingering fetch from a previous channel session
    if not session_manager.is_session_active(client_ip, request_sid, url):
        logger.info(f"Terminating obsolete channel stream request from {client_ip} for {url} [sid={request_sid}] (HTTP 410)")
        return Response(
            content="Channel Switched: Stream Session Terminated",
            status_code=410,
            headers={
                "Content-Type": "text/plain",
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Connection": "close"
            }
        )

    # --- CASE 1: Video Segment (.ts / .m4s / .aac) ---
    if is_segment:
        # Conveyor-belt Lookahead: As TV decodes this segment, trigger prefetching of upcoming segments in RAM
        segment_engine.trigger_lookahead(url, headers)

        # 1. Instant RAM cache hit (< 1ms response to TV!)
        cached = segment_engine.get_cached(url)
        if cached:
            data, content_type = cached
            range_header = request.headers.get("range")
            if range_header and range_header.startswith("bytes="):
                total_len = len(data)
                try:
                    ranges = range_header[6:].split("-")
                    start = int(ranges[0]) if ranges[0] else 0
                    end = int(ranges[1]) if ranges[1] else total_len - 1
                    if start < total_len and end >= start:
                        end = min(end, total_len - 1)
                        sliced = data[start:end+1]
                        return Response(
                            content=sliced,
                            status_code=206,
                            headers={
                                "Content-Type": content_type or "video/mp2t",
                                "Content-Range": f"bytes {start}-{end}/{total_len}",
                                "Content-Length": str(len(sliced)),
                                "Accept-Ranges": "bytes",
                                "Access-Control-Allow-Origin": "*",
                                "Access-Control-Allow-Headers": "*",
                                "Cache-Control": "private, no-cache, no-store, must-revalidate",
                            }
                        )
                except Exception:
                    pass

            return Response(
                content=data,
                status_code=200,
                headers={
                    "Content-Type": content_type or "video/mp2t",
                    "Content-Length": str(len(data)),
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "private, no-cache, no-store, must-revalidate",
                    "Accept-Ranges": "bytes",
                }
            )

        # 2. Cold start segment fetch: Stream immediately to TV so playback starts with 0ms delay!
        client = segment_engine.get_client()
        try:
            if "range" in request.headers:
                headers["Range"] = request.headers["range"]

            upstream_req = client.build_request("GET", url, headers=headers)
            upstream_resp = await client.send(upstream_req, stream=True)

            content_type = upstream_resp.headers.get("content-type", "video/mp2t")
            buffer = bytearray()

            async def segment_stream_and_cache():
                try:
                    async for chunk in upstream_resp.aiter_bytes(chunk_size=131072):
                        buffer.extend(chunk)
                        yield chunk
                    # Once fully streamed, store in RAM cache for subsequent seek/reuse
                    if buffer:
                        segment_engine.put_cache(url, bytes(buffer), content_type)
                except asyncio.CancelledError:
                    pass
                finally:
                    await upstream_resp.aclose()

            resp_headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Content-Type": content_type or "video/mp2t",
                "Cache-Control": "private, no-cache, no-store, must-revalidate",
                "Accept-Ranges": "bytes",
            }
            if "content-length" in upstream_resp.headers:
                resp_headers["Content-Length"] = upstream_resp.headers["content-length"]

            return StreamingResponse(
                segment_stream_and_cache(),
                status_code=upstream_resp.status_code,
                headers=resp_headers
            )
        except Exception as e:
            logger.debug(f"Direct segment stream error for {url}: {e}")
            # Fallback to retry engine
            data, content_type = await segment_engine.get_or_fetch(url, headers)
            if data is not None:
                return Response(content=data, status_code=200, headers={"Content-Type": content_type or "video/mp2t"})
            return Response(content=f"Segment error: {e}", status_code=502)

    # --- CASE 2: HLS Playlist Manifest (.m3u8) or Direct Stream ---
    requested_url = url
    domain = urlsplit(url).netloc

    is_m3u8_target = url_clean.endswith(".m3u8") or "mpegurl" in request.headers.get("accept", "").lower()
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
                )

    client = segment_engine.get_client()
    try:
        upstream_req = client.build_request("GET", url, headers=headers)
        upstream_resp = await client.send(upstream_req, stream=True)

        content_type = upstream_resp.headers.get("content-type", "")
        is_m3u8 = "mpegurl" in content_type.lower() or url_clean.endswith(".m3u8")

        if is_m3u8:
            body = await upstream_resp.aread()
            await upstream_resp.aclose()

            # 429 / 5xx Rate Limit Shield & Circuit Breaker:
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
                    )
                # If no cached manifest exists yet, back off 0.5s and retry once
                await asyncio.sleep(0.5)
                try:
                    retry_req = client.build_request("GET", url, headers=headers)
                    retry_resp = await client.send(retry_req)
                    if retry_resp.status_code == 200:
                        body = retry_resp.content
                        upstream_resp = retry_resp
                except Exception:
                    pass

            # Automatically decompress GZIP if upstream returned compressed bytes
            if body.startswith(b"\x1f\x8b"):
                try:
                    body = gzip.decompress(body)
                except Exception as e:
                    logger.warning(f"Gzip decompression warning for {url}: {e}")

            # Use requested session ID if present, never upgrade an old session manifest to new active sid
            active_sid = request_sid if request_sid else session_manager.get_session_id_for_url(url, client_ip)
            text = body.decode("utf-8", errors="ignore")
            lines = text.splitlines()

            # Master Playlist Flattening: If playlist contains variant streams, resolve the best variant immediately
            # so the TV receives a direct media playlist on request #1 with zero round-trip overhead.
            has_variants = any(l.startswith("#EXT-X-STREAM-INF") for l in lines)
            if has_variants:
                best_variant_url = None
                for idx, line in enumerate(lines):
                    if line.startswith("#EXT-X-STREAM-INF") and idx + 1 < len(lines):
                        cand = lines[idx + 1].strip()
                        if cand and not cand.startswith("#"):
                            best_variant_url = urljoin(url, cand)
                            break
                if best_variant_url:
                    try:
                        v_req = client.build_request("GET", best_variant_url, headers=headers)
                        v_resp = await client.send(v_req)
                        if v_resp.status_code == 200:
                            v_body = v_resp.content
                            if v_body.startswith(b"\x1f\x8b"):
                                v_body = gzip.decompress(v_body)
                            url = best_variant_url
                            text = v_body.decode("utf-8", errors="ignore")
                            lines = text.splitlines()
                    except Exception as e:
                        logger.debug(f"Variant fetch inline warning for {best_variant_url}: {e}")

            # Extract target duration for RFC 8216 cache scheduling
            target_dur = 5.0
            for l in lines:
                if l.startswith("#EXT-X-TARGETDURATION:"):
                    try:
                        target_dur = float(l.split(":")[1].strip())
                    except Exception:
                        pass
                    break
            rewritten_lines = []
            segment_urls_for_prefetch = []
            variant_playlists_to_prewarm = []

            # Auto-detect local LAN requests for Hisense VIDAA / DLNA hardware compatibility
            use_absolute = FORCE_ABSOLUTE_LAN_URL or (
                server_host and not server_host.endswith(".trycloudflare.com") and not server_host.endswith(".ngrok-free.app")
            )

            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    full_segment_url = urljoin(url, stripped)
                    if use_absolute and server_host:
                        proxied_segment = f"http://{server_host}/api/stream/proxy?url={quote(full_segment_url, safe='')}&sid={active_sid}"
                    else:
                        proxied_segment = f"/api/stream/proxy?url={quote(full_segment_url, safe='')}&sid={active_sid}"
                    rewritten_lines.append(proxied_segment)

                    clean_seg = full_segment_url.split("?")[0].lower()
                    if clean_seg.endswith(".ts") or clean_seg.endswith(".m4s") or clean_seg.endswith(".aac"):
                        segment_urls_for_prefetch.append(full_segment_url)
                    elif clean_seg.endswith(".m3u8"):
                        variant_playlists_to_prewarm.append(full_segment_url)
                elif stripped.startswith("#EXT-X-KEY:") and 'URI="' in stripped:
                    def replace_key_uri(match):
                        key_uri = match.group(1)
                        full_key_url = urljoin(url, key_uri)
                        if use_absolute and server_host:
                            rewritten_key = f"http://{server_host}/api/stream/proxy?url={quote(full_key_url, safe='')}&sid={active_sid}"
                        else:
                            rewritten_key = f"/api/stream/proxy?url={quote(full_key_url, safe='')}&sid={active_sid}"
                        return f'URI="{rewritten_key}"'
                    rewritten_line = re.sub(r'URI="([^"]+)"', replace_key_uri, line)
                    rewritten_lines.append(rewritten_line)
                else:
                    rewritten_lines.append(line)

            # Register playlist sequence and gentle lookahead prefetch (only 1 upcoming segment):
            if segment_urls_for_prefetch:
                segment_engine.register_playlist_sequence(segment_urls_for_prefetch)
                segment_engine.prefetch(segment_urls_for_prefetch[-1:], headers)

            rewritten_body = "\r\n".join(rewritten_lines).encode("utf-8")
            # Store in short-lived manifest cache for 0.5s deduplication
            segment_engine.put_manifest(requested_url, rewritten_body, target_dur)
            if requested_url != url:
                segment_engine.put_manifest(url, rewritten_body, target_dur)

            max_age_val = max(1, int(target_dur / 2.0))
            return Response(
                content=rewritten_body,
                status_code=upstream_resp.status_code,
                headers={
                    "Content-Type": "application/vnd.apple.mpegurl",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": f"public, max-age={max_age_val}, stale-while-revalidate=2",
                    "Accept-Ranges": "bytes",
                    "Connection": "keep-alive",
                    "X-Cache": "MISS"
                }
            )

        # For MP4 or raw byte streams:
        async def stream_generator():
            try:
                async for chunk in upstream_resp.aiter_bytes(chunk_size=131072):
                    yield chunk
            except asyncio.CancelledError:
                pass
            finally:
                await upstream_resp.aclose()

        resp_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Content-Type": content_type or "video/mp2t",
        }
        for h in ["content-length", "content-range", "accept-ranges"]:
            if h in upstream_resp.headers:
                resp_headers[h.title()] = upstream_resp.headers[h]

        return StreamingResponse(
            stream_generator(),
            status_code=upstream_resp.status_code,
            headers=resp_headers
        )

    except Exception as e:
        logger.error(f"Stream proxy error for {url}: {e}")
        return Response(content=f"Stream proxy error: {str(e)}", status_code=502)
