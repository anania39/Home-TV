"""
Universal Media Resolver for TV Hub
Extracts clean, ad-free direct video streams (MP4/HLS) from YouTube,
movie platforms, streaming sites, web players, and direct media URLs.
"""

import asyncio
import logging
import re
import urllib.parse
from typing import Dict, Any, Optional
import httpx

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

logger = logging.getLogger("media_resolver")

DIRECT_EXTENSIONS = (
    ".m3u8", ".mp4", ".webm", ".mkv", ".ts", ".mp3", ".aac", ".flv", ".mov", ".m4v"
)

STREAM_PROTOCOLS = ("rtsp://", "rtmp://", "mms://")

class MediaResolver:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=8.0,
            follow_redirects=True,
            verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

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

        # 3. Universal yt-dlp extractor (Vimeo, Dailymotion, Twitch, Movie Hosts)
        if yt_dlp:
            ytdlp_res = await self.resolve_with_ytdlp(url, preferred_title)
            if ytdlp_res.get("resolved"):
                return ytdlp_res

        # 4. Webpage / HTML5 / Iframe Scraper for movie sites & embedded web players
        scraped_res = await self.scrape_web_player(url, preferred_title)
        if scraped_res.get("resolved"):
            return scraped_res

        # Fallback: return as-is
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
                logger.info(f"Successfully resolved YouTube stream: {title} (Zero Ads)")
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "source_type": "youtube",
                    "is_ad_free": True,
                    "mime_type": mime
                }
        except Exception as e:
            logger.warning(f"YouTube extraction error for {url}: {e}")

        return {"resolved": False, "error": "Failed to extract YouTube stream"}

    async def resolve_with_ytdlp(self, url: str, preferred_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Generic yt-dlp resolver for supported video platforms.
        """
        def _extract():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'format': 'best[protocol^=http]/best[ext=mp4]/best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(_extract)
            stream_url = info.get("url")
            if stream_url:
                title = preferred_title or info.get("title") or "Video Stream"
                thumbnail = info.get("thumbnail") or ""
                duration = info.get("duration") or 0
                ext = info.get("ext") or "mp4"
                mime = "application/vnd.apple.mpegurl" if ".m3u8" in stream_url else f"video/{ext}"
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "source_type": "platform",
                    "is_ad_free": True,
                    "mime_type": mime
                }
        except Exception:
            pass

        return {"resolved": False}

    async def scrape_web_player(self, url: str, preferred_title: Optional[str] = None, depth: int = 0) -> Dict[str, Any]:
        """
        Deep HTML and iframe scraper for movie sites, web players, and embed portals.
        """
        if depth > 2:
            return {"resolved": False}

        try:
            resp = await self.http_client.get(url)
            if resp.status_code != 200:
                return {"resolved": False}

            html_text = resp.text

            # Extract title if not provided
            page_title = preferred_title
            if not page_title:
                m_title = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
                if m_title:
                    page_title = re.sub(r"\s+", " ", m_title.group(1)).strip()

            # Pattern 1: Direct HLS or MP4 in HTML or JS variables
            m3u8_matches = re.findall(r'["\'](https?://[^"\'<>]+\.m3u8[^"\'<>]*)["\']', html_text)
            if m3u8_matches:
                stream_url = m3u8_matches[0]
                return {
                    "resolved": True,
                    "stream_url": stream_url,
                    "title": page_title or "Movie Stream",
                    "thumbnail": "",
                    "duration": 0,
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "application/vnd.apple.mpegurl"
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
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "video/mp4"
                }

            # Pattern 2: HTML5 <video> or <source> tag
            video_src = re.findall(r'<video[^>]+src=["\'](https?://[^"\']+)["\']', html_text, re.IGNORECASE)
            if video_src:
                return {
                    "resolved": True,
                    "stream_url": video_src[0],
                    "title": page_title or "Movie Video",
                    "thumbnail": "",
                    "duration": 0,
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "video/mp4"
                }

            source_src = re.findall(r'<source[^>]+src=["\'](https?://[^"\']+)["\']', html_text, re.IGNORECASE)
            if source_src:
                return {
                    "resolved": True,
                    "stream_url": source_src[0],
                    "title": page_title or "Movie Video",
                    "thumbnail": "",
                    "duration": 0,
                    "source_type": "movie_platform",
                    "is_ad_free": True,
                    "mime_type": "video/mp4"
                }

            # Pattern 3: Embedded iframes (follow embeds like player.vidsrc, streamtape, etc.)
            iframes = re.findall(r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']', html_text, re.IGNORECASE)
            for iframe_url in iframes[:3]:
                # Avoid tracking/ad iframes
                if any(x in iframe_url.lower() for x in ("google", "facebook", "disqus", "doubleclick", "ads")):
                    continue
                nested_res = await self.scrape_web_player(iframe_url, page_title, depth=depth + 1)
                if nested_res.get("resolved"):
                    return nested_res

        except Exception as e:
            logger.debug(f"Web scraper error for {url}: {e}")

        return {"resolved": False}

media_resolver = MediaResolver()
