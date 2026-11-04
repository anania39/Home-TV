with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# 1. Update DEFAULT_HOUSEHOLD_DEVICES to include ip, port, dev_type
old_devices = """const DEFAULT_HOUSEHOLD_DEVICES = [
  { id: "tv_192_168_50_205", name: "TCL Smart TV Pro (Google TV)", is_google_tv: true },
  { id: "tv_192_168_50_249", name: "Hisense VIDAA TV (Living Room)", is_hisense: true },
  { id: "tv_192_168_50_3", name: "Xiaomi Mi TV (Google TV)", is_google_tv: true },
  { id: "web_receiver", name: "TV Web Receiver (Browser at /tv)", type: "browser" }
];"""

new_devices = """const DEFAULT_HOUSEHOLD_DEVICES = [
  { id: "tv_192_168_50_205", name: "TCL Smart TV Pro (Google TV)", ip: "192.168.50.205", port: 8009, dev_type: "google_tv", is_google_tv: true },
  { id: "tv_192_168_50_249", name: "Hisense VIDAA TV (Living Room)", ip: "192.168.50.249", port: 38400, dev_type: "hisense", is_hisense: true },
  { id: "tv_192_168_50_3", name: "Xiaomi Mi TV (Google TV)", ip: "192.168.50.3", port: 8009, dev_type: "google_tv", is_google_tv: true },
  { id: "web_receiver", name: "TV Web Receiver (Browser at /tv)", type: "browser" }
];"""

if old_devices in js:
    js = js.replace(old_devices, new_devices, 1)
    print("Updated DEFAULT_HOUSEHOLD_DEVICES in static/app.js")
else:
    print("Warning: old_devices not found")

# 2. Update sendWakeOnLan to invoke native bridge
old_wake = """async function sendWakeOnLan() {
  vibrate(35);
  showToast("⚡ Sending Wake-on-LAN power packet...");
  try {
    await safeFetchWithRetry("/api/tv/wake", { method: "POST" });
  } catch (e) {}
}"""

new_wake = """async function sendWakeOnLan() {
  vibrate(35);
  showToast("⚡ Sending Wake-on-LAN power packet...");
  if (window.TVHubAndroid && typeof window.TVHubAndroid.sendWakeOnLan === "function") {
    window.TVHubAndroid.sendWakeOnLan();
  }
  try {
    await safeFetchWithRetry("/api/tv/wake", { method: "POST" });
  } catch (e) {}
}"""

if old_wake in js:
    js = js.replace(old_wake, new_wake, 1)
    print("Updated sendWakeOnLan in static/app.js")
else:
    print("Warning: old_wake not found")

# 3. Add Native Host Mode to checkAuth
old_auth_badge = 'badge.innerHTML = `<span style="color: var(--accent-green); cursor: pointer;" title="Hub Connected. Click to configure">🟢 Connected (${data.client_ip})</span>`;'
new_auth_badge = """if (window.TVHubAndroid && typeof window.TVHubAndroid.isNativeApp === "function" && window.TVHubAndroid.isNativeApp()) {
        badge.innerHTML = `<span style="color: var(--accent-green); cursor: pointer;" title="Mobile Phone is the Local Network Host">🟢 Host Active (Mobile Wi-Fi)</span>`;
        state.hubOnline = true;
        state.tvOnline = true;
        const barDot = document.getElementById("bar-status-dot");
        const barStatus = document.getElementById("bar-tv-status");
        if (barDot) barDot.style.background = "var(--accent-green)";
        if (barStatus) barStatus.textContent = `${state.currentTvName || "Smart TV"} Ready`;
      } else {
        badge.innerHTML = `<span style="color: var(--accent-green); cursor: pointer;" title="Hub Connected. Click to configure">🟢 Connected (${data.client_ip})</span>`;
      }"""

if old_auth_badge in js:
    js = js.replace(old_auth_badge, new_auth_badge, 1)
    print("Updated checkAuth with Mobile Host mode in static/app.js")
else:
    print("Warning: old_auth_badge not found")

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js)

print("static/app.js patching complete.")
