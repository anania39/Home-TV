import asyncio
import socket
import struct
import time
import json
import os
import logging
from typing import Dict, List, Optional, Tuple, Set

logger = logging.getLogger("adblocker")

# Curated High-Impact Ad, Tracking, YouTube & Smart TV Ad Domains
AD_DOMAINS = {
    # YouTube & Google Video Ads & Telemetry
    "googleads.g.doubleclick.net", "pubads.g.doubleclick.net", "securepubads.g.doubleclick.net",
    "ad.youtube.com", "ads.youtube.com", "s.youtube.com", "video-stats.l.google.com",
    "youtube-ui.l.google.com", "yt3.ggpht.com", "ep1.adtrafficquality.google",
    "ep2.adtrafficquality.google", "adtrafficquality.google", "fundingchoicesmessages.google.com",
    "pagead.l.google.com", "partnerad.l.google.com", "pagead-googlehosted.l.google.com",
    "afs.googlesyndication.com", "2mdn.net", "invitemedia.com", "admeld.com",
    
    # DoH Bypass Prevention (forces browsers to use local port 53)
    "dns.google", "dns.google.com", "cloudflare-dns.com", "dns.quad9.net", "doh.opendns.com",

    # General Ad Networks & Tracking
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "adservice.google.com", "pagead2.googlesyndication.com", "adclick.g.doubleclick.net",
    "adnxs.com", "criteo.com", "criteo.net", "scorecardresearch.com",
    "outbrain.com", "taboola.com", "advertising.com", "adroll.com",
    "rubiconproject.com", "pubmatic.com", "openx.net", "casalemedia.com",
    "moatads.com", "quantserve.com", "adcolony.com", "applovin.com",
    "unityads.unity3d.com", "vungle.com", "inmobi.com", "chartboost.com",
    "serving-sys.com", "smartadserver.com", "spotxchange.com",
    "yandex.ru/ads", "an.yandex.ru", "ad.mail.ru", "target.my.com",
    "aax.amazon-adsystem.com", "c.amazon-adsystem.com", "s.amazon-adsystem.com",
    "bidswitch.net", "mgid.com", "popcash.net", "popads.net", "propellerads.com",
    
    # Smart TV Ad & Telemetry Domains (Hisense VIDAA, Xiaomi, TCL, Samsung, LG)
    "ads.hisense.com", "log.hisense.com", "tracking.hisense.com", "vidaahub.hisense.com",
    "ad.xiaomi.com", "tracking.miui.com", "data.mistat.xiaomi.com", "adv.sec.miui.com",
    "tclclouds.com", "log.tclclouds.com", "ads.tcl.com", "browser.tclclouds.com",
    "samsungads.com", "config.samsungads.com", "gpm.samsungqbe.com", "log-config.samsung.com",
    "lgsmartad.com", "ibis.lgappstv.com", "ad.lgappstv.com", "rdx.lgtvcommon.com",
    
    # Video & Stream Video Ad Injections
    "adserver.adtechus.com", "adserver.yahoo.com", "video-ads.com",
    "delivery.vidible.tv", "ads.stickyadstv.com", "innovid.com", "tremorhub.com",
    
    # Web & Mobile Trackers
    "google-analytics.com", "analytics.google.com", "hotjar.com", "mixpanel.com",
    "segment.io", "amplitude.com", "branch.io", "appsflyer.com", "adjust.com"
}

# Substring / pattern matches for ad domains
AD_KEYWORDS = [
    "googleads", "pagead", "doubleclick", "adservice", "adsystem",
    "adnxs", "popads", "popcash", "propellerads", "adserver",
    "adclick", "adform", "smartad", "adtech", "serving-sys",
    "adtrafficquality", "youtube-ads"
]

