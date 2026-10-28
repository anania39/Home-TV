import re

def main():
    path = "static/app.js"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    prefix = """// TV Hub Dynamic Backend & Permanent GitHub Pages Resolution
let HUB_BASE = localStorage.getItem("tvhub_backend_url") || "";

function getHubBase() {
  if (HUB_BASE) return HUB_BASE.replace(/\\/+$/, "");
  const params = new URLSearchParams(window.location.search);
  const hubParam = params.get("hub");
  if (hubParam) {
    HUB_BASE = hubParam.replace(/\\/+$/, "");
    localStorage.setItem("tvhub_backend_url", HUB_BASE);
    return HUB_BASE;
  }
  return "";
}

function getApiUrl(path) {
  const base = getHubBase();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${cleanPath}` : cleanPath;
}

function getWsUrl(path) {
  const base = getHubBase();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  if (base) {
    const wsProto = base.startsWith("https:") ? "wss:" : "ws:";
    const host = base.replace(/^https?:\\/\\//, "");
    return `${wsProto}//${host}${cleanPath}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${cleanPath}`;
}

function resolveAssetUrl(path) {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:")) {
    return path;
  }
  if (path.startsWith("/static/")) {
    return "./" + path.substring(1);
  }
  if (path.startsWith("/")) {
    return "." + path;
  }
  return path;
}

async function autoDetectHub() {
  if (window.location.hostname.includes("github.io") && !localStorage.getItem("tvhub_backend_url")) {
    try {
      const res = await fetch("./endpoint.json?t=" + Date.now());
      if (res.ok) {
        const info = await res.json();
        if (info.hub_url) {
          HUB_BASE = info.hub_url;
          console.log("TV Hub Auto-Detected:", HUB_BASE);
          return true;
        }
      }
    } catch (e) {}
    try {
      const rawRes = await fetch("https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t=" + Date.now());
      if (rawRes.ok) {
        const info = await rawRes.json();
        if (info.hub_url) {
          HUB_BASE = info.hub_url;
          console.log("TV Hub Auto-Detected from GitHub:", HUB_BASE);
          return true;
        }
      }
    } catch (err) {}
  }
  return false;
}

"""

    text = prefix + text

    # Update handleImgError
    old_handle = """window.handleImgError = function(imgElement, name, genre, lang) {
  // If this image hasn't tried our server logo proxy yet, try it once!
  if (!imgElement.dataset.proxyTried && imgElement.src && !imgElement.src.includes("/api/logo/proxy")) {
    imgElement.dataset.proxyTried = "true";
    imgElement.src = `/api/logo/proxy?url=${encodeURIComponent(imgElement.src)}`;
    return;
  }"""

    new_handle = """window.handleImgError = function(imgElement, name, genre, lang) {
  // 1. Try online fallback logo if available
  const fallback = imgElement.dataset.fallbackLogo;
  if (fallback && imgElement.src !== fallback && !imgElement.dataset.triedFallback) {
    imgElement.dataset.triedFallback = "true";
    imgElement.src = fallback;
    return;
  }

  // 2. Try proxy if backend is active
  const base = getHubBase();
  if (base && !imgElement.dataset.proxyTried && imgElement.src && !imgElement.src.includes("/api/logo/proxy")) {
    imgElement.dataset.proxyTried = "true";
    imgElement.src = `${base}/api/logo/proxy?url=${encodeURIComponent(imgElement.src)}`;
    return;
  }"""

    text = text.replace(old_handle, new_handle)

    # Update DOMContentLoaded
    old_dcl = """document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  checkAuth();"""

    new_dcl = """document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initHubModal();
  await autoDetectHub();
  checkAuth();"""

    text = text.replace(old_dcl, new_dcl)

    # Update checkAuth
    old_auth = """// --- Network & Auth ---
async function checkAuth() {
  try {
    const res = await fetch("/api/auth/status");
    if (res.ok) {
      const data = await res.json();
      document.getElementById("network-badge-text").textContent = `Connected (${data.client_ip})`;
      document.getElementById("info-server-ip").textContent = `${data.server_ip}:${data.port}`;
      document.getElementById("tv-receiver-url").textContent = `http://${data.server_ip}:${data.port}/tv`;

      const localWifi = document.getElementById("local-wifi-link");
      if (localWifi) {
        const localUrl = `http://${data.server_ip}:${data.port}`;
        localWifi.href = localUrl;
        localWifi.textContent = localUrl;
      }

      const shortLink = document.getElementById("short-phone-link");
      const pubLink = document.getElementById("public-phone-link");
      const qrImg = document.getElementById("qr-code-img");

      const activeShort = data.short_url || data.public_url;
      if (activeShort) {
        if (shortLink) {
          shortLink.href = activeShort;
          shortLink.textContent = activeShort;
        }
        if (pubLink && data.public_url) {
          pubLink.href = data.public_url;
          pubLink.textContent = data.public_url;
        }
        if (qrImg) {
          qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=280x280&data=${encodeURIComponent(activeShort)}`;
        }"""

    new_auth = """// --- Network & Auth ---
async function checkAuth() {
  const badge = document.getElementById("network-badge-text");
  try {
    const res = await fetch(getApiUrl("/api/auth/status"));
    if (res.ok) {
      const data = await res.json();
      if (badge) {
        badge.innerHTML = `<span style="color: var(--accent-green); cursor: pointer;" title="Hub Connected. Click to configure">🟢 Connected (${data.client_ip})</span>`;
      }
      const srvIp = document.getElementById("info-server-ip");
      if (srvIp) srvIp.textContent = `${data.server_ip}:${data.port}`;
      const recUrl = document.getElementById("tv-receiver-url");
      if (recUrl) recUrl.textContent = `http://${data.server_ip}:${data.port}/tv`;

      const localWifi = document.getElementById("local-wifi-link");
      if (localWifi) {
        const localUrl = `http://${data.server_ip}:${data.port}`;
        localWifi.href = localUrl;
        localWifi.textContent = localUrl;
      }

      const pubLink = document.getElementById("public-phone-link");
      if (pubLink && data.public_url) {
        pubLink.href = data.public_url;
        pubLink.textContent = data.public_url;
      }
      const shortLink = document.getElementById("short-phone-link");
      const activeShort = data.short_url || data.public_url;
      if (shortLink && activeShort) {
        shortLink.href = activeShort;
        shortLink.textContent = activeShort;
      }"""

    text = text.replace(old_auth, new_auth)

    old_catch = """    }
  } catch (e) {
    document.getElementById("network-badge-text").textContent = "Offline / Standby";
  }
}"""

    new_catch = """    }
  } catch (e) {
    if (window.location.hostname.includes("github.io")) {
      if (badge) {
        badge.innerHTML = `<span style="color: var(--accent-cyan); cursor: pointer;" title="Tap to configure TV Hub">🌐 GitHub Pages (${getHubBase() ? "Hub Linked" : "Tap to Link Hub"})</span>`;
      }
    } else {
      if (badge) {
        badge.innerHTML = `<span style="color: var(--accent-amber); cursor: pointer;" title="Tap to check Hub connection">🟡 Standalone Mode</span>`;
      }
    }
  }
}"""

    text = text.replace(old_catch, new_catch)

    # API endpoints
    text = text.replace('fetch("/api/devices")', 'fetch(getApiUrl("/api/devices"))')
    text = text.replace('fetch("/api/devices/select",', 'fetch(getApiUrl("/api/devices/select"),')
    text = text.replace('fetch("/api/devices/scan",', 'fetch(getApiUrl("/api/devices/scan"),')
    text = text.replace('fetch("/api/tv/wake",', 'fetch(getApiUrl("/api/tv/wake"),')

    old_fetch_channels = """async function fetchChannels() {
  try {
    const res = await fetch("/api/iptv/channels?sort_by=popularity");
    const data = await res.json();
    state.channels = data.channels;
    renderChannels();
  } catch (e) {
    console.error("Failed to load IPTV channels:", e);
  }
}"""

    new_fetch_channels = """async function fetchChannels() {
  try {
    const res = await fetch(getApiUrl("/api/iptv/channels?sort_by=popularity"));
    if (!res.ok) throw new Error("Backend returned " + res.status);
    const data = await res.json();
    state.channels = data.channels;
    renderChannels();
  } catch (e) {
    console.warn("Backend channels unavailable, loading local static playlist:", e);
    try {
      const staticRes = await fetch("./playlists/channels-with-backups.json");
      if (staticRes.ok) {
        const staticList = await staticRes.json();
        state.channels = staticList;
        renderChannels();
      }
    } catch (err2) {
      console.error("Failed to load static playlist:", err2);
    }
  }
}"""

    text = text.replace(old_fetch_channels, new_fetch_channels)

    old_logo = """    const initials = getInitials(ch.name);
    const logoSrc = ch.local_logo || ch.logo;
    const logoHtml = logoSrc
      ? `<img src="${logoSrc}" class="channel-logo" alt="${ch.name}" referrerpolicy="no-referrer" loading="lazy" onerror="handleImgError(this, '${ch.name.replace(/'/g, "\\'")}', '${ch.genre || "General"}', '${ch.language || "English"}')">`
      : `<div class="monogram-fallback"><span>${initials}</span><span class="monogram-sub">📺</span></div>`;"""

    new_logo = """    const initials = getInitials(ch.name);
    const resolvedLocal = resolveAssetUrl(ch.local_logo);
    const logoSrc = resolvedLocal || ch.logo;
    const fallbackLogo = ch.logo || "";
    const logoHtml = logoSrc
      ? `<img src="${logoSrc}" class="channel-logo" alt="${ch.name}" data-fallback-logo="${fallbackLogo}" referrerpolicy="no-referrer" loading="lazy" onerror="handleImgError(this, '${ch.name.replace(/'/g, "\\'")}', '${ch.genre || "General"}', '${ch.language || "English"}')">`
      : `<div class="monogram-fallback"><span>${initials}</span><span class="monogram-sub">📺</span></div>`;"""

    text = text.replace(old_logo, new_logo)

    text = text.replace('fetch(`/api/iptv/cast/${channel.id}`,', 'fetch(getApiUrl(`/api/iptv/cast/${channel.id}`),')
    text = text.replace('fetch("/api/remote/key",', 'fetch(getApiUrl("/api/remote/key"),')
    text = text.replace('fetch("/api/playback/action",', 'fetch(getApiUrl("/api/playback/action"),')
    text = text.replace('fetch("/api/cast",', 'fetch(getApiUrl("/api/cast"),')
    text = text.replace('fetch("/api/media/upload",', 'fetch(getApiUrl("/api/media/upload"),')
    text = text.replace('fetch(`/api/media/cast/${encodeURIComponent(file.name)}`,', 'fetch(getApiUrl(`/api/media/cast/${encodeURIComponent(file.name)}`),')
    text = text.replace('fetch("/api/media/files")', 'fetch(getApiUrl("/api/media/files"))')
    text = text.replace('fetch(`/api/media/cast/${encodeURIComponent(f.name)}`,', 'fetch(getApiUrl(`/api/media/cast/${encodeURIComponent(f.name)}`),')
    text = text.replace('fetch("/api/playback/volume",', 'fetch(getApiUrl("/api/playback/volume"),')
    text = text.replace('fetch("/api/devices/manual",', 'fetch(getApiUrl("/api/devices/manual"),')
    text = text.replace('fetch("/api/iptv/import",', 'fetch(getApiUrl("/api/iptv/import"),')

    old_ws = """// --- WebSocket Real-Time Sync ---
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/controller`;
  state.ws = new WebSocket(wsUrl);"""

    new_ws = """// --- WebSocket Real-Time Sync ---
function connectWebSocket() {
  if (window.location.hostname.includes("github.io") && !getHubBase()) {
    return; // Standalone GitHub Pages mode: skip WebSocket until Hub is linked
  }
  const wsUrl = getWsUrl("/ws/controller");
  try {
    state.ws = new WebSocket(wsUrl);"""

    text = text.replace(old_ws, new_ws)

    old_ws_end = """  state.ws.onclose = () => {
    setTimeout(connectWebSocket, 2500);
  };
}"""

    new_ws_end = """    state.ws.onclose = () => {
      setTimeout(connectWebSocket, 3500);
    };
  } catch (err) {
    console.debug("WebSocket connect error:", err);
  }
}"""

    text = text.replace(old_ws_end, new_ws_end)

    text = text.replace('fetch(`/api/sports/events?${params.toString()}`)', 'fetch(getApiUrl(`/api/sports/events?${params.toString()}`))')
    text = text.replace('fetch(`/api/sports/match/${encodeURIComponent(slug)}`)', 'fetch(getApiUrl(`/api/sports/match/${encodeURIComponent(slug)}`))')
    text = text.replace('iframe.src = `/api/sports/player/${encodeURIComponent(streamSlug)}`;', 'iframe.src = getApiUrl(`/api/sports/player/${encodeURIComponent(streamSlug)}`);')

    hub_modal_code = """
// --- Hub Connection Modal Logic ---
function initHubModal() {
  const modal = document.getElementById("modal-hub-settings");
  const btnOpen = document.getElementById("btn-hub-settings");
  const btnClose = document.getElementById("btn-close-hub-modal");
  const inputUrl = document.getElementById("input-hub-url");
  const feedback = document.getElementById("hub-connection-feedback");
  const btnSave = document.getElementById("btn-save-hub-url");
  const btnTest = document.getElementById("btn-test-hub-url");
  const btnAuto = document.getElementById("btn-use-autodetect");
  const btnLocal = document.getElementById("btn-use-local");
  const btnSameOrigin = document.getElementById("btn-use-sameorigin");
  const networkBadge = document.getElementById("network-badge-text");

  if (!modal) return;

  function openModal() {
    vibrate(20);
    inputUrl.value = getHubBase();
    feedback.innerHTML = getHubBase()
      ? `<span style="color:var(--accent-cyan)">Current Hub: <strong>${escapeHtml(getHubBase())}</strong></span>`
      : `<span style="color:var(--text-muted)">Standalone Mode: All 137 channels viewable in browser. Link Hub to control Living Room TV.</span>`;
    modal.classList.add("open");
  }

  btnOpen?.addEventListener("click", openModal);
  networkBadge?.addEventListener("click", openModal);
  btnClose?.addEventListener("click", () => modal.classList.remove("open"));

  btnAuto?.addEventListener("click", async () => {
    vibrate(15);
    feedback.innerHTML = `<span style="color:var(--accent-cyan)">🔄 Fetching active Hub endpoint from GitHub...</span>`;
    const ok = await autoDetectHub();
    if (ok) {
      inputUrl.value = HUB_BASE;
      feedback.innerHTML = `<span style="color:var(--accent-green)">✅ Found active Hub: ${escapeHtml(HUB_BASE)}</span>`;
    } else {
      feedback.innerHTML = `<span style="color:var(--accent-amber)">⚠️ Could not detect tunnel. Ensure TV Hub is running on your laptop.</span>`;
    }
  });

  btnLocal?.addEventListener("click", () => {
    vibrate(15);
    inputUrl.value = "http://192.168.50.250:8000";
    feedback.innerHTML = `<span style="color:var(--accent-green)">🏠 Local Wi-Fi endpoint set</span>`;
  });

  btnSameOrigin?.addEventListener("click", () => {
    vibrate(15);
    inputUrl.value = "";
    feedback.innerHTML = `<span style="color:var(--accent-green)">⚡ Direct same-origin set</span>`;
  });

  btnTest?.addEventListener("click", async () => {
    vibrate(20);
    const testUrl = inputUrl.value.trim().replace(/\\/+$/, "");
    feedback.innerHTML = `<span style="color:var(--text-muted)">⏳ Testing connection to ${testUrl ? escapeHtml(testUrl) : "same-origin"}...</span>`;
    try {
      const url = testUrl ? `${testUrl}/api/auth/status` : "/api/auth/status";
      const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (res.ok) {
        const data = await res.json();
        feedback.innerHTML = `<span style="color:var(--accent-green)">✅ Online! Connected to Hub (${data.client_ip})</span>`;
      } else {
        feedback.innerHTML = `<span style="color:var(--accent-amber)">⚠️ Reached server but returned HTTP ${res.status}</span>`;
      }
    } catch (e) {
      feedback.innerHTML = `<span style="color:var(--accent-red)">❌ Connection failed: ${escapeHtml(e.message)}</span>`;
    }
  });

  btnSave?.addEventListener("click", async () => {
    vibrate(30);
    const newBase = inputUrl.value.trim().replace(/\\/+$/, "");
    HUB_BASE = newBase;
    if (newBase) {
      localStorage.setItem("tvhub_backend_url", newBase);
    } else {
      localStorage.removeItem("tvhub_backend_url");
    }
    modal.classList.remove("open");
    showToast("Hub URL saved. Connecting...");
    await checkAuth();
    await fetchDevices();
    await fetchChannels();
    connectWebSocket();
  });

  // Permanent link copy handlers
  document.getElementById("btn-copy-gh-link")?.addEventListener("click", () => {
    vibrate(20);
    navigator.clipboard.writeText("https://anania39.github.io/Home-TV/");
    showToast("🌟 Permanent link copied to clipboard!");
  });
  document.getElementById("btn-copy-receiver-link")?.addEventListener("click", () => {
    vibrate(20);
    navigator.clipboard.writeText("https://anania39.github.io/Home-TV/tv.html");
    showToast("📺 TV Receiver link copied!");
  });
}
"""

    text = text + hub_modal_code

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print("Successfully patched static/app.js. New length:", len(text))

if __name__ == "__main__":
    main()
