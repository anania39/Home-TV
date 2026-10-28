import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import PLAYLISTS_DIR, BASE_DIR

logger = logging.getLogger("iptv")
CANONICAL_LOGOS_JSON = BASE_DIR / "docs" / "grokbot" / "channel-logos.json"
CHANNELS_BACKUPS_JSON = PLAYLISTS_DIR / "channels-with-backups.json"
CHANNELS_BACKUPS_DOCS_JSON = BASE_DIR / "docs" / "grokbot" / "channels-with-backups.json"

LOGOS_FALLBACK = {
    "ru-rtdoc-ru": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/RT_Doc.svg/800px-RT_Doc.svg.png",
    "en-cbc-news": "https://i.imgur.com/SjTdhvJ.png",
    "en-bloomberg-asia": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Bloomberg_Television_logo_2016.svg/640px-Bloomberg_Television_logo_2016.svg.png",
    "en-bloomberg-eu": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Bloomberg_Television_logo_2016.svg/640px-Bloomberg_Television_logo_2016.svg.png",
    "en-sky-au1": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Sky_News_Australia_logo_2019.svg/960px-Sky_News_Australia_logo_2019.svg.png",
    "en-sky-au3": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Sky_News_Australia_logo_2019.svg/960px-Sky_News_Australia_logo_2019.svg.png",
    "en-cbc-comedy": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png",
    "en-cbc-explore": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png",
    "en-cbc-kids": "https://cbc-centredepresse.tor1.digitaloceanspaces.com/upload/site/en/article_picture/3984/CBC_Kids_Logo.jpg",
    "en-cbc-heartland": "https://upload.wikimedia.org/wikipedia/en/b/ba/Heartland_TV_logo.png",
    "en-cbc-murdoch": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png",
    "en-cbc-schitt": "https://upload.wikimedia.org/wikipedia/commons/4/40/Schitt%27s_Creek_logo.png"
}

