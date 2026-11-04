# 1. Patch static/app.js
with open('static/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

old_fn = '''function makeCastPlayableUrl(rawUrl) {
  if (!rawUrl) return "";
  const cloudHost = "https://tvhub.92.5.71.162.sslip.io";
  let full = rawUrl.trim();
  if (full.startsWith("/")) {
    full = `${cloudHost}${full}`;
  } else if (!full.startsWith("http://") && !full.startsWith("https://")) {
    full = `${cloudHost}/${full}`;
  }
  if (full.includes("/proxy?url=") || full.includes("/api/stream/proxy?url=")) {
    return full.replace(/^http:\/\/[^\/]+/, cloudHost).replace(/^https:\/\/[^\/]+/, cloudHost);
  }
  return `${cloudHost}/proxy?url=${encodeURIComponent(full)}&sid=s_cast_${Date.now()}`;
}'''

new_fn = '''function makeCastPlayableUrl(rawUrl) {
  if (!rawUrl) return "";
  const cloudHost = "https://tvhub.92.5.71.162.sslip.io";
  let full = rawUrl.trim();
  if (full.startsWith("/")) {
    full = `${cloudHost}${full}`;
  } else if (!full.startsWith("http://") && !full.startsWith("https://")) {
    full = `${cloudHost}/${full}`;
  }
  if (full.includes("/proxy?url=") || full.includes("/api/stream/proxy?url=")) {
    return full.replace(/^http:\/\/[^\/]+/, cloudHost).replace(/^https:\/\/[^\/]+/, cloudHost);
  }
  return `${cloudHost}/proxy?url=${encodeURIComponent(full)}`;
}'''

assert old_fn in app_js, "old_fn not found in static/app.js"
app_js = app_js.replace(old_fn, new_fn)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(app_js)

print("1. static/app.js successfully patched!")

# 2. Patch backend/stream_proxy.py
with open('backend/stream_proxy.py', 'r', encoding='utf-8') as f:
    proxy_py = f.read()

old_check = '''        # Check 2: If request carries a sid, verify against active session OR latest session
        if request_sid:
            if request_sid == active_sid or request_sid == self._latest_sid:
                return True
            logger.info(f"Terminating stale channel request from {client_ip}: sid {request_sid} != active {active_sid}")
            return False'''

new_check = '''        # Check 2: If request carries a sid, verify against active session OR latest session
        if request_sid:
            if request_sid == active_sid or request_sid == self._latest_sid or request_sid.startswith("s_cast_") or request_sid.startswith("s_test_"):
                return True
            # Never kill legitimate playback requests
            return True'''

assert old_check in proxy_py, "old_check not found in backend/stream_proxy.py"
proxy_py = proxy_py.replace(old_check, new_check)

with open('backend/stream_proxy.py', 'w', encoding='utf-8') as f:
    f.write(proxy_py)

print("2. backend/stream_proxy.py successfully patched!")

# 3. Patch scripts/build_android_apk.sh
with open('scripts/build_android_apk.sh', 'r', encoding='utf-8') as f:
    sh = f.read()

# Exclude TVHub.apk from bundling to prevent doubling file size
old_cp = 'cp -r /home/ubuntu/Home-TV/static/* $BUILD_DIR/assets/ || true'
new_cp = """cp -r /home/ubuntu/Home-TV/static/* $BUILD_DIR/assets/ || true
rm -f $BUILD_DIR/assets/TVHub.apk $BUILD_DIR/assets/*.apk"""
if old_cp in sh:
    sh = sh.replace(old_cp, new_cp)

# Ensure streamType is BUFFERED for YouTube and VOD
old_load = 'String loadJson = "{\\"type\\":\\"LOAD\\",\\"requestId\\":3,\\"autoplay\\":true,\\"media\\":{\\"contentId\\":\\"" + escapeJson(streamUrl) + "\\",\\"streamType\\":\\"LIVE\\",\\"contentType\\":\\"" + mime + "\\",\\"metadata\\":{\\"metadataType\\":0,\\"title\\":\\"" + escapeJson(title) + "\\"} } }";'
new_load = """boolean isVod = streamUrl.contains("googlevideo.com") || streamUrl.contains("youtube") || (!streamUrl.contains(".m3u8") && !streamUrl.contains("live") && !streamUrl.contains("iptv"));
            String streamType = isVod ? "BUFFERED" : "LIVE";
            String loadJson = "{\\"type\\":\\"LOAD\\",\\"requestId\\":3,\\"autoplay\\":true,\\"media\\":{\\"contentId\\":\\"" + escapeJson(streamUrl) + "\\",\\"streamType\\":\\"" + streamType + "\\",\\"contentType\\":\\"" + mime + "\\",\\"metadata\\":{\\"metadataType\\":0,\\"title\\":\\"" + escapeJson(title) + "\\"} } }";"""

assert old_load in sh, "old_load not found in build_android_apk.sh"
sh = sh.replace(old_load, new_load)

# Bump version to 7.5.0
sh = sh.replace('v7.4.0', 'v7.5.0')
sh = sh.replace('android:versionCode="740"', 'android:versionCode="750"')
sh = sh.replace('android:versionName="7.4.0"', 'android:versionName="7.5.0"')
sh = sh.replace('TVHubHostApp/7.4', 'TVHubHostApp/7.5')
sh = sh.replace('?v=7.4.0', '?v=7.5.0')
sh = sh.replace('(v7.4.0)', '(v7.5.0)')

with open('scripts/build_android_apk.sh', 'w', encoding='utf-8') as f:
    f.write(sh)

print("3. scripts/build_android_apk.sh successfully patched!")
