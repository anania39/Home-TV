import os
import re
import time
import json
import logging
import urllib.request
from typing import Set, Dict, List, Optional

logger = logging.getLogger("blocklist_manager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKLIST_DIR = os.path.join(BASE_DIR, "data", "blocklists")
COMPILED_FILE = os.path.join(BLOCKLIST_DIR, "compiled_blocklist.txt")
META_FILE = os.path.join(BLOCKLIST_DIR, "blocklists_meta.json")

SOURCES = [
    {
        "id": "adguard_dns",
        "name": "AdGuard Official DNS Filter",
        "url": "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
        "category": "AdGuard Core DNS Filter",
        "format": "adblock"
    },
    {
        "id": "easyprivacy",
        "name": "EasyPrivacy Tracker & Ad Filter",
        "url": "https://v.firebog.net/hosts/Easyprivacy.txt",
        "category": "Telemetry & Web Trackers",
        "format": "domains"
    },
    {
        "id": "prigent_ads",
        "name": "Prigent Video & Web Ads",
        "url": "https://v.firebog.net/hosts/Prigent-Ads.txt",
        "category": "Video & Popup Ads",
        "format": "domains"
    },
    {
        "id": "stevenblack",
        "name": "StevenBlack Unified (Pi-hole Standard)",
        "url": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "category": "General Ads & Trackers",
        "format": "hosts"
    },
    {
        "id": "anudeep",
        "name": "Anudeep Adservers (Pi-hole Curated)",
        "url": "https://raw.githubusercontent.com/anudeepND/blacklist/master/adservers.txt",
        "category": "Ad Servers & Telemetry",
        "format": "domains"
    },
    {
        "id": "youtube_ads",
        "name": "YouTube Ads & Telemetry (Pi-hole Community)",
        "url": "https://raw.githubusercontent.com/kboghdady/youTube_ads_4_pi-hole/master/youtubelist.txt",
        "category": "YouTube Manifests & Ads",
        "format": "domains"
    },
    {
        "id": "peter_lowe",
        "name": "Peter Lowe Ad & Tracking Server List",
        "url": "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=nohtml&showintro=0&mimetype=plaintext",
        "category": "Adservers & Trackers",
        "format": "domains"
    },
    {
        "id": "adguard_mobile",
        "name": "AdGuard Mobile In-App Filter",
        "url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/MobileFilter/sections/adservers.txt",
        "category": "Mobile In-App Ads",
        "format": "adblock"
    }
]

class BlocklistManager:
    def __init__(self):
        os.makedirs(BLOCKLIST_DIR, exist_ok=True)
        self.blocked_domains: Set[str] = set()
        self.meta: Dict = {
            "total_domains": 0,
            "last_updated": 0,
            "sources": []
        }
        self.load()

    def load(self):
        """Loads compiled blocklist from disk into memory."""
        if os.path.exists(COMPILED_FILE):
            try:
                t0 = time.time()
                with open(COMPILED_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    self.blocked_domains = {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}
                logger.info(f"Loaded {len(self.blocked_domains):,} ad domains from local blocklist cache in {time.time()-t0:.2f}s")
                if os.path.exists(META_FILE):
                    with open(META_FILE, "r", encoding="utf-8") as f:
                        self.meta = json.load(f)
                return
            except Exception as e:
                logger.error(f"Error loading compiled blocklist: {e}")

        # If compiled file doesn't exist yet, download and compile
        self.update_sources()

    def parse_content(self, content: str, fmt: str) -> Set[str]:
        domains = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue

            if fmt == "hosts":
                parts = line.split()
                if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                    d = parts[1].strip().lower().strip(".")
                    if d and d not in ("localhost", "broadcasthost", "local"):
                        domains.add(d)
            elif fmt == "domains":
                d = line.split()[0].strip().lower().strip(".")
                if d and "." in d and not d.startswith("127.0."):
                    domains.add(d)
            elif fmt == "adblock":
                # Adblock format e.g. ||example.com^
                m = re.search(r"\|\|([a-zA-Z0-9\.\-_]+)\^", line)
                if m:
                    domains.add(m.group(1).lower().strip("."))
                elif "." in line and not any(c in line for c in ("/", "*", "$", "@")):
                    domains.add(line.lower().strip("."))
        return domains

    def update_sources(self) -> Dict:
        """Downloads all community repositories and compiles into a single fast lookup set."""
        all_domains: Set[str] = set()
        sources_meta = []

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TVHub-DNS/2.0"}

        for src in SOURCES:
            src_info = {
                "id": src["id"],
                "name": src["name"],
                "category": src["category"],
                "url": src["url"],
                "domains_count": 0,
                "status": "pending"
            }
            try:
                logger.info(f"Downloading {src['name']} from {src['url']}...")
                req = urllib.request.Request(src["url"], headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    raw_data = resp.read().decode("utf-8", errors="ignore")
                    domains = self.parse_content(raw_data, src["format"])
                    src_info["domains_count"] = len(domains)
                    src_info["status"] = "ok"
                    all_domains.update(domains)
                    logger.info(f"✓ {src['name']}: {len(domains):,} domains parsed")
            except Exception as e:
                logger.warning(f"Failed to fetch {src['name']}: {e}")
                src_info["status"] = f"error: {str(e)[:50]}"

            sources_meta.append(src_info)

        if all_domains:
            self.blocked_domains = all_domains
            # Write to compiled file
            try:
                with open(COMPILED_FILE, "w", encoding="utf-8") as f:
                    for d in sorted(all_domains):
                        f.write(d + "\n")
                
                self.meta = {
                    "total_domains": len(all_domains),
                    "last_updated": int(time.time()),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "sources": sources_meta
                }
                with open(META_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.meta, f, indent=2)
                logger.info(f"Compiled total {len(all_domains):,} unique ad-blocking domains to {COMPILED_FILE}")
            except Exception as e:
                logger.error(f"Error saving compiled blocklist: {e}")

        return self.meta

blocklist_manager = BlocklistManager()

if __name__ == "__main__":
    bm = BlocklistManager()
    bm.update_sources()
    print("FINISHED COMPILE:", bm.meta["total_domains"])
