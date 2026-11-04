with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

old_univ_path = "  // Path A: Direct in-browser Google Cast is active -> Cast straight from Phone to TV over Wi-Fi"
new_univ_path0 = """  // Path 0: Native Android TV Hub App -> Cast directly to TV via phone local Wi-Fi!
  if (window.TVHubAndroid && typeof window.TVHubAndroid.isNativeApp === "function" && window.TVHubAndroid.isNativeApp()) {
    const selectedDev = state.devices.find(d => d.id === state.currentTvId) || {};
    const targetIp = selectedDev.ip || (state.currentTvId === "hisense" ? "192.168.50.249" : "192.168.50.205");
    const devType = selectedDev.dev_type || (state.currentTvId === "hisense" ? "hisense" : "google_tv");
    let ytId = "";
    const ytMatch = url.match(/(?:youtu\\.be\\/|v\\/|u\\/\\w\\/|embed\\/|watch\\?v=|&v=)([^#&?]{11})/);
    if (ytMatch) ytId = ytMatch[1];
    showToast(`Casting video to ${state.currentTvName}...`);
    window.TVHubAndroid.castToTv(targetIp, devType, makeCastPlayableUrl(url), title || "Video Stream", "video/mp4", ytId);
    state.currentTitle = title || "Video Stream";
    const barTitle = document.getElementById("bar-title");
    if (barTitle) barTitle.textContent = state.currentTitle;
    return;
  }

  // Path A: Direct in-browser Google Cast is active -> Cast straight from Phone to TV over Wi-Fi"""

if old_univ_path in js:
    js = js.replace(old_univ_path, new_univ_path0, 1)
    with open("static/app.js", "w", encoding="utf-8") as f:
        f.write(js)
    print("Added Path 0 to executeUniversalCast in static/app.js")
else:
    print("Warning: old_univ_path not found")
