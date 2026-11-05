"""
Universal Media Resolver for TV Hub
Extracts clean, ad-free direct video streams (MP4/HLS) from YouTube,
movie platforms, streaming sites, web players, and direct media URLs.
Equipped with browser TLS impersonation to bypass Cloudflare and anti-bot systems.
"""

import asyncio
import html
import json
import logging
import os
from pathlib import Path
import re
import time
import urllib.parse
from typing import Dict, Any, Optional, List, Tuple
import httpx

# Prepend local Node.js binary to PATH for yt-dlp JavaScript challenge solver
node_tools = Path(r"C:\Users\Anania Light Laptop\Downloads\Blue Ocean\.tools\node")
if node_tools.exists() and str(node_tools) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(node_tools) + os.pathsep + os.environ.get("PATH", "")

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    cffi_requests = None
    HAS_CURL_CFFI = False

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

def normalize_quality_label(width: int = 0, height: int = 0) -> str:
    """
    Normalizes video stream dimensions into industry-standard resolution tiers.
    Accurately maps cropped widescreen / cinemascope aspect ratios (e.g. 2.39:1 / 21:9):
    - 1920x804 / 1920x822 -> 1080p
    - 1280x536 / 1280x546 -> 720p
    - 854x358 -> 480p
    - 640x268 -> 360p
    - 426x178 -> 240p
    """
    w = int(width or 0)
    h = int(height or 0)

    if w >= 3800 or h >= 2000:
        return "4K"
    if w >= 2500 or h >= 1400:
        return "1440p"
    if w >= 1700 or h >= 750:
        return "1080p"
    if w >= 1100 or h >= 500:
        return "720p"
    if w >= 700 or h >= 340:
        return "480p"
    if w >= 500 or h >= 240:
        return "360p"
    if w >= 350 or h >= 160:
        return "240p"
    if h > 0:
        return f"{h}p"
    return "Auto"

QUALITY_TIER_RANK = {
    "4k": 4000, "2160p": 2160, "1440p": 1440,
    "1080p": 1080, "720p": 720, "480p": 480,
    "360p": 360, "240p": 240, "144p": 144
}

logger = logging.getLogger("media_resolver")

DIRECT_EXTENSIONS = (
    ".m3u8", ".mp4", ".webm", ".mkv", ".ts", ".mp3", ".aac", ".flv", ".mov", ".m4v"
)

STREAM_PROTOCOLS = ("rtsp://", "rtmp://", "mms://")

LANG_NAMES = {
    "en": "English", "eng": "English",
    "ka": "Georgian (ქართული)", "geo": "Georgian (ქართული)",
    "ru": "Russian (Русский)", "rus": "Russian (Русский)",
    "es": "Spanish (Español)", "spa": "Spanish (Español)",
    "de": "German (Deutsch)", "ger": "German (Deutsch)", "deu": "German (Deutsch)",
    "fr": "French (Français)", "fre": "French (Français)", "fra": "French (Français)",
    "it": "Italian (Italiano)", "ita": "Italian (Italiano)",
    "tr": "Turkish (Türkçe)", "tur": "Turkish (Türkçe)",
    "uk": "Ukrainian (Українська)", "ukr": "Ukrainian (Українська)",
    "pt": "Portuguese (Português)", "por": "Portuguese (Português)",
    "ja": "Japanese (日本語)", "jpn": "Japanese (日本語)",
    "zh": "Chinese (中文)", "chi": "Chinese (中文)", "zho": "Chinese (中文)",
    "ar": "Arabic (العربية)", "ara": "Arabic (العربية)"
}

