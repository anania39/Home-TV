import re

# 1. Patch backend/app.py
with open("backend/app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

old_cast_fallback = """        # If home hub is offline but a TV Web Receiver is active on cloud, cast straight to it!
        if len(ws_manager.receivers) > 0:
            logger.info("Home hub is offline, routing cast directly to active TV Web Receiver...")
            device_id = "web_receiver"
            req.device_id = "web_receiver"
        else:
            return forward_res"""

new_cast_fallback = """        # If home hub is offline but a TV Web Receiver is active on cloud, cast straight to it!
        if len(ws_manager.receivers) > 0:
            logger.info("Home hub is offline, routing cast directly to active TV Web Receiver...")
            device_id = "web_receiver"
            req.device_id = "web_receiver"
        else:
            # Home hub is offline: resolve media stream on cloud so phone/Cast can play directly
            from .media_resolver import media_resolver
            pref_title = req.title if req.title not in ("Live Stream", "Video Stream") else None
            resolved = await media_resolver.resolve(req.url.strip(), preferred_title=pref_title)
            final_stream_url = resolved.get("stream_url") or req.url.strip()
            return {
                "status": "fallback",
                "use_web_cast": True,
                "stream_url": final_stream_url,
                "title": resolved.get("title") or req.title or "Video Stream",
                "thumbnail": resolved.get("thumbnail") or "",
                "mime_type": resolved.get("mime_type") or "video/mp4",
                "duration": resolved.get("duration") or 0,
                "message": "Direct phone-to-TV casting active. Select your TV from the Cast prompt.",
                "tv_online": True,
                "offline_reason": "laptop_hub_offline"
            }"""

old_iptv_fallback = """        if len(ws_manager.receivers) > 0:
            logger.info("Home hub is offline, routing IPTV cast directly to active TV Web Receiver...")
            target_dev = "web_receiver"
            device_id = "web_receiver"
        else:
            return forward_res"""

new_iptv_fallback = """        if len(ws_manager.receivers) > 0:
            logger.info("Home hub is offline, routing IPTV cast directly to active TV Web Receiver...")
            target_dev = "web_receiver"
            device_id = "web_receiver"
        else:
            channel = iptv_manager.get_channel_by_id(channel_id)
            active_url = channel["url"] if channel else f"/proxy?url=https://example.com/stream.m3u8"
            name = channel["name"] if channel else "TV Channel"
            logo = channel.get("logo", "") if channel else ""
            return {
                "status": "fallback",
                "use_web_cast": True,
                "stream_url": active_url,
                "title": name,
                "logo": logo,
                "channel_id": channel_id,
                "message": "Direct phone-to-TV casting active. Select your TV from the Cast prompt.",
                "tv_online": True,
                "offline_reason": "laptop_hub_offline"
            }"""

if old_cast_fallback in app_code:
    app_code = app_code.replace(old_cast_fallback, new_cast_fallback)
    print("Replaced old_cast_fallback in backend/app.py")
else:
    print("Warning: old_cast_fallback not matched")

if old_iptv_fallback in app_code:
    app_code = app_code.replace(old_iptv_fallback, new_iptv_fallback)
    print("Replaced old_iptv_fallback in backend/app.py")
else:
    print("Warning: old_iptv_fallback not matched")

with open("backend/app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

# 2. Patch static/app.js
with open("static/app.js", "r", encoding="utf-8") as f:
    js_code = f.read()

old_js_cast_fallback = """    if (data.status === "fallback" || data.use_web_cast) {
      clearTimeout(stepTimer);
      hideCastProgress();
      if (isWebCastActive()) {
        showToast("Casting directly to TV via Web Cast...");
        castViaWebCast(url, title || "Video Stream");
      } else {
        requestWebCastSession({
          url: makeCastPlayableUrl(url),
          title: title || "Video Stream",
          poster: "",
          isChannel: false
        });
        showToast("Select your TV from the Cast prompt or open /tv in TV browser");
      }
      return;
    }"""

new_js_cast_fallback = """    if (data.status === "fallback" || data.use_web_cast) {
      clearTimeout(stepTimer);
      hideCastProgress();
      const castPlayUrl = data.stream_url ? makeCastPlayableUrl(data.stream_url) : makeCastPlayableUrl(url);
      const castTitle = data.title || title || "Video Stream";
      const castPoster = data.thumbnail || "";
      if (isWebCastActive()) {
        showToast("Casting directly to TV via Web Cast...");
        castViaWebCast(castPlayUrl, castTitle, castPoster);
      } else {
        requestWebCastSession({
          url: castPlayUrl,
          title: castTitle,
          poster: castPoster,
          isChannel: false
        });
        showToast("Select your TV from the Cast prompt or open /tv in TV browser");
      }
      return;
    }"""

old_js_iptv_fallback = """      if (data && (data.status === "fallback" || data.use_web_cast)) {
        if (typeof cast !== "undefined" && cast.framework) {
          showToast(`Select your TV to cast ${channel.name}...`);
          requestWebCastSession({
            url: streamUrl,
            title: channel.name,
            poster: channel.logo || "",
            isChannel: true,
            channel: channel
          });
          return;
        }
      }"""

new_js_iptv_fallback = """      if (data && (data.status === "fallback" || data.use_web_cast)) {
        const playUrl = data.stream_url ? makeCastPlayableUrl(data.stream_url) : castUrl;
        if (typeof cast !== "undefined" && cast.framework) {
          showToast(`Select your TV to cast ${channel.name}...`);
          requestWebCastSession({
            url: playUrl,
            title: channel.name,
            poster: channel.logo || "",
            isChannel: true,
            channel: channel
          });
          return;
        } else {
          openInAppPlayer(channel);
          return;
        }
      }"""

if old_js_cast_fallback in js_code:
    js_code = js_code.replace(old_js_cast_fallback, new_js_cast_fallback)
    print("Replaced old_js_cast_fallback in static/app.js")
else:
    print("Warning: old_js_cast_fallback not matched")

if old_js_iptv_fallback in js_code:
    js_code = js_code.replace(old_js_iptv_fallback, new_js_iptv_fallback)
    print("Replaced old_js_iptv_fallback in static/app.js")
else:
    print("Warning: old_js_iptv_fallback not matched")

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js_code)

print("Patch complete.")
with open("backend/app.py", "r", encoding="utf-8") as f:
    text = f.read()

target = '@app.get("/TVHub.apk")\n@app.get("/app.apk")'
replacement = '@app.get("/TVHub.apk")\n@app.head("/TVHub.apk")\n@app.get("/app.apk")\n@app.head("/app.apk")'

if target in text:
    text = text.replace(target, replacement)
    with open("backend/app.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added HEAD route support for APK download")
