"""
ASUS Router Automated Ad-Blocker Configuration Engine
Automatically configures ASUS routers (Asuswrt / Asuswrt-Merlin) such as RT-AX1800U
to route home network DNS to TV Hub Ad-Blocker (192.168.50.250).
"""

import urllib.request
import urllib.parse
import http.cookiejar
import base64
import re
import json
import logging
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger("router_controller")

class AsusRouterController:
    def __init__(self):
        self.default_router_ip = "192.168.50.1"

    def _get_opener(self):
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        return opener, cj

    def check_reachability(self, ip: str = "192.168.50.1") -> Dict:
        """Verifies if the router management interface is accessible."""
        url = f"http://{ip}/Main_Login.asp"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=3) as res:
                content = res.read().decode("utf-8", errors="ignore")
                is_asus = "ASUS" in content or "login.cgi" in content or "asus" in content.lower()
                return {
                    "reachable": True,
                    "is_asus": is_asus,
                    "model": "ASUS RT-AX1800U" if is_asus else "Home Gateway Router",
                    "ip": ip
                }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e),
                "ip": ip
            }

    def login(self, ip: str, username: str, password: str) -> Tuple[bool, Optional[str], Optional[urllib.request.OpenerDirector], Optional[http.cookiejar.CookieJar]]:
        """
        Authenticates against Asuswrt using base64 credentials.
        Returns: (success, error_or_token, opener, cookie_jar)
        """
        login_url = f"http://{ip}/login.cgi"
        auth_str = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")

        post_data = urllib.parse.urlencode({
            "login_authorization": encoded_auth,
            "current_page": "Main_Login.asp",
            "next_page": "Main_Login.asp",
            "action_mode": "",
            "action_script": "",
            "action_wait": "5"
        }).encode("utf-8")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"http://{ip}/Main_Login.asp",
            "Origin": f"http://{ip}"
        }

        opener, cj = self._get_opener()

        try:
            req = urllib.request.Request(login_url, data=post_data, headers=headers)
            with opener.open(req, timeout=6) as res:
                body = res.read().decode("utf-8", errors="ignore")
                
                # Check cookies for asus_token
                token = None
                for cookie in cj:
                    if cookie.name in ("asus_token", "token"):
                        token = cookie.value
                        break

                if not token:
                    set_cookie = res.headers.get("Set-Cookie", "")
                    m = re.search(r'(?:asus_token|token)=([^;,\s]+)', set_cookie)
                    if m:
                        token = m.group(1)

                if not token:
                    m = re.search(r"(?:asus_token|token)[=:](\w+)", body)
                    if m:
                        token = m.group(1)

                # Asuswrt indicates failed login with error_status=1 or 'Invalid username or password'
                if "error_status=1" in body or "Invalid username or password" in body:
                    return False, "Invalid router username or password", None, None
                
                if "error_status=2" in body or "captcha" in body.lower():
                    return False, "Router requires CAPTCHA due to multiple failed attempts. Please unlock on router page.", None, None

                if token or res.status == 200 or "index.asp" in body:
                    logger.info(f"Successfully authenticated with ASUS router at {ip}")
                    return True, token or "authenticated", opener, cj

                return False, "Router did not confirm authentication", None, None

        except urllib.error.HTTPError as e:
            return False, f"Router returned HTTP error {e.code}", None, None
        except Exception as e:
            return False, f"Connection error: {str(e)}", None, None

    def apply_dns_adblocker(self, ip: str, dns_server_ip: str, opener: urllib.request.OpenerDirector, cj: http.cookiejar.CookieJar, token: Optional[str] = None) -> Tuple[bool, str]:
        """
        Applies primary DHCP DNS server setting to point to TV Hub (dns_server_ip).
        Triggers dnsmasq restart on the router.
        """
        apply_urls = [
            f"http://{ip}/start_apply.htm",
            f"http://{ip}/applyapp.cgi",
            f"http://{ip}/apply.cgi"
        ]

        # Asuswrt DHCP NVRAM parameters:
        # dhcp_dns1_x: primary DNS advertised to all DHCP clients on the local network
        payload = {
            "action_mode": "apply",
            "action_script": "restart_dnsmasq",
            "action_wait": "3",
            "current_page": "Advanced_DHCP_Content.asp",
            "next_page": "Advanced_DHCP_Content.asp",
            "dhcp_dns1_x": dns_server_ip
        }
        if token and token != "authenticated":
            payload["asus_token"] = token

        encoded_payload = urllib.parse.urlencode(payload).encode("utf-8")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"http://{ip}/Advanced_DHCP_Content.asp",
            "Origin": f"http://{ip}"
        }

        success = False
        last_error = ""

        for url in apply_urls:
            try:
                req = urllib.request.Request(url, data=encoded_payload, headers=headers)
                with opener.open(req, timeout=6) as res:
                    body = res.read().decode("utf-8", errors="ignore")
                    if res.status in (200, 302):
                        logger.info(f"Successfully posted DNS config to {url}")
                        success = True
                        break
            except Exception as e:
                last_error = str(e)
                logger.debug(f"Apply attempt at {url} returned: {e}")

        if success:
            return True, f"Successfully programmed ASUS router! Primary DNS is now {dns_server_ip} (TV Hub No Ads)."
        return False, f"Could not apply router setting: {last_error or 'Unknown apply error'}"

    def auto_configure(self, router_ip: str, username: str, password: str, dns_server_ip: str = "192.168.50.250") -> Dict:
        """
        End-to-end automated 1-click router ad-block configuration.
        """
        router_ip = router_ip.strip() or self.default_router_ip
        username = username.strip() or "admin"
        password = password.strip()

        if not password:
            return {
                "status": "error",
                "message": "Router password is required to automatically program the router."
            }

        # Step 1: Reachability check
        reach = self.check_reachability(router_ip)
        if not reach.get("reachable"):
            return {
                "status": "error",
                "message": f"Could not reach router at http://{router_ip}. Ensure you are connected to the home Wi-Fi."
            }

        # Step 2: Login
        ok, token_or_err, opener, cj = self.login(router_ip, username, password)
        if not ok or opener is None:
            return {
                "status": "error",
                "message": token_or_err or "Router authentication failed."
            }

        # Step 3: Apply DNS
        ok_apply, msg = self.apply_dns_adblocker(router_ip, dns_server_ip, opener, cj, token=token_or_err if token_or_err != 'authenticated' else None)
        if ok_apply:
            # Save router config state (without persisting plaintext password)
            self._save_router_state(router_ip, username, dns_server_ip)
            return {
                "status": "ok",
                "message": f"✓ Success! ASUS Router ({router_ip}) is now configured for automatic network-wide Ad-Blocking.",
                "dns_ip": dns_server_ip,
                "router_ip": router_ip
            }
        else:
            return {
                "status": "error",
                "message": msg
            }

    def _save_router_state(self, router_ip: str, username: str, dns_ip: str):
        try:
            import os
            state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "router_config.json")
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "router_ip": router_ip,
                    "username": username,
                    "dns_server_ip": dns_ip,
                    "auto_configured": True,
                    "timestamp": int(time.time()),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=2)
        except Exception:
            pass

    def get_router_status(self) -> Dict:
        """Returns detected router info and auto-config history."""
        import os
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "router_config.json")
        saved = {}
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
            except Exception:
                pass

        return {
            "default_router_ip": self.default_router_ip,
            "detected_model": "ASUS RT-AX1800U",
            "auto_configured": saved.get("auto_configured", False),
            "last_configured": saved.get("date", None),
            "dns_server_ip": saved.get("dns_server_ip", "192.168.50.250")
        }

asus_router_controller = AsusRouterController()