class MediaResolver:
    def __init__(self):
        self._cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self.http_client = httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ka;q=0.8,ru;q=0.7",
            }
        )

    @staticmethod
    def _format_duration(seconds: int) -> str:
        seconds = max(0, int(seconds or 0))
        if seconds <= 0:
            return "--:--"
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _clean_extracted_url(raw_url: str) -> str:
        if not raw_url:
            return ""
        # 1. Unescape unicode escapes like \u0026, \/
        cleaned = raw_url.replace(r"\/", "/")
        cleaned = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), cleaned)
        # 2. Unescape HTML entities like &amp;, &#39;
        cleaned = html.unescape(cleaned)
        return cleaned.strip()

    @staticmethod
    def _extract_subtitles_and_qualities(info: Dict[str, Any]):
        subs_list = []
        all_subs = {**info.get("subtitles", {}), **info.get("automatic_captions", {})}
        norm_map = {"eng": "en", "rus": "ru", "kat": "ka", "geo": "ka", "spa": "es", "ger": "de", "deu": "de", "fra": "fr", "fre": "fr"}
        for code, entries in all_subs.items():
            short_code = code.split("-")[0].lower()
            short_code = norm_map.get(short_code, short_code)
            vtts = [e.get("url") for e in entries if (e.get("ext") == "vtt" or "fmt=vtt" in e.get("url", "") or e.get("url", "").endswith(".vtt")) and not e.get("url", "").endswith(".m3u8")]
            if not vtts:
                vtts = [e.get("url") for e in entries if "vtt" in e.get("url", "") and not e.get("url", "").endswith(".m3u8")]
            if vtts and not any(s["code"] == short_code for s in subs_list):
                name = LANG_NAMES.get(short_code, code.upper())
                subs_list.append({"code": short_code, "name": name, "url": vtts[0]})

        # Qualities: extract all distinct video heights (1080, 720, 480, 360, etc.)
        found_heights = set()
        quality_urls = {}
        for f in info.get("formats", []):
            h = f.get("height")
            fid = str(f.get("format_id", ""))
            ext = str(f.get("ext", "")).lower()
            vcodec = str(f.get("vcodec", "")).lower()
            if fid.startswith("sb") or ext in ("mhtml", "jpg", "jpeg", "webp"):
                continue
            if h and int(h) >= 144:
                found_heights.add(int(h))
                q_label = f"{int(h)}p"
                if f.get("url") and q_label not in quality_urls and vcodec != "none":
                    quality_urls[q_label] = f["url"]

        sorted_heights = sorted(list(found_heights), reverse=True)
        qualities = ["Auto"] + [f"{h}p" for h in sorted_heights]

        # Audio tracks (e.g. multi-language dubbed/original audio on YouTube)
        audio_tracks = []
        seen_langs = set()
        for f in info.get("formats", []):
            lang = f.get("language")
            if lang and f.get("vcodec") == "none" and f.get("acodec") != "none":
                note = f.get("format_note") or ""
                clean_name = note.split(",")[0].strip() if "," in note else note
                if not clean_name:
                    clean_name = LANG_NAMES.get(lang.split("-")[0].lower(), lang.upper())
                if lang not in seen_langs:
                    seen_langs.add(lang)
                    is_def = "default" in note.lower() or "original" in note.lower()
                    audio_tracks.append({
                        "code": lang,
                        "name": clean_name,
                        "default": is_def
                    })

        return subs_list, qualities, quality_urls, audio_tracks

    async def extract_hls_metadata(self, m3u8_url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Extract audio tracks, subtitles, and duration from HLS Master/Media Manifests."""
        audio_tracks = []
        subs = []
        total_duration = 0.0
        norm_map = {"eng": "en", "rus": "ru", "kat": "ka", "geo": "ka", "spa": "es", "ger": "de", "deu": "de", "fra": "fr", "fre": "fr"}

        try:
            req_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            if headers:
                req_headers.update(headers)
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                resp = await client.get(m3u8_url, headers=req_headers)
                if resp.status_code == 200:
                    text = resp.text
                    lines = text.splitlines()
                    seen_audio = set()
                    seen_subs = set()

                    parsed_qualities = set()
                    for line in lines:
                        if line.startswith("#EXT-X-MEDIA:"):
                            if "TYPE=AUDIO" in line:
                                name_m = re.search(r'NAME="([^"]+)"', line)
                                lang_m = re.search(r'LANGUAGE="([^"]+)"', line)
                                def_m = re.search(r'DEFAULT=(YES|NO)', line)
                                name = name_m.group(1) if name_m else "Audio"
                                lang = lang_m.group(1) if lang_m else ""
                                is_def = (def_m.group(1) == "YES") if def_m else False
                                if name not in seen_audio:
                                    seen_audio.add(name)
                                    audio_tracks.append({
                                        "name": name,
                                        "code": lang,
                                        "default": is_def
                                    })
                            elif "TYPE=SUBTITLES" in line:
                                name_m = re.search(r'NAME="([^"]+)"', line)
                                lang_m = re.search(r'LANGUAGE="([^"]+)"', line)
                                uri_m = re.search(r'URI="([^"]+)"', line)
                                name = name_m.group(1) if name_m else "Subtitles"
                                lang = lang_m.group(1) if lang_m else "en"
                                sub_uri = uri_m.group(1) if uri_m else ""
                                if sub_uri:
                                    full_sub = urllib.parse.urljoin(m3u8_url, sub_uri)
                                    norm_code = norm_map.get(lang.lower(), lang.lower()[:2])
                                    if norm_code not in seen_subs:
                                        seen_subs.add(norm_code)
                                        subs.append({"code": norm_code, "name": name, "url": full_sub})
                        elif line.startswith("#EXT-X-STREAM-INF:"):
                            res_m = re.search(r'RESOLUTION=(\d+)x(\d+)', line)
                            if res_m:
                                w = int(res_m.group(1))
                                h = int(res_m.group(2))
                                parsed_qualities.add(normalize_quality_label(w, h))
                            else:
                                bw_m = re.search(r'BANDWIDTH=(\d+)', line)
                                if bw_m:
                                    bw = int(bw_m.group(1))
                                    if bw >= 4500000:
                                        parsed_qualities.add("1080p")
                                    elif bw >= 2000000:
                                        parsed_qualities.add("720p")
                                    elif bw >= 900000:
                                        parsed_qualities.add("480p")
                                    else:
                                        parsed_qualities.add("360p")

                    def q_sort_key(q_str):
                        clean = str(q_str).lower().strip()
                        if clean in QUALITY_TIER_RANK:
                            return QUALITY_TIER_RANK[clean]
                        try:
                            return int(clean.replace("p", ""))
                        except Exception:
                            return 0
                    sorted_qs = sorted(list(parsed_qualities), key=q_sort_key, reverse=True)
                    movie_qualities = ["Auto"] + [q for q in sorted_qs if q != "Auto"] if sorted_qs else ["Auto", "1080p", "720p", "480p"]

                    # Calculate total duration if VOD
                    if "#EXTINF:" in text:
                        exts = re.findall(r'#EXTINF:([0-9\.]+)', text)
                        if exts and "#EXT-X-ENDLIST" in text:
                            total_duration = sum(float(x) for x in exts)
                    elif "#EXT-X-STREAM-INF:" in text:
                        first_variant = None
                        for idx, l in enumerate(lines):
                            if l.startswith("#EXT-X-STREAM-INF:") and idx + 1 < len(lines):
                                next_l = lines[idx + 1].strip()
                                if next_l and not next_l.startswith("#"):
                                    first_variant = urllib.parse.urljoin(m3u8_url, next_l)
                                    break
                        if first_variant:
                            v_resp = await client.get(first_variant, headers=req_headers)
                            if v_resp.status_code == 200 and "#EXT-X-ENDLIST" in v_resp.text:
                                exts = re.findall(r'#EXTINF:([0-9\.]+)', v_resp.text)
                                if exts:
                                    total_duration = sum(float(x) for x in exts)
        except Exception as e:
            logger.debug(f"HLS metadata extraction notice for {m3u8_url}: {e}")

        return {
            "audio_tracks": audio_tracks,
            "subtitles": subs,
            "qualities": movie_qualities if 'movie_qualities' in locals() else ["Auto", "1080p", "720p", "480p"],
            "duration": round(total_duration, 1)
        }

    async def extract_hls_audio_tracks(self, m3u8_url: str, headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Extract available audio tracks from HLS Master Manifest."""
        meta = await self.extract_hls_metadata(m3u8_url, headers)
        return meta.get("audio_tracks", [])

    async def fetch_page(self, url: str, referer: Optional[str] = None) -> Tuple[int, str]:
        """
        Fetches a web page with browser TLS impersonation to bypass Cloudflare/anti-bot challenges.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ka;q=0.8,ru;q=0.7",
        }
        if referer:
            headers["Referer"] = referer
            parsed = urllib.parse.urlparse(referer)
            headers["Origin"] = f"{parsed.scheme}://{parsed.netloc}"

        if HAS_CURL_CFFI:
            def _fetch_cffi():
                try:
                    r = cffi_requests.get(url, headers=headers, impersonate="chrome124", timeout=12)
                    return r.status_code, r.text
                except Exception as e:
                    logger.debug(f"cffi fetch error for {url}: {e}")
                    return 0, ""
            status, text = await asyncio.to_thread(_fetch_cffi)
            if status == 200 and text:
                return status, text

        try:
            resp = await self.http_client.get(url, headers=headers)
            return resp.status_code, resp.text
        except Exception as e:
            logger.debug(f"httpx fetch error for {url}: {e}")
            return 0, ""

    async def search_youtube(self, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Search YouTube directly without ads and return clean video items for 1-tap playback.
        """
        if not yt_dlp or not query or not query.strip():
            return []

        clean_q = query.strip()
        # Direct YouTube link handling: if user pasted a full YouTube URL into the search box
        if self.is_youtube(clean_q):
            try:
                def _extract_single():
                    ydl_opts = {
                        "quiet": True,
                        "extract_flat": True,
                        "skip_download": True,
                        "no_warnings": True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(clean_q, download=False)
                single_info = await asyncio.to_thread(_extract_single)
                if single_info:
                    vid_id = single_info.get("id") or "video"
                    title = single_info.get("title") or "YouTube Video"
                    dur = single_info.get("duration") or 0
                    dur_str = self._format_duration(dur)
                    thumb = single_info.get("thumbnails", [{}])[-1].get("url") if single_info.get("thumbnails") else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    return [{
                        "id": vid_id,
                        "title": title,
                        "url": single_info.get("webpage_url") or clean_q,
                        "thumbnail": thumb,
                        "duration": dur,
                        "duration_str": dur_str,
                        "channel": single_info.get("channel") or single_info.get("uploader") or "YouTube"
                    }]
            except Exception as e:
                logger.warning(f"Direct YouTube link resolution in search: {e}")

        def _search():
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "skip_download": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch{limit}:{query.strip()}", download=False)

        try:
            res = await asyncio.to_thread(_search)
            items = []
            for entry in res.get("entries", []):
                vid_id = entry.get("id")
                if not vid_id:
                    continue
                title = entry.get("title") or "YouTube Video"
                dur = entry.get("duration") or 0
                dur_str = self._format_duration(dur)
                thumb = entry.get("thumbnails", [{}])[-1].get("url") if entry.get("thumbnails") else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                items.append({
                    "id": vid_id,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "thumbnail": thumb,
                    "duration": dur,
                    "duration_str": dur_str,
                    "channel": entry.get("channel") or entry.get("uploader") or ""
                })
            return items
        except Exception as e:
            logger.warning(f"YouTube search error for '{query}': {e}")
            return []

    def is_direct_stream(self, url: str) -> bool:
        if not url:
            return False
        clean = url.split("?")[0].lower()
        if any(clean.endswith(ext) for ext in DIRECT_EXTENSIONS):
            return True
        if any(url.lower().startswith(proto) for proto in STREAM_PROTOCOLS):
            return True
        return False

    def is_youtube(self, url: str) -> bool:
        low = url.lower()
        return any(d in low for d in ("youtube.com", "youtu.be", "youtube-nocookie.com"))

    async def resolve(self, url: str, preferred_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entrypoint: takes any media or webpage URL, resolves it to an ad-free direct stream.
        """
        url = url.strip()
        if not url:
            return {"resolved": False, "error": "Empty URL"}

        if preferred_title and preferred_title.strip() in ("Live Stream", "Video Stream", ""):
            preferred_title = None

        cache_key = url
        now = time.time()
        if cache_key in self._cache:
            entry, exp = self._cache[cache_key]
            if now < exp:
                logger.info(f"Instant cache hit for {url[:60]}")
                out = dict(entry)
                if preferred_title:
                    out["title"] = preferred_title
                return out
            else:
                del self._cache[cache_key]

        res = None
        # 1. Direct Stream Link
        if self.is_direct_stream(url):
            mime = "application/vnd.apple.mpegurl" if ".m3u8" in url.lower() else "video/mp4"
            res = {
                "resolved": True,
                "stream_url": url,
                "title": preferred_title or "Direct Video Stream",
                "thumbnail": "",
                "duration": 0,
                "source_type": "direct",
                "is_ad_free": True,
                "mime_type": mime
            }

        # 2. YouTube (Video, Shorts, Mobile) - Zero Ads Guaranteed
        elif self.is_youtube(url):
            yt_res = await self.resolve_youtube(url, preferred_title)
            if yt_res.get("resolved"):
                res = yt_res

        # 3. Webpage / HTML5 / Iframe Scraper for movie sites & embedded web players (with Cloudflare bypass)
        if not res:
            scraped_res = await self.scrape_web_player(url, preferred_title)
            if scraped_res.get("resolved"):
                res = scraped_res

        # 4. Universal yt-dlp extractor (Vimeo, Dailymotion, Twitch, Movie Hosts)
        if not res and yt_dlp:
            ytdlp_res = await self.resolve_with_ytdlp(url, preferred_title)
            if ytdlp_res.get("resolved"):
                res = ytdlp_res

        if res and res.get("resolved"):
            # Extract HLS audio tracks if not already populated
            if not res.get("audio_tracks") and res.get("stream_url") and ".m3u8" in res.get("stream_url"):
                hls_audio = await self.extract_hls_audio_tracks(res["stream_url"], res.get("headers"))
                if hls_audio:
                    res["audio_tracks"] = hls_audio

            # Only cache for 15 minutes if duration was actually measured and title is clean!
            # If duration is 0 or unknown, cache for only 5 seconds so retries can resolve the real duration!
            has_valid_dur = (res.get("duration", 0) > 0)
            has_clean_title = (res.get("title") and res.get("title") not in ("YouTube Video", "Video Stream", "Live Stream", ""))
            cache_duration = 900 if (has_valid_dur and has_clean_title) else 5
            self._cache[cache_key] = (dict(res), now + cache_duration)
            if len(self._cache) > 80:
                oldest = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest]
            return res

        # Fallback: strictly mark resolved as False
        return {
            "resolved": False,
            "stream_url": url,
            "title": preferred_title or "Live Stream",
            "thumbnail": "",
            "duration": 0,
            "source_type": "unknown",
            "is_ad_free": False,
            "mime_type": "video/mp4",
            "error": "Could not extract direct stream from this webpage"
        }

    async def resolve_youtube(self, url: str, preferred_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts clean, progressive ad-free video stream from YouTube via yt-dlp.
        """
        if not yt_dlp:
            return {"resolved": False, "error": "yt-dlp is not installed"}

        def _extract():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'socket_timeout': 8,
                'remote_components': ['ejs:github'],
                'format': 'bestvideo[vcodec^=avc1][height<=1080]+bestaudio[acodec^=mp4a]/bestvideo[vcodec^=avc][height<=1080]+bestaudio/best[vcodec^=avc1][height<=1080]/best[ext=mp4]/best',
                'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'tv', 'web_embedded']}},
            }
            node_exe = r"C:\Users\Anania Light Laptop\Downloads\Blue Ocean\.tools\node\node.exe"
            if os.path.exists(node_exe):
                node_dir = os.path.dirname(node_exe)
                if node_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")
                ydl_opts['js_runtimes'] = {'node': {'path': node_exe}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(_extract)
            manifest_url = None
            for f in info.get("formats", []):
                if f.get("manifest_url"):
                    manifest_url = f.get("manifest_url")
                    break

            stream_url = manifest_url or info.get("url")
            if not stream_url:
                prog = [f for f in info.get("formats", []) if f.get("vcodec") != "none" and f.get("acodec") != "none"]
                if prog:
                    stream_url = prog[-1].get("url")

            if stream_url:
                title = preferred_title or info.get("title") or "YouTube Video"
                thumbnail = info.get("thumbnail") or ""
                duration = info.get("duration") or 0
                ext = info.get("ext") or "mp4"
                mime = "application/x-mpegurl" if (manifest_url or ".m3u8" in stream_url) else ("video/mp4" if ext == "mp4" else "video/webm")
                subs_list, qualities, quality_urls, audio_tracks = self._extract_subtitles_and_qualities(info)
                dur_str = self._format_duration(duration)
                yt_m = re.search(r"(?:youtu\.be/|v/|u/\w/|embed/|watch\?v=|&v=)([^#&?]{11})", url)
                vid_id = yt_m.group(1) if yt_m else (info.get("id") or "")
                logger.info(f"Successfully resolved YouTube stream: {title} (Zero Ads, {len(subs_list)} subs, {len(qualities)} qualities, {len(audio_tracks)} audio tracks)")
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "manifest_url": manifest_url,
                    "youtube_id": vid_id,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "duration_str": dur_str,
                    "source_type": "youtube",
                    "is_ad_free": True,
                    "mime_type": mime,
                    "subtitles": subs_list,
                    "qualities": qualities,
                    "quality_urls": quality_urls,
                    "audio_tracks": audio_tracks
                }
        except Exception as e:
            logger.warning(f"Local YouTube extraction notice for {url}: {e}")
            # Residential relay fallback for Cloud VPS instances:
            # If running on cloud and hit by YouTube datacenter IP challenge,
            # query the Home PC Hub residential tunnel to resolve without bot blocks.
            try:
                hub_tunnel = None
                ep_file = Path(__file__).resolve().parent.parent / "endpoint.json"
                if ep_file.exists():
                    ep_data = json.loads(ep_file.read_text(encoding="utf-8"))
                    cand = ep_data.get("hub_url")
                    if cand and "trycloudflare.com" in cand:
                        hub_tunnel = cand
                if not hub_tunnel:
                    async with httpx.AsyncClient(timeout=3.0) as gc:
                        gr = await gc.get("https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t=" + str(int(time.time())))
                        if gr.status_code == 200:
                            g_data = gr.json()
                            cand = g_data.get("hub_url")
                            if cand and "trycloudflare.com" in cand:
                                hub_tunnel = cand

                if not hub_tunnel:
                    from .cloud_relay import get_active_home_hub_url
                    hub_tunnel = await get_active_home_hub_url()
                if hub_tunnel:
                    async with httpx.AsyncClient(timeout=10.0, verify=False) as c:
                        r = await c.get(
                            f"{hub_tunnel}/api/media/resolve",
                            params={"url": url},
                            headers={"bypass-tunnel-reminder": "true"}
                        )
                        if r.status_code == 200:
                            data = r.json()
                            if data.get("resolved") and data.get("stream_url"):
                                logger.info(f"YouTube stream resolved via Home PC Hub residential tunnel: {data.get('title')}")
                                return data
            except Exception as relay_err:
                logger.debug(f"Home hub delegation notice: {relay_err}")

        # Graceful cloud fallback: If yt-dlp was challenged by YouTube bot detection,
        # return the video as an ad-free embed stream for Web Receiver / Web Cast!
        yt_id_match = re.search(r"(?:youtu\.be/|v/|u/\w/|embed/|watch\?v=|&v=)([^#&?]{11})", url)
        if yt_id_match:
            vid_id = yt_id_match.group(1)
            yt_dur = 0
            yt_title = preferred_title or ""

            # Fast oEmbed query (50ms, 100% reliable, never bot-blocked)
            if not yt_title or yt_title in ("YouTube Video", "Video Stream", "Live Stream"):
                try:
                    async with httpx.AsyncClient(timeout=3.0) as oc:
                        oer = await oc.get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json")
                        if oer.status_code == 200:
                            oed = oer.json()
                            if oed.get("title"):
                                yt_title = oed["title"]
                except Exception as oe_err:
                    logger.debug(f"oEmbed title notice: {oe_err}")

            if not yt_title:
                yt_title = "YouTube Video"

            try:
                innertube_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
                body = {
                    "videoId": vid_id,
                    "context": {
                        "client": {
                            "clientName": "WEB",
                            "clientVersion": "2.20240401.01.00",
                            "hl": "en",
                            "gl": "US"
                        }
                    }
                }
                async with httpx.AsyncClient(timeout=4.0) as hc:
                    hr = await hc.post(innertube_url, json=body, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
                    if hr.status_code == 200:
                        det = hr.json().get("videoDetails", {})
                        if det.get("title") and not preferred_title:
                            yt_title = det["title"]
                        if det.get("lengthSeconds"):
                            yt_dur = int(det["lengthSeconds"])
            except Exception as e:
                logger.debug(f"Innertube fast extraction notice: {e}")

            if yt_dur == 0 or not yt_title or yt_title == "YouTube Video":
                try:
                    async with httpx.AsyncClient(
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
                        timeout=3.0,
                        follow_redirects=True
                    ) as hc:
                        hr = await hc.get(f"https://www.youtube.com/watch?v={vid_id}")
                        if hr.status_code == 200:
                            dm = re.search(r'"lengthSeconds":"(\d+)"', hr.text)
                            if dm:
                                yt_dur = int(dm.group(1))
                            tm = re.search(r'<title>(.*?)(?: - YouTube)?</title>', hr.text)
                            if tm and not preferred_title:
                                yt_title = html.unescape(tm.group(1)).replace(" - YouTube", "").strip()
                except Exception as e:
                    logger.debug(f"Fast YouTube duration extraction notice: {e}")
            return {
                "resolved": True,
                "stream_url": f"https://www.youtube.com/watch?v={vid_id}",
                "youtube_id": vid_id,
                "title": yt_title,
                "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                "duration": yt_dur,
                "duration_str": self._format_duration(yt_dur),
                "source_type": "youtube",
                "is_ad_free": True,
                "mime_type": "video/mp4"
            }

        return {"resolved": False, "error": "Failed to extract YouTube stream"}

    async def resolve_with_ytdlp(self, url: str, preferred_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Generic yt-dlp resolver for supported video platforms with fast timeout.
        """
        def _extract():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'socket_timeout': 3.5,
                'format': 'best[protocol^=http]/best[ext=mp4]/best',
            }
            node_exe = r"C:\Users\Anania Light Laptop\Downloads\Blue Ocean\.tools\node\node.exe"
            if os.path.exists(node_exe):
                node_dir = os.path.dirname(node_exe)
                if node_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")
                ydl_opts['js_runtimes'] = {'node': {'path': node_exe}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.wait_for(asyncio.to_thread(_extract), timeout=4.5)
            stream_url = info.get("url")
            if stream_url:
                title = preferred_title or info.get("title") or "Video Stream"
                thumbnail = info.get("thumbnail") or ""
                duration = info.get("duration") or 0
                ext = info.get("ext") or "mp4"
                mime = "application/vnd.apple.mpegurl" if ".m3u8" in stream_url else f"video/{ext}"
                subs_list, qualities, quality_urls, audio_tracks = self._extract_subtitles_and_qualities(info)
                dur_str = self._format_duration(duration)
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "duration_str": dur_str,
                    "source_type": "platform",
                    "is_ad_free": True,
                    "mime_type": mime,
                    "subtitles": subs_list,
                    "qualities": qualities,
                    "quality_urls": quality_urls,
                    "audio_tracks": audio_tracks
                }
        except Exception:
            pass

        return {"resolved": False}

    def _parse_subtitles(self, sub_str: str) -> List[Dict[str, str]]:
        subs = []
        if not sub_str:
            return subs
        norm_map = {"eng": "en", "rus": "ru", "kat": "ka", "geo": "ka", "spa": "es", "ger": "de", "deu": "de", "fra": "fr", "fre": "fr"}
        matches = re.findall(r'\[([a-zA-Z0-9_\-]+)\](https?://[^\s,\[\]]+)', sub_str)
        for code, vtt_url in matches:
            short = code.lower().strip()
            norm_code = norm_map.get(short[:3], norm_map.get(short[:2], short[:2]))
            name = LANG_NAMES.get(norm_code, code.upper())
            subs.append({"code": norm_code, "name": name, "url": vtt_url})
        return subs

    async def _resolve_playerjs_playlist(self, pl_url: str, base_url: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Resolves PlayerJS playlist file (.plist, .txt, .json) into media stream, subtitles & thumbnail.
        """
        full_pl_url = urllib.parse.urljoin(base_url, pl_url)
        status, text = await self.fetch_page(full_pl_url, referer=base_url)
        if status != 200 or not text:
            return None

        # Clean JSON playlist
        try:
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                stream_url = item.get("file")
                if stream_url:
                    item_title = item.get("title") or title
                    poster = item.get("poster") or ""
                    sub_str = item.get("subtitle") or ""
                    subs = self._parse_subtitles(sub_str)
                    mime = "application/vnd.apple.mpegurl" if ".m3u8" in stream_url.lower() else "video/mp4"
                    dur = 0
                    dur_str = "Movie"
                    audio_tracks = []
                    hdrs = {
                        "Referer": base_url,
                        "Origin": urllib.parse.urlsplit(base_url).scheme + "://" + urllib.parse.urlsplit(base_url).netloc
                    }
                    if ".m3u8" in stream_url.lower():
                        try:
                            meta = await self.extract_hls_metadata(stream_url, hdrs)
                            if meta.get("duration", 0) > 0:
                                dur = meta["duration"]
                                dur_str = self._format_duration(dur)
                            audio_tracks = meta.get("audio_tracks", [])
                            if meta.get("subtitles") and not subs:
                                subs = meta["subtitles"]
                        except Exception:
                            pass
                    return {
                        "resolved": True,
                        "stream_url": stream_url,
                        "title": item_title,
                        "thumbnail": poster,
                        "duration": dur,
                        "duration_str": dur_str,
                        "source_type": "movie_platform",
                        "is_ad_free": True,
                        "mime_type": mime,
                        "subtitles": subs,
                        "audio_tracks": audio_tracks,
                        "qualities": ["Auto", "1080p", "720p", "480p"],
                        "headers": hdrs
                    }
        except Exception:
            pass

        # Text/encoded playlist
        m3u8_m = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', text)
        if m3u8_m:
            return {
                "resolved": True,
                "stream_url": m3u8_m[0],
                "title": title,
                "thumbnail": "",
                "duration": 0,
                "duration_str": "Movie",
                "source_type": "movie_platform",
                "is_ad_free": True,
                "mime_type": "application/vnd.apple.mpegurl",
                "subtitles": [],
                "qualities": ["Auto"],
                "headers": {"Referer": base_url}
            }

        return None

    async def scrape_web_player(self, url: str, preferred_title: Optional[str] = None, depth: int = 0, referer: Optional[str] = None) -> Dict[str, Any]:
        """
        Deep HTML and iframe scraper for movie sites, web players, and embed portals.
        Uses Cloudflare-bypassing client and unescapes nested iframes.
        """
        if depth > 3:
            return {"resolved": False}

        try:
            status, html_text = await self.fetch_page(url, referer=referer)
            if status != 200 or not html_text:
                return {"resolved": False}

            # Extract title if not provided
            page_title = preferred_title
            if not page_title:
                m_title = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
                if m_title:
                    raw_title = html.unescape(m_title.group(1))
                    page_title = re.sub(r"\s+", " ", raw_title).strip()
                    # Clean up common portal prefixes/suffixes
                    for remove_term in (" - GE.MOVIE", " - Watch Online", " Free Full Movie", " HD 1080p", " | GE.MOVIE"):
                        page_title = page_title.replace(remove_term, "")

            # PlayerJS Pattern: new Playerjs({ ... pl: "...", file: "..." })
            pl_match = re.search(r'Playerjs\s*\(\s*\{[^}]*?pl\s*:\s*["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            if pl_match:
                pl_path = self._clean_extracted_url(pl_match.group(1))
                res = await self._resolve_playerjs_playlist(pl_path, url, page_title or "Movie Stream")
                if res and res.get("resolved"):
                    return res

            file_match = re.search(r'Playerjs\s*\(\s*\{[^}]*?file\s*:\s*["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            if file_match:
                f_path = self._clean_extracted_url(file_match.group(1))
                if any(ext in f_path for ext in (".m3u8", ".mp4")):
                    mime = "application/vnd.apple.mpegurl" if ".m3u8" in f_path else "video/mp4"
                    dur = 0
                    dur_str = "Movie"
                    audio_tracks = []
                    subs = []
                    movie_qs = ["Auto", "1080p", "720p", "480p"]
                    if ".m3u8" in f_path:
                        headers_dict = {"Referer": url}
                        meta = await self.extract_hls_metadata(f_path, headers_dict)
                        if meta.get("duration", 0) > 0:
                            dur = meta["duration"]
                            dur_str = self._format_duration(dur)
                        audio_tracks = meta.get("audio_tracks", [])
                        subs = meta.get("subtitles", [])
                        if meta.get("qualities"):
                            movie_qs = meta["qualities"]
                    return {
                        "resolved": True,
                        "stream_url": f_path,
                        "title": page_title or "Movie Stream",
                        "thumbnail": "",
                        "duration": dur,
                        "duration_str": dur_str,
                        "source_type": "movie_platform",
                        "is_ad_free": True,
                        "mime_type": mime,
                        "subtitles": subs,
                        "audio_tracks": audio_tracks,
                        "qualities": movie_qs,
                        "headers": {"Referer": url}
                    }
                elif any(ext in f_path for ext in (".plist", ".txt", ".json")):
                    res = await self._resolve_playerjs_playlist(f_path, url, page_title or "Movie Stream")
                    if res and res.get("resolved"):
                        return res

            # Direct HLS or MP4 in HTML or JS variables
            m3u8_matches = re.findall(r'["\'](https?://[^"\'<>]+\.m3u8[^"\'<>]*)["\']', html_text)
            if m3u8_matches:
                stream_url = m3u8_matches[0]
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": page_title or "Movie Stream",
                    "thumbnail": "",
                    "duration": 0,
                    "duration_str": "Movie",
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "application/vnd.apple.mpegurl",
                    "subtitles": [],
                    "qualities": ["Auto"],
                    "headers": {"Referer": url}
                }

            mp4_matches = re.findall(r'["\'](https?://[^"\'<>]+\.mp4[^"\'<>]*)["\']', html_text)
            if mp4_matches:
                stream_url = mp4_matches[0]
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": page_title or "Movie Stream",
                    "thumbnail": "",
                    "duration": 0,
                    "duration_str": "Movie",
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "video/mp4",
                    "subtitles": [],
                    "qualities": ["Auto"],
                    "headers": {"Referer": url}
                }

            # HTML5 <video> or <source> tag
            video_src = re.findall(r'<video[^>]+src=["\'](https?://[^"\']+)["\']', html_text, re.IGNORECASE)
            if video_src:
                return {
                    "resolved": True,
                    "stream_url": video_src[0],
                    "title": page_title or "Movie Video",
                    "thumbnail": "",
                    "duration": 0,
                    "duration_str": "Movie",
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "video/mp4",
                    "subtitles": [],
                    "qualities": ["Auto"],
                    "headers": {"Referer": url}
                }

            source_src = re.findall(r'<source[^>]+src=["\'](https?://[^"\']+)["\']', html_text, re.IGNORECASE)
            if source_src:
                s_url = source_src[0]
                mime = "application/vnd.apple.mpegurl" if ".m3u8" in s_url else "video/mp4"
                return {
                    "resolved": True,
                    "stream_url": s_url,
                    "title": page_title or "Movie Video",
                    "thumbnail": "",
                    "duration": 0,
                    "duration_str": "Movie",
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": mime,
                    "subtitles": [],
                    "qualities": ["Auto"],
                    "headers": {"Referer": url}
                }

            # Embedded iframes: unescape &amp; and join relative links
            raw_iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            for raw_iframe_url in raw_iframes[:5]:
                iframe_url = html.unescape(raw_iframe_url)
                if not iframe_url.startswith("http"):
                    iframe_url = urllib.parse.urljoin(url, iframe_url)

                # Avoid tracking / ad iframes
                if any(x in iframe_url.lower() for x in ("google", "facebook", "disqus", "doubleclick", "adnxs", "mc.yandex", "clarity")):
                    continue

                logger.info(f"Following movie embed iframe: {iframe_url}")
                nested_res = await self.scrape_web_player(iframe_url, page_title, depth=depth + 1, referer=url)
                if nested_res.get("resolved"):
                    return nested_res

        except Exception as e:
            logger.debug(f"Web scraper error for {url}: {e}")

        return {"resolved": False}

media_resolver = MediaResolver()
