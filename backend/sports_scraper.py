import asyncio
import httpx
import re
import json
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any

TBILISI_TZ = timezone(timedelta(hours=4))

CATEGORIES = [
    {"slug": "all", "name": "All Sports", "icon": "fa-trophy"},
    {"slug": "football", "name": "Football", "icon": "fa-futbol"},
    {"slug": "rugby", "name": "Rugby", "icon": "fa-football"},
    {"slug": "basketball", "name": "Basketball", "icon": "fa-basketball"},
    {"slug": "tennis", "name": "Tennis", "icon": "fa-table-tennis-paddle-ball"},
    {"slug": "f1", "name": "Formula 1", "icon": "fa-flag-checkered"},
    {"slug": "mma", "name": "MMA & UFC", "icon": "fa-hand-fist"},
    {"slug": "boxing", "name": "Boxing", "icon": "fa-hand-back-fist"},
    {"slug": "others", "name": "Cyber Sport", "icon": "fa-gamepad"}
]

CATEGORY_MAP = {c["slug"]: c["name"] for c in CATEGORIES}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fbstream.st/"
}

class SportsScraper:
    def __init__(self):
        self._cache: List[Dict[str, Any]] = []
        self._cache_time: float = 0.0
        self._cache_ttl: float = 90.0  # 90 seconds
        self._lock = asyncio.Lock()
        self._match_cache: Dict[str, Any] = {}

    def _parse_iso_time(self, iso_str: str) -> Optional[datetime]:
        if not iso_str:
            return None
        try:
            return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _format_tbilisi_time(self, dt: Optional[datetime]) -> tuple[str, str, bool]:
        if not dt:
            return "TBD", "TBD", False
        
        dt_tbilisi = dt.astimezone(TBILISI_TZ)
        now_tbilisi = datetime.now(TBILISI_TZ)
        now_utc = datetime.now(timezone.utc)

        # A match is live if it started between now and 2.5 hours ago
        diff_sec = (now_utc - dt.astimezone(timezone.utc)).total_seconds()
        is_live = 0 <= diff_sec <= 9000  # 2.5 hours window

        if dt_tbilisi.date() == now_tbilisi.date():
            day_label = "Today"
        elif dt_tbilisi.date() == (now_tbilisi + timedelta(days=1)).date():
            day_label = "Tomorrow"
        else:
            day_label = dt_tbilisi.strftime("%d %b")

        time_str = dt_tbilisi.strftime("%H:%M")
        return day_label, time_str, is_live

    async def fetch_category_events(self, client: httpx.AsyncClient, cat_slug: str) -> List[Dict[str, Any]]:
        url = f"https://fbstream.st/stream/{cat_slug}"
        events = []
        try:
            r = await client.get(url, headers=HEADERS, timeout=12.0)
            if r.status_code != 200:
                return []
            
            details = re.findall(r'<details[^>]*fb-data-events-row[^>]*>(.*?)</details>', r.text, re.DOTALL | re.IGNORECASE)
            for det in details:
                time_m = re.search(r'<time[^>]+content="([^"]+)"', det)
                iso = time_m.group(1) if time_m else ""

                a_m = re.search(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>', det, re.DOTALL)
                href = a_m.group(1) if a_m else ""
                title = a_m.group(2) if a_m else ""
                if not title and a_m:
                    title = re.sub(r'<[^>]+>', '', a_m.group(3)).strip()
                    title = re.sub(r'^\d\d:\d\d\s*', '', title).strip()

                if not title:
                    continue

                icon_m = re.search(r'fb-icon\s+([a-zA-Z0-9_-]+)', det)
                icon = icon_m.group(1) if icon_m else ""

                disc_m = re.search(r'class="disclosure__content"\s+id="([^"]+)"', det)
                disc_id = disc_m.group(1) if disc_m else ""

                dt = self._parse_iso_time(iso)
                day_lbl, time_tbilisi, is_live = self._format_tbilisi_time(dt)

                slug = href.strip("/").split("/")[-1] if href else ""

                # Format teams if title contains ' - ' or ' vs '
                teams = [t.strip() for t in re.split(r'\s+-\s+|\s+vs\.?\s+', title, flags=re.IGNORECASE)]
                team1 = teams[0] if len(teams) > 0 else title
                team2 = teams[1] if len(teams) > 1 else ""

                events.append({
                    "id": f"{cat_slug}_{slug or disc_id}",
                    "category": CATEGORY_MAP.get(cat_slug, cat_slug.capitalize()),
                    "cat_slug": cat_slug,
                    "title": title,
                    "team1": team1,
                    "team2": team2,
                    "href": href,
                    "slug": slug,
                    "disc_id": disc_id,
                    "iso_utc": iso,
                    "day_tbilisi": day_lbl,
                    "time_tbilisi": time_tbilisi,
                    "is_live": is_live,
                    "icon": icon,
                    "timestamp": dt.timestamp() if dt else 0
                })
        except Exception as e:
            print(f"[SportsScraper] Error fetching category {cat_slug}: {e}")
        return events

    async def get_all_events(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force_refresh and self._cache and (now - self._cache_time < self._cache_ttl):
            # Recalculate is_live dynamically based on current time
            now_utc = datetime.now(timezone.utc)
            for e in self._cache:
                if e.get("timestamp"):
                    diff = (now_utc - datetime.fromtimestamp(e["timestamp"], tz=timezone.utc)).total_seconds()
                    e["is_live"] = 0 <= diff <= 9000
            return self._cache

        async with self._lock:
            # Double check lock pattern
            if not force_refresh and self._cache and (time.time() - self._cache_time < self._cache_ttl):
                return self._cache

            all_slugs = ["football", "rugby", "basketball", "tennis", "f1", "mma", "boxing", "others"]
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                tasks = [self.fetch_category_events(client, cat) for cat in all_slugs]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            merged = []
            seen_slugs = set()
            for r in results:
                if isinstance(r, list):
                    for e in r:
                        if e["slug"] and e["slug"] in seen_slugs:
                            continue
                        if e["slug"]:
                            seen_slugs.add(e["slug"])
                        merged.append(e)

            # Sort: Live first, then by timestamp
            merged.sort(key=lambda x: (0 if x["is_live"] else 1, x["timestamp"] if x["timestamp"] > 0 else float("inf")))
            self._cache = merged
            self._cache_time = time.time()
            return self._cache

    async def get_match_stream_options(self, slug: str) -> Dict[str, Any]:
        """Resolves available stream options (Stream 1, Stream 2, etc.) for a match."""
        if not slug:
            return {"error": "Missing match slug", "streams": []}

        # Check match cache (TTL 30s)
        cached = self._match_cache.get(slug)
        if cached and (time.time() - cached.get("_time", 0) < 30.0):
            return cached

        match_url = f"https://fbstream.st/live/stream/{slug}"
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=HEADERS) as client:
            try:
                r = await client.get(match_url)
                if r.status_code != 200:
                    return {"error": f"Match page returned HTTP {r.status_code}", "streams": []}
                
                html = r.text
                title_m = re.search(r'<title>(.*?)</title>', html)
                page_title = title_m.group(1).replace(" - FBStream", "").strip() if title_m else slug

                # Find stream buttons
                buttons = re.findall(r'<button[^>]+data-uri="([^"]+)"[^>]*>(.*?)</button>', html)
                streams = []

                if buttons:
                    for uri, btn_text in buttons:
                        clean_text = re.sub(r'<[^>]+>', '', btn_text).strip()
                        stream_slug = uri.strip("/").split("/")[-1]
                        streams.append({
                            "name": clean_text or f"Stream {len(streams)+1}",
                            "uri": uri,
                            "stream_slug": stream_slug,
                            "direct_url": f"https://fbstream.st/live/stream/{stream_slug}/",
                            "is_primary": "🌟" in clean_text or len(streams) == 0
                        })
                else:
                    # Default to Stream 1 and Stream 2
                    streams.append({
                        "name": "Stream 1 (Primary)",
                        "uri": f"/live/stream/{slug}-fb-1/",
                        "stream_slug": f"{slug}-fb-1",
                        "direct_url": f"https://fbstream.st/live/stream/{slug}-fb-1/",
                        "is_primary": True
                    })
                    streams.append({
                        "name": "Stream 2 (Backup)",
                        "uri": f"/live/stream/{slug}-fb-2/",
                        "stream_slug": f"{slug}-fb-2",
                        "direct_url": f"https://fbstream.st/live/stream/{slug}-fb-2/",
                        "is_primary": False
                    })

                result = {
                    "slug": slug,
                    "title": page_title,
                    "streams": streams,
                    "_time": time.time()
                }
                self._match_cache[slug] = result
                return result
            except Exception as e:
                return {"error": str(e), "streams": []}

    async def resolve_embed_url(self, stream_slug: str) -> Optional[str]:
        """Fetches the stream page and constructs the ad-free embed URL."""
        stream_url = f"https://fbstream.st/live/stream/{stream_slug}/"
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            try:
                r = await client.get(stream_url)
                if r.status_code != 200:
                    return None
                
                tag_m = re.search(r'<script[^>]+embed\.min\.js[^>]*>', r.text)
                if not tag_m:
                    return None
                
                tag = tag_m.group(0)
                pldm = re.search(r'data-pldm="([^"]+)"', tag).group(1)
                pid = re.search(r'data-pid="([^"]+)"', tag).group(1)
                play = re.search(r'data-play="([^"]+)"', tag).group(1)
                player = re.search(r'data-player="([^"]+)"', tag).group(1)
                gc = re.search(r'data-gc="([^"]+)"', tag).group(1)
                
                cfg_m = re.search(r'const\s+siteConfig\s*=\s*(\{.*?\});', r.text)
                if not cfg_m:
                    return None
                cfg = json.loads(cfg_m.group(1))

                embed_url = (
                    f"https://{pldm}/sd0embed/{gc}?"
                    f"pid={pid}&v={play}&player={player}&"
                    f"csrf={cfg['csrf']}&csrf_ip={cfg['csrf_ip']}&"
                    f"expires={cfg['sec_expires']}&sec_hash={cfg['sec_hash']}"
                )
                return embed_url
            except Exception as e:
                print(f"[SportsScraper] resolve_embed_url error: {e}")
                return None

    async def get_sanitized_player_html(self, stream_slug: str) -> str:
        """Fetches the embed player page, strips all popunders and ad scripts, returns clean HTML."""
        embed_url = await self.resolve_embed_url(stream_slug)
        if not embed_url:
            return """
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><style>body{background:#0b0f19;color:#94a3b8;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}</style></head>
            <body><div style="text-align:center;"><h3>Stream not yet available</h3><p>Please check back when the match starts or try another stream.</p></div></body>
            </html>
            """

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                r = await client.get(embed_url, headers={
                    "User-Agent": HEADERS["User-Agent"],
                    "Referer": f"https://fbstream.st/live/stream/{stream_slug}/"
                })
                html = r.text

                # Strip known ad domains and popup scripts completely
                ad_keywords = [
                    "eludestop.cyou", "budgetezy.org", "unfortunateheart.com",
                    "popundersPerIP", "minBid", "siteId", "a.bcdn.info", "adnetwork"
                ]

                def script_filter(match):
                    content = match.group(0)
                    if any(k in content for k in ad_keywords):
                        return "<!-- ad script removed -->"
                    return content

                html = re.sub(r'<script\b[^>]*>.*?</script>', script_filter, html, flags=re.DOTALL | re.IGNORECASE)

                # Ensure base URL is set to the embed host so relative assets resolve
                embed_host = re.search(r'https://[^/]+', embed_url).group(0)
                if "<head>" in html:
                    html = html.replace("<head>", f'<head><base href="{embed_host}/">')
                
                return html
            except Exception as e:
                return f"""
                <!DOCTYPE html>
                <html>
                <head><meta charset="utf-8"><style>body{background:#0b0f19;color:#ef4444;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}</style></head>
                <body><div style="text-align:center;"><h3>Error loading stream</h3><p>{str(e)}</p></div></body>
                </html>
                """

# Global singleton
sports_scraper = SportsScraper()
