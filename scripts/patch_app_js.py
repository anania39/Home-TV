from pathlib import Path

def patch_app_js():
    p = Path("static/app.js")
    code = p.read_text(encoding="utf-8")

    # 1. Update Safe Fetch & Hub Base logic
    old_top = '''// TV Hub Dynamic Backend & Permanent GitHub Pages Resolution
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


async function safeFetchWithRetry(path, options = {}) {
  let url = getApiUrl(path);
  options = options || {};
  let hdrs = options.headers || {};
  if (typeof Headers !== "undefined" && hdrs instanceof Headers) {
    hdrs.set("bypass-tunnel-reminder", "true");
    hdrs.set("ngrok-skip-browser-warning", "true");
  } else {
    hdrs = Object.assign({}, hdrs, { "bypass-tunnel-reminder": "true", "ngrok-skip-browser-warning": "true" });
  }
  options.headers = hdrs;

  try {
    const res = await fetch(url, options);
    if (res.status === 502 || res.status === 504 || res.status === 503) {
      throw new Error(`Tunnel gateway error: ${res.status}`);
    }
    return res;
  } catch (err) {
    console.warn(`Request to ${url} failed, attempting endpoint recovery...`, err);
    if (window.location.hostname.includes("github.io")) {
      const recovered = await autoDetectHub(true);
      if (recovered) {
        url = getApiUrl(path);
        return await fetch(url, options);
      }
    }
    throw err;
  }
}

function getApiUrl(path) {
  const base = getHubBase();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${cleanPath}` : cleanPath;
}'''

    new_top = '''// TV Hub Dynamic Backend & Permanent GitHub Pages Resolution
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
  if (base) {
    return `${base}${cleanPath}`;
  }
  // On GitHub Pages, NEVER return relative API path to avoid HTTP 405 Method Not Allowed!
  if (window.location.hostname.includes("github.io")) {
    return "";
  }
  return cleanPath;
}

async function safeFetchWithRetry(path, options = {}) {
  const isGithubPages = window.location.hostname.includes("github.io");
  let base = getHubBase();

  // On GitHub Pages, ensure backend URL is resolved before firing requests
  if (isGithubPages && (!base || base.includes("github.io"))) {
    await autoDetectHub(true);
    base = getHubBase();
  }

  let url = getApiUrl(path);
  if (!url) {
    // If backend is offline on GitHub Pages, throw descriptive error instead of 405
    throw new Error("TV Hub server is offline. Please make sure TV Hub is running on your laptop.");
  }

  options = options || {};
  let hdrs = options.headers || {};
  if (typeof Headers !== "undefined" && hdrs instanceof Headers) {
    hdrs.set("bypass-tunnel-reminder", "true");
    hdrs.set("ngrok-skip-browser-warning", "true");
  } else {
    hdrs = Object.assign({}, hdrs, { "bypass-tunnel-reminder": "true", "ngrok-skip-browser-warning": "true" });
  }
  options.headers = hdrs;

  try {
    const res = await fetch(url, options);
    // Treat gateway errors or static host method rejection as recoverable tunnel drops
    if (res.status === 405 || res.status === 404 || res.status === 502 || res.status === 504 || res.status === 503) {
      throw new Error(`Endpoint response status ${res.status}`);
    }
    return res;
  } catch (err) {
    console.warn(`Request to ${url} failed, attempting endpoint recovery...`, err);
    if (isGithubPages) {
      const recovered = await autoDetectHub(true);
      if (recovered && getHubBase()) {
        url = getApiUrl(path);
        if (url) {
          const retryRes = await fetch(url, options);
          if (retryRes.status !== 405 && retryRes.status !== 502 && retryRes.status !== 504 && retryRes.status !== 503) {
            return retryRes;
          }
        }
      }
    }
    throw new Error("Unable to reach TV Hub server. Make sure TV Hub is running on your laptop or check your connection.");
  }
}'''

    if old_top in code:
        code = code.replace(old_top, new_top)
        print("Patched top getHubBase and safeFetchWithRetry")
    else:
        print("Warning: old_top not found directly, checking variations")

    # 2. Update autoDetectHub
    old_autodetect = '''async function autoDetectHub(forceRefresh = false) {
  const isGithubPages = window.location.hostname.includes("github.io");
  if (!isGithubPages) return true;

  // 1. Verify if existing cached HUB_BASE is actually online right now
  if (!forceRefresh) {
    let currentBase = localStorage.getItem("tvhub_backend_url") || HUB_BASE;
    if (currentBase) {
      const isAlive = await probeEndpoint(currentBase, 1500);
      if (isAlive) {
        HUB_BASE = currentBase.replace(/\\/+$/, "");
        console.log("Current Hub confirmed responsive:", HUB_BASE);
        return true;
      }
      console.warn("Cached Hub URL is offline or expired. Purging stale link:", currentBase);
      localStorage.removeItem("tvhub_backend_url");
      HUB_BASE = "";
    }
  } else {
    localStorage.removeItem("tvhub_backend_url");
    HUB_BASE = "";
  }

  // 2. Fetch fresh endpoint.json (direct + GitHub raw fallback)
  let endpointData = null;
  try {
    const res = await fetch("./endpoint.json?t=" + Date.now());
    if (res.ok) endpointData = await res.json();
  } catch (e) {}

  if (!endpointData) {
    try {
      const rawRes = await fetch("https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t=" + Date.now());
      if (rawRes.ok) endpointData = await rawRes.json();
    } catch (e) {}
  }

  if (endpointData) {
    // 2A. Probe Home Wi-Fi LAN direct connection first (0ms latency, maximum speed!)
    const localUrl = endpointData.local_url || `http://${endpointData.local_ip || window.location.hostname || "localhost"}:${endpointData.port || 8000}`;
    const localOk = await probeEndpoint(localUrl, 1200);
    if (localOk) {
      setHubBase(localUrl);
      console.log("Connected directly to Home TV Hub via Wi-Fi:", localUrl);
      return true;
    }

    // 2B. Probe active public tunnel
    if (endpointData.hub_url) {
      const tunnelOk = await probeEndpoint(endpointData.hub_url, 3000);
      if (tunnelOk) {
        setHubBase(endpointData.hub_url);
        console.log("Connected to Home TV Hub via Public Tunnel:", endpointData.hub_url);
        return true;
      }
      // If probe was slow, set tunnel URL anyway so background requests continue
      setHubBase(endpointData.hub_url);
      return true;
    }
  }

  return false;
}'''

    new_autodetect = '''function updateHubStatusBadge(isOnline, labelText = null) {
  const badge = document.getElementById("network-badge-text");
  if (!badge) return;
  if (!window.location.hostname.includes("github.io")) {
    badge.textContent = "Local Network";
    return;
  }
  const base = getHubBase();
  const label = labelText || (isOnline ? "Hub Linked" : (base ? "Hub Reconnecting..." : "Hub Offline"));
  const color = isOnline ? "var(--accent-cyan)" : (base ? "#f59e0b" : "#ef4444");
  badge.innerHTML = `<span style="color: ${color}; cursor: pointer;" title="Tap to configure TV Hub connection">🌐 GitHub Pages (${label})</span>`;
}

async function autoDetectHub(forceRefresh = false) {
  const isGithubPages = window.location.hostname.includes("github.io");
  if (!isGithubPages) {
    updateHubStatusBadge(true, "Local Network");
    return true;
  }

  // 1. Verify if existing cached HUB_BASE is actually online right now
  if (!forceRefresh) {
    let currentBase = localStorage.getItem("tvhub_backend_url") || HUB_BASE;
    if (currentBase && !currentBase.includes("github.io")) {
      const isAlive = await probeEndpoint(currentBase, 1800);
      if (isAlive) {
        HUB_BASE = currentBase.replace(/\\/+$/, "");
        console.log("Current Hub confirmed responsive:", HUB_BASE);
        updateHubStatusBadge(true, "Hub Linked");
        state.hubOnline = true;
        return true;
      }
    }
  }

  // 2. Fetch fresh endpoint.json (direct + GitHub raw fallback)
  let endpointData = null;
  try {
    const res = await fetch("./endpoint.json?t=" + Date.now());
    if (res.ok) endpointData = await res.json();
  } catch (e) {}

  if (!endpointData) {
    try {
      const rawRes = await fetch("https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t=" + Date.now());
      if (rawRes.ok) endpointData = await rawRes.json();
    } catch (e) {}
  }

  if (endpointData && endpointData.hub_url) {
    setHubBase(endpointData.hub_url);
    console.log("Connected to Home TV Hub via Public Tunnel:", endpointData.hub_url);
    updateHubStatusBadge(true, "Hub Linked");
    state.hubOnline = true;
    probeEndpoint(endpointData.hub_url, 3000).then(alive => {
      updateHubStatusBadge(alive, alive ? "Hub Linked" : "Hub Reconnecting...");
      state.hubOnline = alive;
    });
    return true;
  }

  updateHubStatusBadge(false, "Hub Offline");
  state.hubOnline = false;
  return false;
}'''

    if old_autodetect in code:
        code = code.replace(old_autodetect, new_autodetect)
        print("Patched autoDetectHub and updateHubStatusBadge")
    else:
        print("Warning: old_autodetect not found directly")

    # 3. Add Google Cast Web SDK & In-App Mobile Video Player logic
    web_cast_and_player_code = '''
// --- Google Cast Web SDK (In-Browser Casting for ANY Wi-Fi Network) ---
let gCastInitialized = false;
let gCastConnected = false;

window.__onGCastApiAvailable = function(isAvailable) {
  if (isAvailable) {
    initGoogleCastWebSdk();
  }
};

function initGoogleCastWebSdk() {
  if (gCastInitialized) return;
  try {
    cast.framework.CastContext.getInstance().setOptions({
      receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
      autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
    });
    gCastInitialized = true;
    console.log("Google Cast Web SDK initialized successfully");

    const context = cast.framework.CastContext.getInstance();
    context.addEventListener(
      cast.framework.CastContextEventType.CAST_STATE_CHANGED,
      function(event) {
        handleWebCastStateChange(event.castState);
      }
    );
    handleWebCastStateChange(context.getCastState());
  } catch (e) {
    console.warn("Google Cast SDK init notice:", e);
  }
}

function handleWebCastStateChange(castState) {
  const btnCast = document.getElementById("btn-web-cast");
  if (!btnCast) return;
  if (typeof cast !== "undefined" && cast.framework && castState === cast.framework.CastState.CONNECTED) {
    gCastConnected = true;
    btnCast.classList.add("active");
    btnCast.title = "Connected to TV via Web Cast (Tap to Disconnect / Change)";
  } else {
    gCastConnected = false;
    btnCast.classList.remove("active");
    btnCast.title = "Cast directly from Browser to any TV on this Wi-Fi";
  }
}

function requestWebCastSession() {
  if (typeof cast !== "undefined" && cast.framework) {
    const context = cast.framework.CastContext.getInstance();
    context.requestSession().then(
      () => {
        showToast("Connected to TV via Web Cast!");
        handleWebCastStateChange(context.getCastState());
      },
      (err) => {
        if (err !== "cancel") {
          console.warn("Web Cast session notice:", err);
        }
      }
    );
  } else {
    showToast("Web Cast initializing... Use Google Chrome on Wi-Fi for direct TV casting.");
  }
}

function isWebCastActive() {
  try {
    if (typeof cast !== "undefined" && cast.framework) {
      const state = cast.framework.CastContext.getInstance().getCastState();
      return state === cast.framework.CastState.CONNECTED;
    }
  } catch (e) {}
  return false;
}

function castViaWebCast(url, title = "Video Stream", poster = "") {
  try {
    const session = cast.framework.CastContext.getInstance().getCurrentSession();
    if (!session) return false;
    const isM3u8 = url.includes(".m3u8");
    const mimeType = isM3u8 ? "application/x-mpegurl" : "video/mp4";
    const mediaInfo = new chrome.cast.media.MediaInfo(url, mimeType);
    mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata();
    mediaInfo.metadata.title = title;
    if (poster) {
      mediaInfo.metadata.images = [{ url: poster }];
    }
    const request = new chrome.cast.media.LoadRequest(mediaInfo);
    session.loadMedia(request).then(
      () => {
        showToast(`Playing ${title} on TV via Web Cast!`);
        state.currentTitle = title;
        state.playbackState = "PLAYING";
        const barTitle = document.getElementById("bar-title");
        if (barTitle) barTitle.textContent = title;
        updatePlayPauseButton(true);
      },
      (err) => {
        console.error("Web Cast loadMedia failed:", err);
        showToast("Web Cast failed: " + err);
      }
    );
    return true;
  } catch (e) {
    console.error("castViaWebCast error:", e);
    return false;
  }
}

// --- In-App Mobile Video Player (Play channels directly on phone without TV) ---
let inAppHls = null;
let activeInAppChannel = null;

function openInAppPlayer(channel) {
  const modal = document.getElementById("modal-inapp-player");
  const video = document.getElementById("inapp-video");
  const title = document.getElementById("inapp-channel-name");
  if (!modal || !video) return;

  activeInAppChannel = channel;
  const streamUrl = (channel.sources && channel.sources[0]?.url) || channel.url || channel.stream_url;
  if (!streamUrl) {
    showToast("⚠️ Stream URL unavailable for this channel");
    return;
  }

  if (title) title.textContent = channel.name || channel.title || "Live Stream";
  modal.style.display = "flex";

  if (inAppHls) {
    try { inAppHls.destroy(); } catch (e) {}
    inAppHls = null;
  }

  const isM3u8 = streamUrl.includes(".m3u8");
  if (isM3u8 && typeof Hls !== "undefined" && Hls.isSupported()) {
    inAppHls = new Hls({ enableWorker: true, lowLatencyMode: true });
    inAppHls.loadSource(streamUrl);
    inAppHls.attachMedia(video);
    inAppHls.on(Hls.Events.MANIFEST_PARSED, () => {
      video.play().catch(() => {});
    });
    inAppHls.on(Hls.Events.ERROR, (event, data) => {
      if (data.fatal) {
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          inAppHls.startLoad();
        } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          inAppHls.recoverMediaError();
        } else {
          inAppHls.destroy();
        }
      }
    });
  } else {
    video.src = streamUrl;
    video.play().catch(() => {});
  }
}

function closeInAppPlayer() {
  const modal = document.getElementById("modal-inapp-player");
  const video = document.getElementById("inapp-video");
  if (video) {
    try { video.pause(); } catch (e) {}
    video.src = "";
  }
  if (inAppHls) {
    try { inAppHls.destroy(); } catch (e) {}
    inAppHls = null;
  }
  if (modal) modal.style.display = "none";
}
'''

    if "initGoogleCastWebSdk" not in code:
        code += web_cast_and_player_code
        print("Appended Google Cast Web SDK and In-App Player functions")

    # 4. Patch renderChannels to include phone button
    old_card_html = '''    card.innerHTML = `
      <div class="channel-logo-container">
        ${logoHtml}
        <span class="channel-card-glow"></span>
      </div>
      <div class="channel-name" title="${ch.name}">${ch.name}</div>
      <div class="channel-badge-row">
        <span class="channel-tag ${langClass}">${langLabel}</span>
        <span class="channel-tag tag-genre">${ch.genre || "Live"}</span>
        ${statusBadge}
        ${sourceBadge}
      </div>
    `;'''

    new_card_html = '''    card.innerHTML = `
      <div class="channel-logo-container">
        ${logoHtml}
        <span class="channel-card-glow"></span>
        <button class="channel-phone-play-btn" title="Watch on Phone" data-play-phone="${ch.id}">📱</button>
      </div>
      <div class="channel-name" title="${ch.name}">${ch.name}</div>
      <div class="channel-badge-row">
        <span class="channel-tag ${langClass}">${langLabel}</span>
        <span class="channel-tag tag-genre">${ch.genre || "Live"}</span>
        ${statusBadge}
        ${sourceBadge}
      </div>
    `;

    const phoneBtn = card.querySelector("[data-play-phone]");
    if (phoneBtn) {
      phoneBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        vibrate(20);
        openInAppPlayer(ch);
      });
    }'''

    if old_card_html in code:
        code = code.replace(old_card_html, new_card_html)
        print("Patched renderChannels card HTML and phone play button")
    else:
        print("Warning: old_card_html not found")

    # 5. Patch castChannel to support Web Cast and fallback to In-App player
    old_cast_channel = '''async function castChannel(channel) {
  if (castAbortController) {
    try { castAbortController.abort(); } catch (e) {}
  }
  castAbortController = new AbortController();
  const signal = castAbortController.signal;

  vibrate(35);
  showToast(`Casting ${channel.name} to TV...`);
  
  // If TV is currently in standby, send WoL first
  if (!state.tvOnline) {
    sendWakeOnLan();
  }

  try {
    const devParam = state.currentTvId ? `?device_id=${encodeURIComponent(state.currentTvId)}` : "";
    const res = await fetch(getApiUrl(`/api/iptv/cast/${channel.id}${devParam}`), { method: "POST", signal });
    if (signal.aborted) return;
    const data = await res.json();
    if (signal.aborted) return;
    if (data.status === "superseded") {
      console.log(`Cast for ${channel.name} was superseded by a newer channel command`);
      return;
    }
    if (data.status === "waking" || data.tv_online === false) {
      showToast("⚡ TV is in Standby! Sent Wake packet, please power on TV.");
      updateHardwareStatus({
        tv_online: false,
        state: "STANDBY",
        status_text: `${state.currentTvName} is in Standby (Turn TV on to play)`
      });
    } else if (res.ok) {
      state.currentTitle = channel.name;
      const sCount = (channel.sources && channel.sources.length) ? channel.sources.length : (channel.source_count || 1);
      const sBadge = sCount > 1 ? " (S1)" : "";
      document.getElementById("bar-title").textContent = `${channel.name}${sBadge}`;
      showToast(`Playing ${channel.name} on TV!`);
    }
  } catch (e) {
    if (e.name === "AbortError" || signal.aborted) {
      return; // Newer channel tap took priority
    }
    console.error("Cast channel failed:", e);
    showToast("Failed to cast channel");
  }
}'''

    new_cast_channel = '''async function castChannel(channel) {
  if (castAbortController) {
    try { castAbortController.abort(); } catch (e) {}
  }
  castAbortController = new AbortController();
  const signal = castAbortController.signal;

  vibrate(35);

  // Check 1: Direct in-browser Google Cast session (works on ANY Wi-Fi network without laptop)
  if (isWebCastActive()) {
    showToast(`Casting ${channel.name} to TV via Web Cast...`);
    const streamUrl = (channel.sources && channel.sources[0]?.url) || channel.url;
    castViaWebCast(streamUrl, channel.name, channel.logo || "");
    return;
  }

  // Check 2: If hub is offline on GitHub Pages, fallback directly to in-app phone player
  const isGithubPages = window.location.hostname.includes("github.io");
  if (isGithubPages && (!getHubBase() || state.hubOnline === false)) {
    showToast(`TV Hub offline. Playing ${channel.name} on device`);
    openInAppPlayer(channel);
    return;
  }

  showToast(`Casting ${channel.name} to TV...`);
  if (!state.tvOnline) {
    sendWakeOnLan();
  }

  try {
    const devParam = state.currentTvId ? `?device_id=${encodeURIComponent(state.currentTvId)}` : "";
    const res = await safeFetchWithRetry(`/api/iptv/cast/${channel.id}${devParam}`, { method: "POST", signal });
    if (signal.aborted) return;
    const data = await res.json();
    if (signal.aborted) return;
    if (data.status === "superseded") return;
    if (data.status === "waking" || data.tv_online === false) {
      showToast("⚡ TV is in Standby! Sent Wake packet, please power on TV.");
      updateHardwareStatus({
        tv_online: false,
        state: "STANDBY",
        status_text: `${state.currentTvName} is in Standby (Turn TV on to play)`
      });
    } else if (res.ok) {
      state.currentTitle = channel.name;
      const sCount = (channel.sources && channel.sources.length) ? channel.sources.length : (channel.source_count || 1);
      const sBadge = sCount > 1 ? " (S1)" : "";
      const barTitle = document.getElementById("bar-title");
      if (barTitle) barTitle.textContent = `${channel.name}${sBadge}`;
      showToast(`Playing ${channel.name} on TV!`);
    }
  } catch (e) {
    if (e.name === "AbortError" || signal.aborted) return;
    console.error("Cast channel failed:", e);
    // If backend failed, automatically open in-app player so stream is NEVER lost
    showToast(`TV Hub unreachable. Playing ${channel.name} on device`);
    openInAppPlayer(channel);
  }
}'''

    if old_cast_channel in code:
        code = code.replace(old_cast_channel, new_cast_channel)
        print("Patched castChannel with Web Cast and In-App fallback")
    else:
        print("Warning: old_cast_channel not found directly")

    # 6. Replace raw fetch(getApiUrl(...)) in sendPlaybackAction & remote keys
    code = code.replace(
        'await fetch(getApiUrl("/api/remote/key"), {',
        'await safeFetchWithRetry("/api/remote/key", {'
    )
    code = code.replace(
        'const res = await fetch(getApiUrl("/api/playback/action"), {',
        'const res = await safeFetchWithRetry("/api/playback/action", {'
    )
    code = code.replace(
        'await fetch(getApiUrl("/api/playback/volume"), {',
        'await safeFetchWithRetry("/api/playback/volume", {'
    )
    code = code.replace(
        'const res = await fetch(getApiUrl("/api/devices/select"), {',
        'const res = await safeFetchWithRetry("/api/devices/select", {'
    )
    code = code.replace(
        'await fetch(getApiUrl("/api/devices/scan"), { method: "POST" });',
        'await safeFetchWithRetry("/api/devices/scan", { method: "POST" });'
    )
    code = code.replace(
        'await fetch(getApiUrl("/api/tv/wake"), { method: "POST" });',
        'await safeFetchWithRetry("/api/tv/wake", { method: "POST" });'
    )

    # 7. Wire up buttons in DOMContentLoaded
    old_init = '''  initModals();
  connectWebSocket();
  initSportsAggregator();
  initYouTubeSearch();'''

    new_init = '''  initModals();
  connectWebSocket();
  initSportsAggregator();
  initYouTubeSearch();

  // Web Cast & In-App Player listeners
  document.getElementById("btn-web-cast")?.addEventListener("click", () => {
    vibrate(20);
    requestWebCastSession();
  });
  document.getElementById("btn-close-inapp-player")?.addEventListener("click", () => {
    vibrate(15);
    closeInAppPlayer();
  });
  document.getElementById("btn-inapp-switch-tv")?.addEventListener("click", () => {
    vibrate(25);
    if (activeInAppChannel) {
      closeInAppPlayer();
      castChannel(activeInAppChannel);
    }
  });'''

    if old_init in code:
        code = code.replace(old_init, new_init)
        print("Patched DOMContentLoaded with Web Cast & In-App Player listeners")

    p.write_text(code, encoding="utf-8")
    print("static/app.js patched successfully")

if __name__ == "__main__":
    patch_app_js()
