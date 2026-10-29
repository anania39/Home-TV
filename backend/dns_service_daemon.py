"""
Enterprise DNS Ad-Blocker - 24/7 Persistent Windows Background Daemon
Runs independently of the TV Hub web UI / terminal window on port 53 (UDP).
Survives application closures and automatically reloads configuration from data/adblock_state.json.
"""

import os, sys
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test_entry.log"), "a") as _f:
        _f.write(f"loaded at {os.getpid()} with {sys.executable}\n")
except Exception:
    pass

import asyncio
import time
import json
import logging
import signal

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.dns_adblocker import DNSAdBlocker

# Setup file logging for daemon
LOG_FILE = os.path.join(BASE_DIR, "data", "dns_daemon.log")
PID_FILE = os.path.join(BASE_DIR, "data", "dns_adblocker.pid")
STATE_FILE = os.path.join(BASE_DIR, "data", "adblock_state.json")

os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# Safe logging configuration for both console and pythonw.exe (headless)
handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=handlers
)
logger = logging.getLogger("dns_daemon")

class PersistentDNSDaemon:
    def __init__(self):
        self.adblocker = DNSAdBlocker(state_file=STATE_FILE)
        self.last_mtime = 0
        self.running = True

    def write_pid(self):
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
            logger.info(f"PID {os.getpid()} written to {PID_FILE}")
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")

    def cleanup_pid(self):
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass

    def check_and_reload_state(self):
        if not os.path.exists(STATE_FILE):
            return
        try:
            mtime = os.path.getmtime(STATE_FILE)
            if mtime > self.last_mtime:
                self.last_mtime = mtime
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    new_global = data.get("global_enabled", True)
                    new_rules = data.get("device_rules", {})
                    
                    if new_global != self.adblocker.global_enabled or new_rules != self.adblocker.device_rules:
                        self.adblocker.global_enabled = new_global
                        self.adblocker.device_rules = new_rules
                        logger.info(f"Updated rules from state file: Global No-Ads={new_global}, Device Rules={len(new_rules)}")

                    loaded_stats = data.get("stats", {})
                    if loaded_stats.get("reset_trigger") or (loaded_stats.get("queries_total", 0) == 0 and self.adblocker.stats.get("queries_total", 0) > 0):
                        self.adblocker.stats["queries_total"] = 0
                        self.adblocker.stats["ads_blocked"] = 0
                        self.adblocker.stats["start_time"] = time.time()
                        self.adblocker.recent_blocks.clear()
                        logger.info("Reset query statistics and counters in daemon memory")
        except Exception as e:
            logger.debug(f"State check notice: {e}")

    def flush_stats_to_disk(self):
        try:
            current_state = {}
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        current_state = json.load(f)
                except Exception:
                    pass
            
            current_state["global_enabled"] = self.adblocker.global_enabled
            current_state["device_rules"] = self.adblocker.device_rules
            current_state["stats"] = self.adblocker.stats
            current_state["recent_blocks"] = self.adblocker.recent_blocks[-25:]
            current_state["daemon_pid"] = os.getpid()
            current_state["daemon_alive"] = True
            current_state["updated_at"] = int(time.time())

            tmp_path = STATE_FILE + f".tmp.{os.getpid()}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(current_state, f, indent=2)
            os.replace(tmp_path, STATE_FILE)
            self.last_mtime = os.path.getmtime(STATE_FILE)
        except Exception as e:
            logger.debug(f"Stats flush notice: {e}")

    async def sync_loop(self):
        last_flush = time.time()
        while self.running:
            self.check_and_reload_state()
            now = time.time()
            if now - last_flush >= 3.0:
                self.flush_stats_to_disk()
                last_flush = now
            await asyncio.sleep(1.0)

    async def run(self):
        self.write_pid()
        logger.info("=" * 60)
        logger.info("[STARTUP] TV Hub Persistent DNS Ad-Blocker Daemon Starting...")
        logger.info(f"Target: Port 53 UDP on 0.0.0.0 (Persistent Background Service)")
        logger.info("=" * 60)

        # Start DNS adblocker engine on port 53
        await self.adblocker.start(host="0.0.0.0", port=53)

        # Run background sync loop
        sync_task = asyncio.create_task(self.sync_loop())

        try:
            while self.running:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        finally:
            sync_task.cancel()
            self.adblocker.stop()
            self.cleanup_pid()
            logger.info("DNS Ad-Blocker Daemon stopped gracefully.")

def main():
    daemon = PersistentDNSDaemon()

    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}, terminating daemon...")
        daemon.running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(daemon.run())
    except Exception as e:
        logger.error(f"Daemon fatal error: {e}", exc_info=True)
    finally:
        daemon.cleanup_pid()

if __name__ == "__main__":
    main()
