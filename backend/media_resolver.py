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
import re
import urllib.parse
from typing import Dict, Any, Optional, List, Tuple
import httpx

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
            return "Live"
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
        for code, entries in all_subs.items():
            short_code = code.split("-")[0].lower()
            vtts = [e.get("url") for e in entries if e.get("ext") == "vtt" or "vtt" in e.get("url", "")]
            if vtts and not any(s["code"] == short_code for s in subs_list):
                name = LANG_NAMES.get(short_code, code.upper())
                subs_list.append({"code": short_code, "name": name, "url": vtts[0]})

        # Qualities
        qualities = ["Auto"]
        quality_urls = {}
        for f in info.get("formats", []):
            h = f.get("height")
            if h and f.get("url"):
                q_label = f"{h}p"
                if q_label not in qualities:
                    qualities.append(q_label)
                    quality_urls[q_label] = f["url"]

        return subs_list, qualities, quality_urls

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

        # 1. Direct Stream Link
        if self.is_direct_stream(url):
            mime = "application/vnd.apple.mpegurl" if ".m3u8" in url.lower() else "video/mp4"
            return {
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
        if self.is_youtube(url):
            yt_res = await self.resolve_youtube(url, preferred_title)
            if yt_res.get("resolved"):
                return yt_res

        # 3. Webpage / HTML5 / Iframe Scraper for movie sites & embedded web players (with Cloudflare bypass)
        scraped_res = await self.scrape_web_player(url, preferred_title)
        if scraped_res.get("resolved"):
            return scraped_res

        # 4. Universal yt-dlp extractor (Vimeo, Dailymotion, Twitch, Movie Hosts)
        if yt_dlp:
            ytdlp_res = await self.resolve_with_ytdlp(url, preferred_title)
            if ytdlp_res.get("resolved"):
                return ytdlp_res

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
                'format': 'best[protocol^=http]/best[ext=mp4]/best',
                'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'tv', 'web']}}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(_extract)
            stream_url = info.get("url")
            if not stream_url:
                # Search formats
                prog = [f for f in info.get("formats", []) if f.get("vcodec") != "none" and f.get("acodec") != "none"]
                if prog:
                    stream_url = prog[-1].get("url")

            if stream_url:
                title = preferred_title or info.get("title") or "YouTube Video"
                thumbnail = info.get("thumbnail") or ""
                duration = info.get("duration") or 0
                ext = info.get("ext") or "mp4"
                mime = "application/vnd.apple.mpegurl" if ".m3u8" in stream_url else ("video/mp4" if ext == "mp4" else "video/webm")
                subs_list, qualities, quality_urls = self._extract_subtitles_and_qualities(info)
                dur_str = self._format_duration(duration)
                logger.info(f"Successfully resolved YouTube stream: {title} (Zero Ads, {len(subs_list)} subs)")
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "duration_str": dur_str,
                    "source_type": "youtube",
                    "is_ad_free": True,
                    "mime_type": mime,
                    "subtitles": subs_list,
                    "qualities": qualities,
                    "quality_urls": quality_urls
                }
        except Exception as e:
            logger.warning(f"YouTube extraction error for {url}: {e}")

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
                subs_list, qualities, quality_urls = self._extract_subtitles_and_qualities(info)
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
                    "quality_urls": quality_urls
                }
        except Exception:
            pass

        return {"resolved": False}

    def _parse_subtitles(self, sub_str: str) -> List[Dict[str, str]]:
        subs = []
        if not sub_str:
            return subs
        matches = re.findall(r'\[([a-zA-Z0-9_\-]+)\](https?://[^\s,\[\]]+)', sub_str)
        for code, vtt_url in matches:
            short = code.lower().strip()
            name = LANG_NAMES.get(short, code.upper())
            subs.append({"code": short, "name": name, "url": vtt_url})
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
                    return {
                        "resolved": True,
                        "stream_url": stream_url,
                        "title": item_title,
                        "thumbnail": poster,
                        "duration": 0,
                        "duration_str": "Movie",
                        "source_type": "movie_platform",
                        "is_ad_free": True,
                        "mime_type": mime,
                        "subtitles": subs,
                        "qualities": ["Auto", "1080p", "720p", "480p"],
                        "headers": {
                            "Referer": base_url,
                            "Origin": urllib.parse.urlsplit(base_url).scheme + "://" + urllib.parse.urlsplit(base_url).netloc
                        }
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
                    return {
                        "resolved": True,
                        "stream_url": f_path,
                        "title": page_title or "Movie Stream",
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
