with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Fix makeCastPlayableUrl to ALWAYS return an absolute URL anchored to https://tvhub.92.5.71.162.sslip.io
old_cast_playable = """function makeCastPlayableUrl(rawUrl) {
  if (!rawUrl) return "";
  const cloudHost = CLOUD_FALLBACK_URL;
  const base = getHubBase() || cloudHost;
  if (rawUrl.includes("/proxy?url=") || rawUrl.includes("/api/stream/proxy?url=")) {
    if (rawUrl.startsWith("/")) return `${base}${rawUrl}`;
    return rawUrl.replace(/^http:\/\//, "https://");
  }
  return `${base}/proxy?url=${encodeURIComponent(rawUrl)}&sid=s_cast_${Date.now()}`;
}"""

new_cast_playable = """function makeCastPlayableUrl(rawUrl) {
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
}"""

assert old_cast_playable in js, "old_cast_playable not found"
js = js.replace(old_cast_playable, new_cast_playable, 1)

# 2. In executeUniversalCast ensure playUrl is absolute
old_yt_replace = 'playUrl = data.stream_url.includes("/proxy?url=") ? data.stream_url : `/proxy?url=${encodeURIComponent(data.stream_url)}`;'
new_yt_replace = 'playUrl = data.stream_url.includes("/proxy?url=") ? data.stream_url : `https://tvhub.92.5.71.162.sslip.io/proxy?url=${encodeURIComponent(data.stream_url)}`;'

if old_yt_replace in js:
    js = js.replace(old_yt_replace, new_yt_replace, 1)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("static/app.js patched with absolute cast URLs!")