class IPTVManager:
    def __init__(self):
        self.channels: List[Dict[str, Any]] = []
        self.languages: List[str] = ["All", "Georgian", "Russian", "English"]
        self.genres: List[str] = ["All", "News", "Movies", "Sports", "Kids", "Music", "Entertainment", "Documentaries"]
        self.load_default_playlist()

    def parse_m3u(self, content: str) -> List[Dict[str, Any]]:
        """Parse M3U/M3U8 playlist with EXTINF tags and custom metadata."""
        channels = []
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        current_channel = {}
        for line in lines:
            if line.startswith("#EXTINF:"):
                current_channel = {}
                tvg_name = re.search(r'tvg-name="([^"]+)"', line, re.IGNORECASE)
                tvg_logo = re.search(r'tvg-logo="([^"]+)"', line, re.IGNORECASE)
                group_title = re.search(r'group-title="([^"]+)"', line, re.IGNORECASE)
                tvg_id = re.search(r'tvg-id="([^"]+)"', line, re.IGNORECASE)
                genre_m = re.search(r'genre="([^"]+)"', line, re.IGNORECASE)
                pop_m = re.search(r'popularity="([^"]+)"', line, re.IGNORECASE)

                comma_idx = line.rfind(',')
                display_name = line[comma_idx + 1:].strip() if comma_idx != -1 else "Live Channel"

                group = group_title.group(1) if group_title else "General"
                
                # Determine language & genre
                lang = "English"
                if "georgian" in group.lower() or "ge-" in (tvg_id.group(1) if tvg_id else "") or any(c in display_name for c in "აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ"):
                    lang = "Georgian"
                elif "russian" in group.lower() or "ru-" in (tvg_id.group(1) if tvg_id else "") or any(c in display_name for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ"):
                    lang = "Russian"

                # Determine genre if not explicit
                genre = genre_m.group(1) if genre_m else "General"
                if genre == "General":
                    low_name = display_name.lower()
                    if any(w in low_name for w in ["news", "ნიუსი", "новости", "euronews", "bmg", "1tv", "პირველი", "formula", "pirveli"]):
                        genre = "News"
                    elif any(w in low_name for w in ["kino", "movie", "film", "кино", "фильм", "series", "dorama", "imedi", "fox", "amedia", "murdoch", "gds"]):
                        genre = "Movies"
                    elif any(w in low_name for w in ["sport", "სპორტ", "спорт", "red bull", "avto", "rybalka", "okhota"]):
                        genre = "Sports"
                    elif any(w in low_name for w in ["kids", "детский", "karusel", "карусель"]):
                        genre = "Kids"
                    elif any(w in low_name for w in ["music", "музыка", "1hd", "bridge"]):
                        genre = "Music"
                    elif any(w in low_name for w in ["discovery", "animal", "space", "nasa", "ertsulovneba", "explore", "nature", "abaza", "apsua"]):
                        genre = "Documentaries"
                    else:
                        genre = "Entertainment"

                pop = int(pop_m.group(1)) if pop_m else 70

                current_channel = {
                    "id": tvg_id.group(1) if tvg_id else f"ch_{len(channels)+1}",
                    "name": tvg_name.group(1) if tvg_name else display_name,
                    "logo": tvg_logo.group(1) if tvg_logo else "",
                    "group": group,
                    "language": lang,
                    "genre": genre,
                    "popularity": pop,
                    "url": ""
                }
            elif not line.startswith("#") and (line.startswith("http://") or line.startswith("https://") or line.startswith("rtmp://") or line.startswith("rtsp://")):
                if current_channel:
                    current_channel["url"] = line
                    if not current_channel.get("id"):
                        current_channel["id"] = f"ch_{len(channels)+1}"
                    channels.append(current_channel)
                    current_channel = {}

        return channels

    def load_default_playlist(self):
        """Load and merge complete channel collection (130+ channels across Georgian, Russian, English) with logos and backups."""
        logos_data = []
        if CANONICAL_LOGOS_JSON.exists():
            try:
                logos_data = json.loads(CANONICAL_LOGOS_JSON.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error reading canonical logos json: {e}")

        backups_data = []
        target_json = CHANNELS_BACKUPS_JSON if CHANNELS_BACKUPS_JSON.exists() else (
            CHANNELS_BACKUPS_DOCS_JSON if CHANNELS_BACKUPS_DOCS_JSON.exists() else None
        )
        if target_json and target_json.exists():
            try:
                backups_data = json.loads(target_json.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error reading backups json: {e}")

        # Index backups by id and lowercase name for fast lookup
        b_by_id = {b["id"]: b for b in backups_data if "id" in b}
        b_by_name = {b["name"].lower().strip(): b for b in backups_data if "name" in b}

        merged = []
        seen_ids = set()
        seen_names = set()

        # 1. Canonical channels with logos & curated ordering
        for idx, c in enumerate(logos_data):
            cid = c["id"]
            name = c["name"]
            cname_low = name.lower().strip()
            seen_ids.add(cid)
            seen_names.add(cname_low)

            b_match = b_by_id.get(cid) or b_by_name.get(cname_low)
            sources = []
            if b_match and b_match.get("sources"):
                sources = list(b_match["sources"])
            elif c.get("stream_url"):
                sources = [{
                    "url": c["stream_url"],
                    "type": c.get("stream_type", "hls"),
                    "max_res": "1080p",
                    "headers": {}
                }]

            primary_url = sources[0]["url"] if sources else c.get("stream_url", "")
            if not primary_url:
                continue

            local_logo = f"/static/logos/{cid}.png" if (BASE_DIR / "static" / "logos" / f"{cid}.png").exists() else ""
            logo = local_logo or (b_match.get("logo") if b_match and "wikimedia" not in b_match.get("logo", "") else "") or (c.get("logo_url") if "wikimedia" not in c.get("logo_url", "") else "") or LOGOS_FALLBACK.get(cid, "")
            is_dead = c.get("stream_status") == "dead" or cid in ["ge-pirveli", "ge-euronews", "ru-rossiya1", "ru-rossiya24"]
            pop = max(10, 100 - idx) if not is_dead else 5

            # Genre normalization
            genre = c.get("genre", "General")
            if genre == "General":
                low = name.lower()
                if any(w in low for w in ["news", "ნიუსი", "новости", "euronews", "bmg", "1tv", "პირველი", "formula", "al jazeera", "trt"]):
                    genre = "News"
                elif any(w in low for w in ["kino", "movie", "film", "кино", "фильм", "series", "fox", "amedia", "murdoch", "gds", "heartland", "schitt"]):
                    genre = "Movies"
                elif any(w in low for w in ["sport", "სპორტ", "спорт", "red bull", "avto", "rybalka", "okhota", "khl", "rugby", "silk"]):
                    genre = "Sports"
                elif any(w in low for w in ["kids", "детский", "karusel", "карусель"]):
                    genre = "Kids"
                elif any(w in low for w in ["music", "музыка", "1hd", "bridge"]):
                    genre = "Music"
                elif any(w in low for w in ["discovery", "animal", "space", "nasa", "ertsulovneba", "explore", "nature", "abaza", "rtdoc"]):
                    genre = "Documentaries"
                else:
                    genre = "Entertainment"

            lang = c.get("language", "English")
            clean_group = "Georgian" if lang == "Georgian" else ("Russian" if lang == "Russian" else "English")

            merged.append({
                "id": cid,
                "name": name,
                "tvg_id": c.get("tvg_id", ""),
                "group": clean_group,
                "language": lang,
                "genre": genre,
                "url": primary_url,
                "stream_type": sources[0].get("type", "hls") if sources else "hls",
                "logo": logo,
                "local_logo": local_logo,
                "sources": sources,
                "source_count": len(sources),
                "primary_res": b_match.get("primary_res", "1080p") if b_match else "1080p",
                "stream_status": "dead" if is_dead else "live",
                "is_alive": not is_dead,
                "notes": c.get("notes", ""),
                "popularity": pop
            })

        # 2. Add extra unique channels from backups
        for b in backups_data:
            bid = b["id"]
            bname = b["name"]
            bname_low = bname.lower().strip()
            if bid in seen_ids or bname_low in seen_names:
                continue
            seen_ids.add(bid)
            seen_names.add(bname_low)

            sources = b.get("sources", [])
            primary_url = sources[0]["url"] if sources else b.get("url", "")
            if not primary_url:
                continue

            local_logo = f"/static/logos/{bid}.png" if (BASE_DIR / "static" / "logos" / f"{bid}.png").exists() else ""
            logo = local_logo or (b.get("logo") if "wikimedia" not in b.get("logo", "") else "") or LOGOS_FALLBACK.get(bid, "")

            lang = b.get("language")
            if not lang:
                if "georgian" in b.get("group", "").lower() or "ge-" in bid:
                    lang = "Georgian"
                elif "russian" in b.get("group", "").lower() or "ru-" in bid:
                    lang = "Russian"
                else:
                    lang = "English"

            clean_group = "Georgian" if lang == "Georgian" else ("Russian" if lang == "Russian" else "English")

            # Genre normalization
            genre = b.get("genre", "General")
            if genre == "General":
                low = bname.lower()
                if any(w in low for w in ["news", "ნიუსი", "новости", "euronews", "bmg", "1tv", "პირველი", "formula", "al jazeera", "trt"]):
                    genre = "News"
                elif any(w in low for w in ["kino", "movie", "film", "кино", "фильм", "series", "fox", "amedia", "murdoch", "gds", "heartland", "schitt"]):
                    genre = "Movies"
                elif any(w in low for w in ["sport", "სპორტ", "спорт", "red bull", "avto", "rybalka", "okhota", "khl", "rugby", "silk"]):
                    genre = "Sports"
                elif any(w in low for w in ["kids", "детский", "karusel", "карусель"]):
                    genre = "Kids"
                elif any(w in low for w in ["music", "музыка", "1hd", "bridge"]):
                    genre = "Music"
                elif any(w in low for w in ["discovery", "animal", "space", "nasa", "ertsulovneba", "explore", "nature", "abaza", "rtdoc"]):
                    genre = "Documentaries"
                else:
                    genre = "Entertainment"

            merged.append({
                "id": bid,
                "name": bname,
                "tvg_id": b.get("tvg_id", ""),
                "group": clean_group,
                "language": lang,
                "genre": genre,
                "url": primary_url,
                "stream_type": sources[0].get("type", "hls") if sources else "hls",
                "logo": logo,
                "local_logo": local_logo,
                "sources": sources,
                "source_count": len(sources),
                "primary_res": b.get("primary_res", "1080p"),
                "stream_status": "live",
                "is_alive": True,
                "notes": b.get("notes", ""),
                "popularity": 70
            })

        if merged:
            self.channels = merged
            logger.info(f"Loaded and merged {len(self.channels)} total IPTV channels with full metadata.")
            self.sync_default_m3u_file()
            return

        default_file = PLAYLISTS_DIR / "default_channels.m3u"
        if default_file.exists():
            try:
                content = default_file.read_text(encoding="utf-8")
                self.channels = self.parse_m3u(content)
                logger.info(f"Loaded {len(self.channels)} default IPTV channels from M3U.")
            except Exception as e:
                logger.error(f"Error loading default playlist: {e}")

    def sync_default_m3u_file(self):
        """Generate/update default_channels.m3u with real logo URLs and metadata."""
        try:
            m3u_file = PLAYLISTS_DIR / "default_channels.m3u"
            lines = ["#EXTM3U\n"]
            for ch in self.channels:
                lines.append(
                    f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
                    f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}" '
                    f'genre="{ch["genre"]}" stream-type="{ch["stream_type"]}" '
                    f'stream-status="{ch["stream_status"]}" popularity="{ch["popularity"]}",{ch["name"]}\n'
                    f'{ch["url"]}\n'
                )
            m3u_file.write_text("".join(lines), encoding="utf-8")
            logger.info("Synchronized default_channels.m3u with real logo URLs.")
        except Exception as e:
            logger.warning(f"Could not sync default_channels.m3u: {e}")

    def get_channels(
        self,
        language: Optional[str] = None,
        genre: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "popularity"  # popularity, name, genre
    ) -> List[Dict[str, Any]]:
        result = self.channels

        # Filter by language
        if language and language != "All":
            result = [c for c in result if c.get("language", "").lower() == language.lower()]

        # Filter by genre
        if genre and genre != "All":
            result = [c for c in result if c.get("genre", "").lower() == genre.lower()]

        # Filter by search
        if search:
            q = search.lower()
            result = [
                c for c in result 
                if q in c.get("name", "").lower() 
                or q in c.get("genre", "").lower()
                or q in c.get("language", "").lower()
            ]

        # Sorting
        if sort_by == "popularity":
            result = sorted(result, key=lambda x: x.get("popularity", 50), reverse=True)
        elif sort_by == "least_popular":
            result = sorted(result, key=lambda x: x.get("popularity", 50))
        elif sort_by == "name":
            result = sorted(result, key=lambda x: x.get("name", "").lower())
        elif sort_by == "genre":
            result = sorted(result, key=lambda x: (x.get("genre", ""), -x.get("popularity", 50)))

        return result

    def get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        for ch in self.channels:
            if ch.get("id") == channel_id:
                return ch
        return None

    def add_channel(self, name: str, url: str, group: str = "Custom", logo: str = "", language: str = "English", genre: str = "General") -> Dict[str, Any]:
        ch = {
            "id": f"custom_{len(self.channels)+1}",
            "name": name,
            "url": url,
            "sources": [{"url": url, "type": "hls", "max_res": "1080p", "headers": {}}],
            "source_count": 1,
            "group": group or "Custom",
            "language": language,
            "genre": genre,
            "popularity": 75,
            "logo": logo,
            "stream_status": "live",
            "is_alive": True
        }
        self.channels.insert(0, ch)
        return ch

iptv_manager = IPTVManager()
