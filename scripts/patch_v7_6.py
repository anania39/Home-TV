# 1. Patch static/app.js
with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# A. Update makeCastPlayableUrl to pass googlevideo.com directly to TV
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
  return `${cloudHost}/proxy?url=${encodeURIComponent(full)}`;
}'''

new_fn = '''function makeCastPlayableUrl(rawUrl) {
  if (!rawUrl) return "";
  const cloudHost = "https://tvhub.92.5.71.162.sslip.io";
  let full = rawUrl.trim();
  // YouTube and GoogleVideo streams are signed with client IP; TV fetches them directly from Google without VPS proxy
  if (full.includes("googlevideo.com")) {
    if (full.includes("/proxy?url=")) {
      const match = full.match(/[?&]url=([^&]+)/);
      if (match) return decodeURIComponent(match[1]);
    }
    return full;
  }
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

assert old_fn in js, "makeCastPlayableUrl not found"
js = js.replace(old_fn, new_fn)

# B. Prevent any phone playback inside the native app
old_open_player = '''function openInAppPlayer(channel) {
  const modal = document.getElementById("modal-inapp-player");'''

new_open_player = '''function openInAppPlayer(channel) {
  if (window.TVHubAndroid && typeof window.TVHubAndroid.isNativeApp === "function" && window.TVHubAndroid.isNativeApp()) {
    // In native app, NEVER play on phone - ALWAYS cast to TV!
    castChannel(channel);
    return;
  }
  const modal = document.getElementById("modal-inapp-player");'''

assert old_open_player in js, "openInAppPlayer not found"
js = js.replace(old_open_player, new_open_player)

# C. Remove the small phone button from channel cards
js = js.replace('<button class="channel-phone-play-btn" title="Watch on Phone" data-play-phone="${ch.id}">📱</button>', '')

# D. Update executeUniversalCast playUrl handling for YouTube
old_yt_resolve = '''        if (data.resolved && data.stream_url) {
          playUrl = data.stream_url.includes("/proxy?url=") ? data.stream_url : `https://tvhub.92.5.71.162.sslip.io/proxy?url=${encodeURIComponent(data.stream_url)}`;
          playTitle = data.title || playTitle;
          mimeType = data.mime_type || "application/x-mpegurl";
        }'''

new_yt_resolve = '''        if (data.resolved && data.stream_url) {
          // Pass direct stream_url for googlevideo so TV fetches directly from Google CDN with matching IP token
          playUrl = data.stream_url;
          playTitle = data.title || playTitle;
          mimeType = data.mime_type || "application/x-mpegurl";
        }'''

assert old_yt_resolve in js, "old_yt_resolve not found"
js = js.replace(old_yt_resolve, new_yt_resolve)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("1. static/app.js patched for direct YouTube playback and zero in-app phone playback!")

# 2. Patch scripts/build_android_apk.sh
with open('scripts/build_android_apk.sh', 'r', encoding='utf-8') as f:
    sh = f.read()

# In performDirectCast, unwrap googlevideo proxy if present
old_pdc = '''        String targetIp = (ip != null && !ip.isEmpty()) ? ip : "192.168.50.205";
        if (streamUrl != null && streamUrl.startsWith("/")) {
            streamUrl = "https://tvhub.92.5.71.162.sslip.io" + streamUrl;
        }'''

new_pdc = '''        String targetIp = (ip != null && !ip.isEmpty()) ? ip : "192.168.50.205";
        if (streamUrl != null && streamUrl.startsWith("/")) {
            streamUrl = "https://tvhub.92.5.71.162.sslip.io" + streamUrl;
        }
        if (streamUrl != null && streamUrl.contains("googlevideo.com") && streamUrl.contains("/proxy?url=")) {
            int qIdx = streamUrl.indexOf("url=");
            if (qIdx != -1) {
                String sub = streamUrl.substring(qIdx + 4);
                try {
                    streamUrl = java.net.URLDecoder.decode(sub, "UTF-8");
                } catch (Exception ignored) {}
            }
        }'''

assert old_pdc in sh, "old_pdc not found"
sh = sh.replace(old_pdc, new_pdc)

# Bump version to 7.6.0
sh = sh.replace('v7.5.0', 'v7.6.0')
sh = sh.replace('android:versionCode="750"', 'android:versionCode="760"')
sh = sh.replace('android:versionName="7.5.0"', 'android:versionName="7.6.0"')
sh = sh.replace('TVHubHostApp/7.5', 'TVHubHostApp/7.6')
sh = sh.replace('?v=7.5.0', '?v=7.6.0')
sh = sh.replace('(v7.5.0)', '(v7.6.0)')

with open('scripts/build_android_apk.sh', 'w', encoding='utf-8') as f:
    f.write(sh)

print("2. scripts/build_android_apk.sh patched for v7.6.0!")