class DNSAdBlocker:
    def __init__(self, state_file: str = "data/adblock_state.json"):
        self.state_file = state_file
        self.global_enabled = True
        self.device_rules: Dict[str, bool] = {} # ip -> bool
        self.stats = {
            "queries_total": 0,
            "ads_blocked": 0,
            "start_time": time.time()
        }
        self.recent_blocks: List[Dict] = []
        self._upstream_primary = ("94.140.14.14", 53)    # AdGuard Clean DNS
        self._upstream_secondary = ("94.140.15.15", 53)  # AdGuard Clean DNS Secondary
        self._upstream_neutral = ("1.1.1.1", 53)         # Cloudflare Neutral DNS
        self._cache: Dict[Tuple[str, int], Tuple[bytes, float]] = {} # (qname, qtype) -> (resp, expires_at)
        self._udp_transport = None
        self._tcp_server = None
        self._running = False
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.global_enabled = data.get("global_enabled", True)
                    self.device_rules = data.get("device_rules", {})
                    loaded_stats = data.get("stats", {})
                    self.stats["queries_total"] = loaded_stats.get("queries_total", 0)
                    self.stats["ads_blocked"] = loaded_stats.get("ads_blocked", 0)
        except Exception as e:
            logger.debug(f"Adblocker state load notice: {e}")

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "global_enabled": self.global_enabled,
                    "device_rules": self.device_rules,
                    "stats": self.stats,
                    "updated_at": int(time.time())
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Adblocker state save error: {e}")

    def is_ad_domain(self, domain: str) -> bool:
        domain = domain.lower().strip(".")
        if domain in AD_DOMAINS:
            return True
        parts = domain.split(".")
        # Check subdomains (e.g. ad.doubleclick.net -> doubleclick.net)
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in AD_DOMAINS:
                return True
        for kw in AD_KEYWORDS:
            if kw in domain:
                return True
        return False

    def is_blocking_enabled_for_ip(self, client_ip: str) -> bool:
        if client_ip in self.device_rules:
            return self.device_rules[client_ip]
        return self.global_enabled

    def set_global_enabled(self, enabled: bool):
        self.global_enabled = enabled
        self.save_state()

    def set_device_enabled(self, ip: str, enabled: bool):
        self.device_rules[ip] = enabled
        self.save_state()

    def get_status(self) -> Dict:
        block_pct = 0
        if self.stats["queries_total"] > 0:
            block_pct = round((self.stats["ads_blocked"] / self.stats["queries_total"]) * 100, 1)
        return {
            "global_enabled": self.global_enabled,
            "running": self._running,
            "port": 53,
            "listen_ip": "192.168.50.250",
            "stats": {
                "queries_total": self.stats["queries_total"],
                "ads_blocked": self.stats["ads_blocked"],
                "block_rate_percent": block_pct,
                "uptime_seconds": int(time.time() - self.stats["start_time"])
            },
            "device_rules": self.device_rules,
            "recent_blocks": self.recent_blocks[-25:]
        }

    def _parse_qname(self, data: bytes, offset: int = 12) -> Tuple[str, int, int]:
        labels = []
        curr = offset
        while curr < len(data):
            length = data[curr]
            if length == 0:
                curr += 1
                break
            curr += 1
            labels.append(data[curr:curr+length].decode("ascii", errors="ignore"))
            curr += length
        qname = ".".join(labels).lower()
        qtype = 1
        if curr + 2 <= len(data):
            qtype = struct.unpack("!H", data[curr:curr+2])[0]
        return qname, qtype, curr + 4

    def _build_nxdomain_response(self, req_data: bytes) -> bytes:
        """Returns standard NXDOMAIN (Name Error) response for DoH canary."""
        txid = req_data[:2]
        flags = b"\x81\x83" # Standard response, NXDOMAIN
        counts = b"\x00\x01\x00\x00\x00\x00\x00\x00"
        _, _, end_offset = self._parse_qname(req_data, 12)
        question = req_data[12:end_offset]
        return txid + flags + counts + question

    def _build_sinkhole_response(self, req_data: bytes, qname: str, qtype: int) -> bytes:
        txid = req_data[:2]
        flags = b"\x81\x80" # Standard query response, No error
        counts = b"\x00\x01\x00\x01\x00\x00\x00\x00"
        _, _, end_offset = self._parse_qname(req_data, 12)
        question = req_data[12:end_offset]
        ans_name = b"\xc0\x0c"
        ttl = struct.pack("!I", 300)
        
        if qtype == 28: # AAAA
            ans_type = b"\x00\x1c\x00\x01"
            rdata = b"\x00" * 16
            rdlen = struct.pack("!H", 16)
        else: # Type A
            ans_type = b"\x00\x01\x00\x01"
            rdata = b"\x00\x00\x00\x00"
            rdlen = struct.pack("!H", 4)
            
        answer = ans_name + ans_type + ttl + rdlen + rdata
        return txid + flags + counts + question + answer

    async def handle_query(self, data: bytes, client_ip: str) -> Optional[bytes]:
        if len(data) < 12:
            return None
        self.stats["queries_total"] += 1
        
        try:
            qname, qtype, _ = self._parse_qname(data, 12)
        except Exception:
            qname, qtype = "unknown", 1

        is_blocked_device = self.is_blocking_enabled_for_ip(client_ip)

        # DoH Canary domain check: forces Chrome & Firefox to disable DoH and use system DNS
        if qname == "use-application-dns.net":
            logger.info(f"[DoH CANARY] {client_ip} -> returning NXDOMAIN to enforce local DNS")
            return self._build_nxdomain_response(data)

        # 1. Check if domain is blocked for this device
        if is_blocked_device and self.is_ad_domain(qname):
            self.stats["ads_blocked"] += 1
            block_entry = {
                "domain": qname,
                "client_ip": client_ip,
                "time": time.strftime("%H:%M:%S"),
                "timestamp": time.time()
            }
            self.recent_blocks.append(block_entry)
            if len(self.recent_blocks) > 100:
                self.recent_blocks.pop(0)
            logger.info(f"[AD BLOCKED] {client_ip} -> {qname}")
            return self._build_sinkhole_response(data, qname, qtype)

        # 2. Check local RAM cache for non-ad queries
        now = time.time()
        cache_key = (qname, qtype)
        if cache_key in self._cache:
            resp, exp = self._cache[cache_key]
            if now < exp:
                # Update transaction ID to match current request
                return data[:2] + resp[2:]

        # 3. Forward to Upstream DNS
        upstream = self._upstream_primary if is_blocked_device else self._upstream_neutral
        try:
            loop = asyncio.get_running_loop()
            resp = await self._forward_upstream(data, upstream)
            if resp:
                # Cache response for 60 seconds
                self._cache[cache_key] = (resp, now + 60.0)
                if len(self._cache) > 2000:
                    self._cache.clear()
                return resp
        except Exception as e:
            logger.debug(f"Upstream DNS notice for {qname}: {e}")
            # Try secondary upstream
            try:
                resp = await self._forward_upstream(data, self._upstream_secondary)
                if resp:
                    return resp
            except Exception:
                pass

        return None

    async def _forward_upstream(self, data: bytes, target_server: Tuple[str, int]) -> bytes:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        
        class UpstreamProtocol(asyncio.DatagramProtocol):
            def __init__(self, fut):
                self.fut = fut
            def datagram_received(self, data, addr):
                if not self.fut.done():
                    self.fut.set_result(data)
            def error_received(self, exc):
                if not self.fut.done():
                    self.fut.set_exception(exc)

        transport, _ = await loop.create_datagram_endpoint(
            lambda: UpstreamProtocol(future),
            remote_addr=target_server
        )
        try:
            transport.sendto(data)
            resp = await asyncio.wait_for(future, timeout=2.0)
            return resp
        finally:
            transport.close()

    async def start(self, host: str = "0.0.0.0", port: int = 53):
        if self._running:
            return
        loop = asyncio.get_running_loop()
        adblocker_ref = self

        class DNSUDPProtocol(asyncio.DatagramProtocol):
            def connection_made(self, transport):
                self.transport = transport

            def datagram_received(self, data, addr):
                asyncio.create_task(self.process(data, addr))

            async def process(self, data, addr):
                try:
                    resp = await adblocker_ref.handle_query(data, addr[0])
                    if resp and self.transport:
                        self.transport.sendto(resp, addr)
                except Exception as e:
                    logger.debug(f"DNS UDP process error: {e}")

        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda: DNSUDPProtocol(),
                local_addr=(host, port)
            )
            self._udp_transport = transport
            self._running = True
            logger.info(f"Enterprise DNS Ad-Blocker active on {host}:{port} (UDP)")
        except Exception as e:
            logger.warning(f"Could not bind DNS port {port}: {e}")

    def stop(self):
        if self._udp_transport:
            self._udp_transport.close()
            self._udp_transport = None
        self._running = False
        logger.info("DNS Ad-Blocker stopped.")

dns_adblocker = DNSAdBlocker()
