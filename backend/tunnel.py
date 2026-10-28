import sys
import time
import subprocess
import threading
import re
import logging
import json
import urllib.request
import urllib.parse
import os
import base64
from pathlib import Path
from .config import BASE_DIR, PORT, SERVER_IP

logger = logging.getLogger("tunnel")

CACHE_FILE = BASE_DIR / "backend" / ".tunnel_cache.json"

def get_github_token() -> str:
    """Read GitHub fine-grained token from env or local .github_token file."""
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if tok:
        return tok
    token_file = BASE_DIR / ".github_token"
    if token_file.exists():
        try:
            return token_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""

GITHUB_REPO = "anania39/Home-TV"

def ensure_cloudflared_binary(binary_path: Path) -> bool:
    """Ensure cloudflared binary is present, downloading from official release if missing."""
    if binary_path.exists() and binary_path.stat().st_size > 5000000:
        return True
    try:
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        logger.info(f"Downloading official cloudflared binary to {binary_path}...")
        urllib.request.urlretrieve(url, str(binary_path))
        return binary_path.exists()
    except Exception as e:
        logger.warning(f"Could not auto-download cloudflared: {e}")
        return False

def publish_endpoint(public_url: str):
    """Publish current tunnel and local endpoint to endpoint.json locally and sync to GitHub."""
    data = {
        "hub_url": public_url,
        "local_url": f"http://{SERVER_IP}:{PORT}",
        "local_ip": SERVER_IP,
        "port": PORT,
        "github_pages_url": "https://anania39.github.io/Home-TV/",
        "status": "online",
        "updated_at": int(time.time()),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # 1. Update local endpoint.json
    endpoint_file = BASE_DIR / "endpoint.json"
    try:
        endpoint_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug(f"Failed to write local endpoint.json: {e}")

    # 2. Async GitHub API sync
    def _sync():
        token = get_github_token()
        if not token:
            logger.debug("No GitHub token configured for endpoint sync.")
            return
        try:
            content_bytes = json.dumps(data, indent=2).encode("utf-8")
            b64_content = base64.b64encode(content_bytes).decode("ascii")

            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/endpoint.json"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "TVHub-AutoSync"
            }

            # Check existing sha
            req = urllib.request.Request(api_url, headers=headers)
            sha = None
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    sha = resp_data.get("sha")
            except Exception:
                pass

            payload = {
                "message": "chore: sync active TV Hub endpoint",
                "content": b64_content
            }
            if sha:
                payload["sha"] = sha

            put_req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"},
                method="PUT"
            )
            with urllib.request.urlopen(put_req, timeout=8) as resp:
                logger.info(f"🌐 Active Hub Endpoint Synced to GitHub: {public_url}")
        except Exception as err:
            logger.debug(f"GitHub endpoint sync notice: {err}")

    threading.Thread(target=_sync, daemon=True).start()

def is_pid_running(pid: int) -> bool:
    """Check if process with given PID is alive on Windows."""
    try:
        res = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return "cloudflared" in res.stdout.lower()
    except Exception:
        return False

def make_short_url(long_url: str) -> str:
    """Generate a clean, static, memorable short URL for the public link."""
    try:
        api_url = f"https://clck.ru/--?url={urllib.parse.quote(long_url)}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            short = resp.read().decode("utf-8").strip()
            if short.startswith("http"):
                return short
    except Exception as e:
        logger.debug(f"Short link service fallback: {e}")
    return long_url

class PublicTunnelManager:
    def __init__(self):
        self.proc: subprocess.Popen | None = None
        self.public_url: str | None = None
        self.short_url: str | None = None
        self._lock = threading.Lock()
        self.binary_path = BASE_DIR / "tools" / "cloudflared.exe"

    def start(self):
        # 1. First, check if an existing persistent tunnel is already running from previous iteration
        if CACHE_FILE.exists():
            try:
                data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                cached_pid = data.get("pid")
                cached_url = data.get("public_url")
                cached_short = data.get("short_url")

                if cached_pid and is_pid_running(cached_pid) and cached_url:
                    with self._lock:
                        self.public_url = cached_url
                        self.short_url = cached_short or cached_url
                    logger.info("=" * 65)
                    logger.info(f"🌐 REUSING PERSISTENT STATIC TUNNEL (PID {cached_pid})")
                    logger.info(f"   * Clean Short Link: {self.short_url}")
                    logger.info(f"   * Direct Link:     {self.public_url}")
                    logger.info("=" * 65)
                    publish_endpoint(self.public_url)
                    return self
            except Exception as e:
                logger.debug(f"Cache check notice: {e}")

        if not ensure_cloudflared_binary(self.binary_path):
            logger.warning(f"cloudflared.exe unavailable at {self.binary_path}")
            return None

        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        return self

    def _run(self):
        while True:
            try:
                logger.info("Initializing high-availability public tunnel...")
                flags = 0
                if sys.platform == "win32":
                    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                self.proc = subprocess.Popen(
                    [str(self.binary_path), "tunnel", "--protocol", "http2", "--url", f"http://127.0.0.1:{PORT}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=flags
                )

                found_url = False
                while self.proc and self.proc.poll() is None:
                    line = self.proc.stderr.readline()
                    if not line:
                        continue
                    match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                    if match and not found_url:
                        found_url = True
                        direct_url = match.group(1)
                        short_link = make_short_url(direct_url)
                        with self._lock:
                            self.public_url = direct_url
                            self.short_url = short_link

                        # Persist across future server reloads so the URL NEVER changes!
                        try:
                            CACHE_FILE.write_text(json.dumps({
                                "pid": self.proc.pid,
                                "public_url": self.public_url,
                                "short_url": self.short_url
                            }, indent=2), encoding="utf-8")
                        except Exception:
                            pass

                        logger.info("=" * 65)
                        logger.info(f"🌐 PUBLIC PHONE LINK READY (STATIC ACROSS ITERATIONS)")
                        logger.info(f"   * Clean Short Link: {self.short_url}")
                        logger.info(f"   * Direct Link:     {self.public_url}")
                        logger.info("=" * 65)

                        publish_endpoint(self.public_url)

                logger.warning("Public tunnel process exited. Auto-reconnecting in 3 seconds...")
                time.sleep(3)
            except Exception as e:
                logger.error(f"Error in tunnel loop: {e}")
                time.sleep(5)

    def get_url(self) -> str | None:
        with self._lock:
            return self.public_url

    def get_short_url(self) -> str | None:
        with self._lock:
            return self.short_url or self.public_url

    def stop(self, kill_process: bool = False):
        """Keep the background tunnel alive across server reloads for permanent static URL."""
        if kill_process and self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None
            if CACHE_FILE.exists():
                try:
                    CACHE_FILE.unlink()
                except Exception:
                    pass

tunnel_manager = PublicTunnelManager()
