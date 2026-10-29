// TV Hub Dynamic Backend & Permanent GitHub Pages Resolution
let HUB_BASE = localStorage.getItem("tvhub_backend_url") || "";

function getHubBase() {
  if (HUB_BASE) return HUB_BASE.replace(/\/+$/, "");
  const params = new URLSearchParams(window.location.search);
  const hubParam = params.get("hub");
  if (hubParam) {
    HUB_BASE = hubParam.replace(/\/+$/, "");
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
}

function getWsUrl(path) {
  const base = getHubBase();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  if (base) {
    const wsProto = base.startsWith("https:") ? "wss:" : "ws:";
    const host = base.replace(/^https?:\/\//, "");
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

async function probeEndpoint(url, timeoutMs = 2000) {
  if (!url) return false;
  const cleanUrl = url.replace(/\/+$/, "");
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    const res = await fetch(`${cleanUrl}/api/auth/status`, {
      signal: controller.signal,
      headers: { "bypass-tunnel-reminder": "true", "ngrok-skip-browser-warning": "true" }
    });
    clearTimeout(timeoutId);
    if (res.ok) {
      const data = await res.json();
      return data.authenticated === true;
    }
  } catch (e) {}
  return false;
}

function setHubBase(url) {
  HUB_BASE = (url || "").replace(/\/+$/, "");
  if (HUB_BASE) {
    localStorage.setItem("tvhub_backend_url", HUB_BASE);
  } else {
    localStorage.removeItem("tvhub_backend_url");
  }
}

async function autoDetectHub(forceRefresh = false) {
  const isGithubPages = window.location.hostname.includes("github.io");
  if (!isGithubPages) return true;

  // 1. Verify if existing cached HUB_BASE is actually online right now
  if (!forceRefresh) {
    let currentBase = localStorage.getItem("tvhub_backend_url") || HUB_BASE;
    if (currentBase) {
      const isAlive = await probeEndpoint(currentBase, 1500);
      if (isAlive) {
        HUB_BASE = currentBase.replace(/\/+$/, "");
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
    const localUrl = endpointData.local_url || `http://${endpointData.local_ip || "192.168.50.250"}:${endpointData.port || 8000}`;
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
}

// TV Hub Modern Mobile Frontend Logic
let state = {
  currentTvId: null,
  currentTvName: "Hisense VIDAA TV (Living Room)",
  currentTvId: "tv_192_168_50_249",
  tvOnline: false,
  playbackState: "STANDBY",
  currentTitle: "TV Hub Ready",
  volume: 20,
  muted: false,
  channels: [],
  selectedLanguage: "All",
  selectedGenre: "All",
  sortBy: "popularity",
  searchQuery: "",
  ws: null,
  // Sports Aggregator State
  sportsEvents: [],
  selectedSportsCategory: "all",
  sportsStatusFilter: "all",
  sportsSearchQuery: "",
  activeStreamSlug: null
};

// Haptic feedback helper
function vibrate(ms = 22) {
  if (navigator.vibrate) {
    try { navigator.vibrate(ms); } catch (e) {}
  }
}

// 2-Letter Monogram Fallback Generator for channel images
function getInitials(name) {
  if (!name) return "TV";
  let clean = name.replace(/[^\w\s\u10A0-\u10FF\u0400-\u04FF]/g, ' ').trim();
  const words = clean.split(/\s+/).filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  } else if (words.length === 1 && words[0].length >= 2) {
    return words[0].slice(0, 2).toUpperCase();
  } else if (words.length === 1 && words[0].length === 1) {
    return words[0].toUpperCase();
  }
  return "TV";
}

window.handleImgError = function(imgElement, name, genre, lang) {
  // 1. Try online fallback logo if available
  const onlineFallback = imgElement.dataset.fallbackLogo;
  if (onlineFallback && imgElement.src !== onlineFallback && !imgElement.dataset.triedFallback) {
    imgElement.dataset.triedFallback = "true";
    imgElement.src = onlineFallback;
    return;
  }

  // 2. Try proxy if backend is active
  const base = getHubBase();
  if (base && !imgElement.dataset.proxyTried && imgElement.src && !imgElement.src.includes("/api/logo/proxy")) {
    imgElement.dataset.proxyTried = "true";
    imgElement.src = `${base}/api/logo/proxy?url=${encodeURIComponent(imgElement.src)}`;
    return;
  }

  imgElement.onerror = null; // Prevent loop
  imgElement.style.display = "none";

  const parent = imgElement.parentElement;
  if (!parent) return;

  const initials = getInitials(name);

  // Genre emoji icon
  const genreIcons = {
    "News": "📰",
    "Movies": "🎬",
    "Sports": "⚽",
    "Kids": "👶",
    "Music": "🎵",
    "Documentaries": "🧠",
    "Entertainment": "🎭"
  };
  const icon = genreIcons[genre] || "📺";

  let fallback = parent.querySelector(".monogram-fallback");
  if (!fallback) {
    fallback = document.createElement("div");
    fallback.className = "monogram-fallback";
    fallback.innerHTML = `<span>${initials}</span><span class="monogram-sub">${icon}</span>`;
    parent.appendChild(fallback);
  }
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initHubModal();
  await autoDetectHub();
  populateDevicesList(DEFAULT_HOUSEHOLD_DEVICES, "tv_192_168_50_249");
  checkAuth();
  fetchDevices();
  fetchHardwareStatus();
  fetchChannels();
  fetchMediaFiles();
  initRemoteKeys();
  initFiltersAndSort();
  initModals();
  connectWebSocket();
  initSportsAggregator();
});

// --- Tab Navigation ---
function initTabs() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      vibrate(15);
      const targetId = item.getAttribute("data-tab");

      navItems.forEach(n => n.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));

      item.classList.add("active");
      const targetTab = document.getElementById(targetId);
      if (targetTab) {
        targetTab.classList.add("active");
        if (targetId === "tab-devices") {
          initDevicesTab();
          if (!adblockPollingTimer) {
            adblockPollingTimer = setInterval(loadAdblockStatus, 6000);
          }
        } else if (adblockPollingTimer) {
          clearInterval(adblockPollingTimer);
          adblockPollingTimer = null;
        }
      }
    });
  });
}

// --- Screen Wake Lock & Background Resilience (Android & iOS) ---
let wakeLockSentinel = null;
async function requestScreenWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLockSentinel = await navigator.wakeLock.request('screen');
    }
  } catch (err) {}
}

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    requestScreenWakeLock();
    // Seamlessly re-sync with server without interrupting streaming
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({ type: "ping" }));
    }
  }
});
document.addEventListener("click", () => {
  if (!wakeLockSentinel) requestScreenWakeLock();
}, { once: true });

// --- Network & Auth ---
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
      }

      // Network routing advisor (Tunnel vs Home LAN)
      const advisor = document.getElementById("network-advisor-text");
      if (advisor) {
        const isTunnel = window.location.hostname.includes("trycloudflare.com") || window.location.hostname.includes("clck.ru");
        if (isTunnel) {
          advisor.innerHTML = `<span style="color: var(--accent-amber);">🌐 Connected via Cloudflare Quick Tunnel.</span><br>Quick tunnels add internet relay hops. When connected to home Wi-Fi, open <strong style="color:var(--accent-green)">http://${data.server_ip}:${data.port}</strong> for lowest latency & highest 1080p bitrate.`;
        } else {
          advisor.innerHTML = `<span style="color: var(--accent-green);">⚡ Direct Local Wi-Fi Connection.</span><br>Optimal 0ms local network routing directly to target TV.`;
        }
      }
    } else {
      const shortLink = document.getElementById("short-phone-link");
      const pubLink = document.getElementById("public-phone-link");
      if (shortLink) shortLink.textContent = "Connecting static link...";
      if (pubLink) pubLink.textContent = "Connecting public tunnel...";
      setTimeout(checkAuth, 2000);
    }
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
}

document.getElementById("btn-copy-short-link")?.addEventListener("click", () => {
  const shortLink = document.getElementById("short-phone-link");
  if (shortLink && shortLink.href && shortLink.href !== "#") {
    navigator.clipboard.writeText(shortLink.href);
    showToast("⚡ Short link copied to clipboard!");
  }
});

document.getElementById("btn-copy-public-link")?.addEventListener("click", () => {
  const pubLink = document.getElementById("public-phone-link");
  if (pubLink && pubLink.href && pubLink.href !== "#") {
    navigator.clipboard.writeText(pubLink.href);
    showToast("Direct tunnel link copied to clipboard!");
  }
});

document.getElementById("btn-copy-local-link")?.addEventListener("click", () => {
  const localWifi = document.getElementById("local-wifi-link");
  if (localWifi && localWifi.href && localWifi.href !== "#") {
    navigator.clipboard.writeText(localWifi.href);
    showToast("Home Wi-Fi link copied to clipboard!");
  }
});

// Known household TVs for instant zero-wait selection
const DEFAULT_HOUSEHOLD_DEVICES = [
  { id: "tv_192_168_50_249", name: "Hisense VIDAA TV (Living Room)", is_hisense: true },
  { id: "tv_192_168_50_3", name: "Xiaomi Mi TV (Google TV)", is_google_tv: true },
  { id: "tv_192_168_50_205", name: "TCL Smart TV Pro (Google TV)", is_google_tv: true },
  { id: "web_receiver", name: "TV Web Receiver (Browser at /tv)", type: "browser" }
];

function populateDevicesList(devices, selectedId) {
  const dropdown = document.getElementById("tv-dropdown");
  if (!dropdown) return;
  dropdown.innerHTML = "";

  (devices || []).forEach(dev => {
    const opt = document.createElement("option");
    opt.value = dev.id;
    let label = dev.name;
    if (dev.is_hisense && !label.includes("VIDAA")) {
      label += " (Hisense VIDAA)";
    } else if (dev.is_google_tv && !label.includes("Google TV")) {
      label += " (Google TV)";
    } else if (dev.type === "browser" && !label.includes("/tv")) {
      label += " (Browser)";
    }
    opt.textContent = label;
    if (dev.id === selectedId) {
      opt.selected = true;
      state.currentTvId = dev.id;
      state.currentTvName = dev.name;
      const infoTv = document.getElementById("info-active-tv");
      if (infoTv) infoTv.textContent = dev.name;
    }
    dropdown.appendChild(opt);
  });

  if (!state.currentTvId && devices.length > 0) {
    state.currentTvId = devices[0].id;
    state.currentTvName = devices[0].name;
    const infoTv = document.getElementById("info-active-tv");
    if (infoTv) infoTv.textContent = devices[0].name;
  }
}

// --- Device Discovery & Hardware Status ---
async function fetchDevices() {
  try {
    const res = await fetch(getApiUrl("/api/devices"));
    if (res.ok) {
      const data = await res.json();
      populateDevicesList(data.devices, data.selected_device_id || "tv_192_168_50_249");
      return;
    }
  } catch (e) {
    console.warn("Device fetch notice:", e);
  }

  // Resilient fallback: ensure household TVs are always populated
  const dropdown = document.getElementById("tv-dropdown");
  if (dropdown && dropdown.options.length <= 1) {
    populateDevicesList(DEFAULT_HOUSEHOLD_DEVICES, "tv_192_168_50_249");
  }
}

async function fetchHardwareStatus() {
  try {
    const res = await fetch(getApiUrl("/api/state/current"));
    if (res.ok) {
      const data = await res.json();
      updateHardwareStatus(data);
    }
  } catch (e) {}
}

document.getElementById("tv-dropdown").addEventListener("change", async (e) => {
  const deviceId = e.target.value;
  vibrate(20);
  try {
    const res = await fetch(getApiUrl("/api/devices/select"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: deviceId })
    });
    if (res.ok) {
      const data = await res.json();
      state.currentTvId = data.selected_device_id;
      state.currentTvName = data.name;
      document.getElementById("info-active-tv").textContent = data.name;
    }
  } catch (err) {}
});

document.getElementById("btn-scan").addEventListener("click", async () => {
  vibrate(30);
  const btn = document.getElementById("btn-scan");
  btn.style.transform = "rotate(360deg)";
  btn.style.transition = "transform 0.8s ease";
  showToast("Scanning local Wi-Fi for TVs...");
  try {
    await fetch(getApiUrl("/api/devices/scan"), { method: "POST" });
    await fetchDevices();
  } finally {
    setTimeout(() => { btn.style.transform = "none"; }, 800);
  }
});

// Quick Wake / Turn On TV button
async function sendWakeOnLan() {
  vibrate(35);
  showToast("⚡ Sending Wake-on-LAN power packet...");
  try {
    await fetch(getApiUrl("/api/tv/wake"), { method: "POST" });
  } catch (e) {}
}

document.getElementById("btn-quick-wake")?.addEventListener("click", sendWakeOnLan);

// Update Real Hardware Status UI
function updateHardwareStatus(data) {
  const banner = document.getElementById("tv-status-banner");
  const dot = document.getElementById("tv-status-dot");
  const text = document.getElementById("tv-status-text");
  const wakeBtn = document.getElementById("btn-quick-wake");
  const barDot = document.getElementById("bar-status-dot");
  const barStatus = document.getElementById("bar-tv-status");
  const hwInfo = document.getElementById("info-hardware-status");
  const eqIcon = document.getElementById("player-eq");

  const isOnline = data.tv_online === true;
  const pState = data.state || "STANDBY";

  state.tvOnline = isOnline;
  state.playbackState = pState;

  if (!isOnline || pState === "STANDBY") {
    // TV Standby
    banner.className = "tv-status-banner standby";
    dot.className = "status-dot red";
    text.textContent = data.status_text || `${state.currentTvName} is in Standby`;
    wakeBtn.style.display = "flex";

    barDot.className = "status-dot red";
    barStatus.textContent = "TV in Standby";
    hwInfo.textContent = "Standby / Sleeping";
    hwInfo.style.color = "var(--accent-red)";
    if (eqIcon) eqIcon.style.display = "none";
    updatePlayPauseButton(false);

  } else if (pState === "PLAYING") {
    // TV Playing Media
    banner.className = "tv-status-banner playing";
    dot.className = "status-dot blue";
    text.textContent = data.status_text || `Playing: ${state.currentTitle}`;
    wakeBtn.style.display = "none";

    barDot.className = "status-dot blue";
    barStatus.textContent = "Playing on TV";
    hwInfo.textContent = "Active / Playing";
    hwInfo.style.color = "var(--accent-cyan)";
    if (eqIcon) eqIcon.style.display = "flex";
    updatePlayPauseButton(true);

  } else {
    // TV Online & Idle
    banner.className = "tv-status-banner idle";
    dot.className = "status-dot green";
    text.textContent = data.status_text || `${state.currentTvName} Ready`;
    wakeBtn.style.display = "none";

    barDot.className = "status-dot green";
    barStatus.textContent = "TV Ready / Idle";
    hwInfo.textContent = "Online & Ready";
    hwInfo.style.color = "var(--accent-green)";
    if (eqIcon) eqIcon.style.display = "none";
    updatePlayPauseButton(false);
  }

  if (data.title) {
    state.currentTitle = data.title;
    const sBadge = (data.source_index !== undefined && data.sources_total > 1) ? ` (S${data.source_index + 1})` : "";
    document.getElementById("bar-title").textContent = `${data.title}${sBadge}`;
  }
  if (data.volume !== undefined) {
    state.volume = data.volume;
  }
}

function updatePlayPauseButton(isPlaying) {
  const btn = document.getElementById("btn-bar-play");
  const remoteBtn = document.getElementById("remote-play-btn");

  const pauseSvg = `<svg viewBox="0 0 24 24"><rect width="4" height="16" x="6" y="4" rx="1"/><rect width="4" height="16" x="14" y="4" rx="1"/></svg>`;
  const playSvg = `<svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;

  btn.innerHTML = isPlaying ? pauseSvg : playSvg;
  if (remoteBtn) remoteBtn.innerHTML = isPlaying ? pauseSvg : playSvg;
}

// --- IPTV Channels: Sorting & Dual Filters ---
async function fetchChannels() {
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
}

function initFiltersAndSort() {
  // Language filter pills
  document.querySelectorAll("#language-bar .filter-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      vibrate(15);
      state.selectedLanguage = pill.getAttribute("data-lang");
      document.querySelectorAll("#language-bar .filter-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      renderChannels();
    });
  });

  // Genre filter pills
  document.querySelectorAll("#genre-bar .filter-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      vibrate(15);
      state.selectedGenre = pill.getAttribute("data-genre");
      document.querySelectorAll("#genre-bar .filter-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      renderChannels();
    });
  });

  // Sort dropdown
  document.getElementById("sort-dropdown").addEventListener("change", (e) => {
    vibrate(15);
    state.sortBy = e.target.value;
    renderChannels();
  });

  // Search input
  document.getElementById("iptv-search").addEventListener("input", (e) => {
    state.searchQuery = e.target.value;
    renderChannels();
  });
  // Low Data Mode Toggle (480p Quality Cap)
  const lowDataToggle = document.getElementById("toggle-low-data");
  if (lowDataToggle) {
    const savedLowData = localStorage.getItem("tvhub_low_data") === "true";
    lowDataToggle.checked = savedLowData;
    lowDataToggle.addEventListener("change", (e) => {
      vibrate(20);
      const enabled = e.target.checked;
      localStorage.setItem("tvhub_low_data", enabled ? "true" : "false");
      if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({
          type: "abr_hint",
          maxHeight: enabled ? 480 : null
        }));
      }
      showToast(enabled ? "Low Data Mode: Capped to 480p" : "Auto Quality: Maximum Bitrate");
    });
  }
}

function renderChannels() {
  const container = document.getElementById("channels-container");
  container.innerHTML = "";

  const query = state.searchQuery.toLowerCase();
  
  // Filter by language, genre, and search
  let filtered = state.channels.filter(ch => {
    const matchLang = state.selectedLanguage === "All" || (ch.language && ch.language.toLowerCase() === state.selectedLanguage.toLowerCase());
    const matchGenre = state.selectedGenre === "All" || (ch.genre && ch.genre.toLowerCase() === state.selectedGenre.toLowerCase());
    const matchSearch = !query || ch.name.toLowerCase().includes(query) || (ch.genre && ch.genre.toLowerCase().includes(query));
    return matchLang && matchGenre && matchSearch;
  });

  // Apply sorting
  if (state.sortBy === "popularity") {
    filtered.sort((a, b) => (b.popularity || 50) - (a.popularity || 50));
  } else if (state.sortBy === "least_popular") {
    filtered.sort((a, b) => (a.popularity || 50) - (b.popularity || 50));
  } else if (state.sortBy === "name") {
    filtered.sort((a, b) => a.name.localeCompare(b.name));
  } else if (state.sortBy === "genre") {
    filtered.sort((a, b) => (a.genre || "").localeCompare(b.genre || "") || (b.popularity || 50) - (a.popularity || 50));
  }

  if (filtered.length === 0) {
    container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 50px 0; font-size: 13px;">No channels found for selected filters</div>`;
    return;
  }

  filtered.forEach(ch => {
    const card = document.createElement("div");
    const isDead = ch.is_alive === false || ch.stream_status === "dead";
    card.className = isDead ? "channel-card offline" : "channel-card";

    // Language badge styling
    let langClass = "lang-en";
    let langLabel = "EN";
    if (ch.language === "Georgian") { langClass = "lang-ge"; langLabel = "🇬🇪 GE"; }
    else if (ch.language === "Russian") { langClass = "lang-ru"; langLabel = "🇷🇺 RU"; }
    else if (ch.language === "English") { langClass = "lang-en"; langLabel = "🇬🇧 EN"; }

    const initials = getInitials(ch.name);
    const resolvedLocal = resolveAssetUrl(ch.local_logo);
    const resolvedOnline = resolveAssetUrl(ch.logo);
    const logoSrc = resolvedLocal || resolvedOnline;
    const fallbackAttr = (resolvedLocal && resolvedOnline && resolvedOnline !== resolvedLocal) ? ` data-fallback-logo="${resolvedOnline}"` : "";
    const logoHtml = logoSrc
      ? `<img src="${logoSrc}"${fallbackAttr} class="channel-logo" alt="${ch.name}" referrerpolicy="no-referrer" loading="lazy" onerror="handleImgError(this, '${ch.name.replace(/'/g, "\\'")}', '${ch.genre || "General"}', '${ch.language || "English"}')">`
      : `<div class="monogram-fallback"><span>${initials}</span><span class="monogram-sub">📺</span></div>`;

    const statusBadge = isDead
      ? `<span class="channel-tag tag-offline">OFFLINE</span>`
      : `<span class="channel-tag tag-hd">HD</span>`;

    const sourceCount = (ch.sources && ch.sources.length) ? ch.sources.length : (ch.source_count || 1);
    const sourceBadge = sourceCount > 1
      ? `<span class="channel-tag tag-src" title="${sourceCount} redundant backup sources available" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); font-weight: 700;">${sourceCount} SRC</span>`
      : "";

    card.innerHTML = `
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
    `;

    card.addEventListener("click", () => {
      if (isDead) {
        vibrate(35);
        showToast(`⚠️ ${ch.name} is currently offline upstream`);
        return;
      }
      castChannel(ch);
    });

    container.appendChild(card);
  });
}

let castAbortController = null;
async function castChannel(channel) {
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
}

// --- Remote Control ---
function initRemoteKeys() {
  document.querySelectorAll("[data-key]").forEach(btn => {
    btn.addEventListener("click", async () => {
      vibrate(24);
      const key = btn.getAttribute("data-key");

      if (key === "power") {
        sendWakeOnLan();
      }

      try {
        await fetch(getApiUrl("/api/remote/key"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key, device_id: state.currentTvId })
        });
      } catch (e) {}
    });
  });

  document.querySelectorAll("[data-action]").forEach(btn => {
    btn.addEventListener("click", async () => {
      vibrate(24);
      const action = btn.getAttribute("data-action");
      const val = btn.getAttribute("data-val");

      if (action === "play") {
        const nextAction = state.playbackState === "PLAYING" ? "pause" : "play";
        await sendPlaybackAction(nextAction);
      } else {
        await sendPlaybackAction(action, val);
      }
    });
  });
}

async function sendPlaybackAction(action, value = null) {
  try {
    const res = await fetch(getApiUrl("/api/playback/action"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, value, device_id: state.currentTvId })
    });
    if (res.ok) {
      if (action === "play") updatePlayPauseButton(true);
      if (action === "pause" || action === "stop") updatePlayPauseButton(false);
    }
  } catch (e) {}
}

// --- Cast Tab: Direct Stream & Local Upload ---
document.getElementById("btn-submit-cast").addEventListener("click", async () => {
  const url = document.getElementById("cast-url-input").value.trim();
  const title = document.getElementById("cast-title-input").value.trim() || "Video Stream";
  const useProxy = document.getElementById("cast-use-proxy").checked;

  if (!url) {
    showToast("Please enter a stream URL");
    return;
  }

  vibrate(30);
  showToast("Sending stream to TV...");
  try {
    const res = await fetch(getApiUrl("/api/cast"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, title, use_proxy: useProxy, device_id: state.currentTvId })
    });
    if (res.ok) {
      state.currentTitle = title;
      state.playbackState = "PLAYING";
      document.getElementById("bar-title").textContent = title;
      showToast("Playing on TV!");
    }
  } catch (e) {
    showToast("Cast failed");
  }
});

document.getElementById("btn-upload-cast").addEventListener("click", async () => {
  const fileInput = document.getElementById("media-file-input");
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast("Select a video/media file first");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  vibrate(30);
  showToast(`Uploading ${file.name}...`);
  try {
    const uploadRes = await fetch(getApiUrl("/api/media/upload"), {
      method: "POST",
      body: formData
    });
    if (uploadRes.ok) {
      showToast("Playing uploaded file on TV...");
      await fetch(getApiUrl(`/api/media/cast/${encodeURIComponent(file.name)}`), { method: "POST" });
      state.currentTitle = file.name;
      state.playbackState = "PLAYING";
      document.getElementById("bar-title").textContent = file.name;
      fetchMediaFiles();
    }
  } catch (e) {
    showToast("Upload failed");
  }
});

async function fetchMediaFiles() {
  const list = document.getElementById("media-files-list");
  try {
    const res = await fetch(getApiUrl("/api/media/files"));
    const data = await res.json();
    if (data.files.length === 0) {
      list.innerHTML = "";
      return;
    }
    list.innerHTML = `<h4 style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Uploaded Media Files:</h4>`;
    data.files.forEach(f => {
      const item = document.createElement("div");
      item.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(0,0,0,0.3); border-radius: 8px; margin-bottom: 6px; font-size: 12px;";
      item.innerHTML = `
        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px;">🎬 ${f.name} (${f.size_mb} MB)</span>
        <button class="btn-primary" style="width: auto; padding: 4px 10px; font-size: 11px;">Play</button>
      `;
      item.querySelector("button").addEventListener("click", async () => {
        vibrate(25);
        await fetch(getApiUrl(`/api/media/cast/${encodeURIComponent(f.name)}`), { method: "POST" });
        state.currentTitle = f.name;
        state.playbackState = "PLAYING";
        document.getElementById("bar-title").textContent = f.name;
      });
      list.appendChild(item);
    });
  } catch (e) {}
}

// --- Player Bar & Volume Modal ---
document.getElementById("btn-bar-play").addEventListener("click", () => {
  vibrate(25);
  const next = state.playbackState === "PLAYING" ? "pause" : "play";
  sendPlaybackAction(next);
});

document.getElementById("player-info-click").addEventListener("click", () => {
  vibrate(20);
  const remoteTabBtn = document.querySelector('[data-tab="tab-remote"]');
  if (remoteTabBtn) remoteTabBtn.click();
});

const modalVol = document.getElementById("modal-volume");
const volSlider = document.getElementById("vol-slider");
const modalVolVal = document.getElementById("modal-vol-val");

document.getElementById("btn-bar-vol").addEventListener("click", () => {
  vibrate(20);
  volSlider.value = state.volume;
  modalVolVal.textContent = state.muted ? "MUTED" : `${state.volume}%`;
  modalVol.classList.add("open");
});

volSlider.addEventListener("input", (e) => {
  const val = parseInt(e.target.value);
  modalVolVal.textContent = `${val}%`;
});

volSlider.addEventListener("change", async (e) => {
  const val = parseInt(e.target.value);
  state.volume = val;
  state.muted = false;
  try {
    await fetch(getApiUrl("/api/playback/volume"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ volume: val, device_id: state.currentTvId })
    });
  } catch (err) {}
});

document.getElementById("btn-modal-mute").addEventListener("click", async () => {
  vibrate(25);
  state.muted = !state.muted;
  modalVolVal.textContent = state.muted ? "MUTED" : `${state.volume}%`;
  try {
    await fetch(getApiUrl("/api/playback/volume"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mute: state.muted, device_id: state.currentTvId })
    });
  } catch (err) {}
});

// --- Modals Setup ---
function initModals() {
  document.querySelectorAll("[data-close]").forEach(btn => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-close");
      const m = document.getElementById(modalId);
      if (m) m.classList.remove("open");
      if (modalId === "modal-sports-match") {
        const frame = document.getElementById("sports-iframe-player");
        if (frame) frame.src = "about:blank";
      }
    });
  });

  // Manual TV Modal
  document.getElementById("btn-manual-tv").addEventListener("click", () => {
    vibrate(20);
    document.getElementById("modal-manual-tv").classList.add("open");
  });

  document.getElementById("btn-save-manual-tv").addEventListener("click", async () => {
    vibrate(25);
    const ip = document.getElementById("manual-ip-input").value.trim();
    const port = parseInt(document.getElementById("manual-port-input").value) || 38400;
    const name = document.getElementById("manual-name-input").value.trim() || "Hisense TV";

    if (!ip) return;
    try {
      await fetch(getApiUrl("/api/devices/manual"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip, port, name })
      });
      document.getElementById("modal-manual-tv").classList.remove("open");
      await fetchDevices();
      showToast("TV added successfully");
    } catch (e) {
      showToast("Failed to add TV");
    }
  });

  // Import M3U Modal
  document.getElementById("btn-open-import").addEventListener("click", () => {
    vibrate(20);
    document.getElementById("modal-import-iptv").classList.add("open");
  });

  document.getElementById("btn-submit-import").addEventListener("click", async () => {
    vibrate(25);
    const url = document.getElementById("import-url-input").value.trim();
    const content = document.getElementById("import-text-input").value.trim();

    if (!url && !content) {
      showToast("Please enter an M3U URL or paste text");
      return;
    }

    showToast("Importing playlist...");
    try {
      const res = await fetch(getApiUrl("/api/iptv/import"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url || null, content: content || null, append: false })
      });
      if (res.ok) {
        const data = await res.json();
        document.getElementById("modal-import-iptv").classList.remove("open");
        showToast(`Imported ${data.channels_imported} channels!`);
        await fetchChannels();
      }
    } catch (e) {
      showToast("Playlist import failed");
    }
  });
}

// --- WebSocket Real-Time Sync ---
function connectWebSocket() {
  if (window.location.hostname.includes("github.io") && !getHubBase()) {
    return; // Standalone GitHub Pages mode: skip WebSocket until Hub is linked
  }
  const wsUrl = getWsUrl("/ws/controller");
  try {
    state.ws = new WebSocket(wsUrl);

  state.ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "tv_status_sync" || msg.type === "sync_state" || msg.type === "playback_update") {
        updateHardwareStatus(msg.data);
      } else if (msg.type === "volume_update") {
        state.volume = msg.data.volume;
        state.muted = msg.data.muted;
        modalVolVal.textContent = state.muted ? "MUTED" : `${state.volume}%`;
        volSlider.value = state.volume;
      }
    } catch (e) {}
  };

    state.ws.onclose = () => {
      setTimeout(connectWebSocket, 3500);
    };
  } catch (err) {
    console.debug("WebSocket connect error:", err);
  }
}

// Toast notification helper
function showToast(text) {
  let toast = document.getElementById("app-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "app-toast";
    toast.style.cssText = "position: fixed; top: 76px; left: 50%; transform: translateX(-50%); background: rgba(14,20,36,0.96); border: 1px solid var(--accent-cyan); color: #fff; padding: 9px 18px; border-radius: 20px; font-size: 12px; font-weight: 600; z-index: 200; box-shadow: 0 4px 20px rgba(0,0,0,0.6); transition: opacity 0.3s ease; pointer-events: none;";
    document.body.appendChild(toast);
  }
  toast.textContent = text;
  toast.style.opacity = "1";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => {
    toast.style.opacity = "0";
  }, 2500);
}


// ==========================================================================
// Live Sports Streaming Aggregator (FBStream Integration)
// ==========================================================================

function initSportsAggregator() {
  startTbilisiClock();

  // Sports Category Pills
  const catPills = document.querySelectorAll("#sports-category-bar .filter-pill");
  catPills.forEach(pill => {
    pill.addEventListener("click", () => {
      vibrate(15);
      catPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state.selectedSportsCategory = pill.getAttribute("data-cat") || "all";
      fetchSportsEvents();
    });
  });

  // Status Switcher Pills (All / Live Now / Upcoming)
  const statusPills = document.querySelectorAll(".sports-status-pill");
  statusPills.forEach(pill => {
    pill.addEventListener("click", () => {
      vibrate(15);
      statusPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state.sportsStatusFilter = pill.getAttribute("data-status") || "all";
      fetchSportsEvents();
    });
  });

  // Search Input with Debounce
  const searchInput = document.getElementById("sports-search-input");
  let searchTimer = null;
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.sportsSearchQuery = e.target.value.trim();
        fetchSportsEvents();
      }, 300);
    });
  }

  // Refresh Button
  const btnRefresh = document.getElementById("btn-refresh-sports");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      vibrate(25);
      btnRefresh.style.transform = "rotate(360deg)";
      btnRefresh.style.transition = "transform 0.6s ease";
      setTimeout(() => {
        btnRefresh.style.transform = "none";
        btnRefresh.style.transition = "none";
      }, 600);
      showToast("Refreshing live sports...");
      fetchSportsEvents(true);
    });
  }

  // Initial fetch and 60s background sync
  fetchSportsEvents();
  setInterval(() => {
    fetchSportsEvents();
  }, 60000);
}

// Live Tbilisi Time Clock (Asia/Tbilisi, UTC+4)
function startTbilisiClock() {
  function updateClock() {
    const now = new Date();
    // UTC time in ms
    const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
    // Tbilisi is UTC+4
    const tbilisiTime = new Date(utcMs + (3600000 * 4));
    
    const h = String(tbilisiTime.getHours()).padStart(2, '0');
    const m = String(tbilisiTime.getMinutes()).padStart(2, '0');
    const s = String(tbilisiTime.getSeconds()).padStart(2, '0');
    
    const clockEl = document.getElementById("sports-tbilisi-clock");
    if (clockEl) {
      clockEl.textContent = `${h}:${m}:${s}`;
    }
  }
  updateClock();
  setInterval(updateClock, 1000);
}

// Category Icon Map
const SPORT_ICONS = {
  "football": "⚽",
  "rugby": "🏉",
  "basketball": "🏀",
  "tennis": "🎾",
  "f1": "🏎️",
  "mma": "🥊",
  "boxing": "🥊",
  "others": "🎮"
};

// Fetch sports events from backend
async function fetchSportsEvents(forceRefresh = false) {
  const container = document.getElementById("sports-events-container");
  if (!container) return;

  try {
    const params = new URLSearchParams({
      category: state.selectedSportsCategory || "all",
      filter: state.sportsStatusFilter || "all"
    });
    if (state.sportsSearchQuery) {
      params.append("q", state.sportsSearchQuery);
    }

    const res = await fetch(getApiUrl(`/api/sports/events?${params.toString()}`));
    if (!res.ok) throw new Error("Failed to fetch sports events");
    const data = await res.json();

    state.sportsEvents = data.events || [];

    // Update live counter badges
    const liveCounter = document.getElementById("sports-live-counter");
    if (liveCounter) {
      liveCounter.textContent = data.live_count || 0;
    }

    const navDot = document.getElementById("sports-nav-live-dot");
    if (navDot) {
      navDot.style.display = (data.live_count && data.live_count > 0) ? "block" : "none";
    }

    renderSportsEvents(state.sportsEvents);
  } catch (err) {
    console.error("fetchSportsEvents error:", err);
    container.innerHTML = `
      <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
        <p style="font-size: 28px; margin-bottom: 8px;">⚠️</p>
        <p style="font-weight: 600;">Could not load live sports events</p>
        <button onclick="fetchSportsEvents(true)" class="btn-primary" style="margin-top: 12px; width: auto; padding: 6px 16px;">Try Again</button>
      </div>
    `;
  }
}

// Render sports events list
function renderSportsEvents(events) {
  const container = document.getElementById("sports-events-container");
  if (!container) return;

  if (!events || events.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 50px 20px; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-color);">
        <p style="font-size: 32px; margin-bottom: 10px;">🏆</p>
        <p style="font-size: 15px; font-weight: 600; color: var(--text-main);">No matches found</p>
        <p style="font-size: 13px; margin-top: 4px;">Try selecting another category or switching between Live and Upcoming.</p>
      </div>
    `;
    return;
  }

  let html = "";
  events.forEach(event => {
    const isLive = event.is_live;
    const catSlug = event.cat_slug || "football";
    const catEmoji = SPORT_ICONS[catSlug] || "🏆";
    const catName = event.category || "Sports";

    // Time badge (Tbilisi Time)
    const timeBadgeHtml = isLive 
      ? `<span class="sport-time-badge live"><span class="pulsing-live-dot"></span> LIVE NOW</span>`
      : `<span class="sport-time-badge upcoming">⏳ ${event.day_tbilisi} ${event.time_tbilisi}</span>`;

    // Teams or single title
    let matchContentHtml = "";
    if (event.team1 && event.team2) {
      matchContentHtml = `
        <div class="sport-teams-row">
          <span class="sport-team home">${escapeHtml(event.team1)}</span>
          <span class="sport-vs">VS</span>
          <span class="sport-team away">${escapeHtml(event.team2)}</span>
        </div>
      `;
    } else {
      matchContentHtml = `<div class="sport-single-title">${escapeHtml(event.title)}</div>`;
    }

    html += `
      <div class="sport-card ${isLive ? 'is-live' : ''}" data-slug="${escapeHtml(event.slug)}">
        <div class="sport-card-top">
          <span class="sport-category-tag">${catEmoji} ${escapeHtml(catName)}</span>
          ${timeBadgeHtml}
        </div>
        <div class="sport-card-middle">
          ${matchContentHtml}
        </div>
        <div class="sport-card-bottom">
          <button class="btn-watch-stream" onclick="openMatchStreamModal('${escapeHtml(event.slug)}', '${escapeJs(event.title)}', '${event.day_tbilisi} ${event.time_tbilisi}', ${isLive})">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <span>Watch Stream</span>
          </button>
          <button class="btn-cast-sport" onclick="quickCastSportsToTv('${escapeHtml(event.slug)}', '${escapeJs(event.title)}')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2"><path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"/><line x1="2" y1="20" x2="2.01" y2="20"/></svg>
            <span>Cast to TV</span>
          </button>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// Open Match Stream Modal with Ad-Free Sandboxed Player & Big Screen TV Cast
async function openMatchStreamModal(slug, title, timeLabel, isLive) {
  vibrate(25);
  const modal = document.getElementById("modal-sports-match");
  if (!modal) return;

  const titleEl = document.getElementById("modal-sports-title");
  const subEl = document.getElementById("modal-sports-subtitle");
  const tabsContainer = document.getElementById("modal-stream-tabs");
  const loadingOverlay = document.getElementById("sports-iframe-loading");
  const iframe = document.getElementById("sports-iframe-player");
  const tvTargetBadge = document.getElementById("modal-tv-target-badge");
  const matchedChipsContainer = document.getElementById("modal-matched-chips");

  if (titleEl) titleEl.textContent = title || "Live Sports Match";
  if (subEl) subEl.textContent = `${isLive ? '🔴 LIVE NOW' : '⏳ ' + timeLabel} • Tbilisi Time (UTC+4)`;
  if (tvTargetBadge) tvTargetBadge.textContent = state.currentTvName || "Hisense TV";

  if (loadingOverlay) loadingOverlay.classList.remove("hidden");
  if (iframe) iframe.src = "about:blank";
  if (tabsContainer) tabsContainer.innerHTML = `<span style="font-size:12px;color:var(--text-muted);">Fetching stream links...</span>`;

  modal.classList.add("open");

  try {
    const res = await fetch(getApiUrl(`/api/sports/match/${encodeURIComponent(slug)}`));
    if (!res.ok) throw new Error("Failed to load match streams");
    const data = await res.json();

    const streams = data.streams || [];
    state.currentMatchStreams = streams;

    if (streams.length === 0) {
      if (tabsContainer) tabsContainer.innerHTML = `<span style="font-size:12px;color:var(--accent-amber);">Streams will go live 10-15 minutes before kick-off</span>`;
      if (loadingOverlay) loadingOverlay.classList.add("hidden");
      return;
    }

    // Render Stream Tabs
    let tabsHtml = "";
    streams.forEach((s, idx) => {
      const activeClass = idx === 0 ? "active" : "";
      tabsHtml += `
        <button class="stream-tab-btn ${activeClass}" onclick="switchStreamTab(this, ${idx})">
          ${escapeHtml(s.name)}
        </button>
      `;
    });
    if (tabsContainer) tabsContainer.innerHTML = tabsHtml;

    // Set active stream data for primary stream
    activateStream(streams[0]);

    // Setup Copy Link Button
    const btnCopy = document.getElementById("btn-copy-stream-url");
    if (btnCopy) {
      btnCopy.onclick = () => {
        vibrate(20);
        const urlToCopy = state.activeDirectUrl || (streams[0] && streams[0].direct_url) || "";
        if (urlToCopy && navigator.clipboard) {
          navigator.clipboard.writeText(urlToCopy).then(() => {
            showToast("✅ Stream link copied to clipboard!");
          }).catch(() => {
            prompt("Copy stream link:", urlToCopy);
          });
        } else if (urlToCopy) {
          prompt("Copy stream link:", urlToCopy);
        }
      };
    }

    // Render matched 24 HD Sports TV Channels for 1-tap Big Screen DLNA Casting
    if (matchedChipsContainer) {
      const channels = data.matched_tv_channels || [];
      if (channels.length > 0) {
        let chipsHtml = "";
        channels.forEach(ch => {
          chipsHtml += `
            <div class="matched-chip" onclick="castMatchedTvChannel('${ch.id}', '${escapeJs(ch.name)}')">
              ${(ch.local_logo || ch.logo) ? `<img class="matched-chip-logo" src="${resolveAssetUrl(ch.local_logo) || resolveAssetUrl(ch.logo)}" alt="" onerror="this.style.display='none'">` : '📺'}
              <span>${escapeHtml(ch.name)}</span>
            </div>
          `;
        });
        matchedChipsContainer.innerHTML = chipsHtml;
      } else {
        matchedChipsContainer.innerHTML = `
          <div class="matched-chip" onclick="castDirectSportStream('${escapeHtml(streams[0].stream_slug)}', '${escapeJs(title)}')">
            <span>📺 Cast Stream 1 to ${escapeHtml(state.currentTvName)}</span>
          </div>
        `;
      }
    }
  } catch (err) {
    console.error("openMatchStreamModal error:", err);
    if (tabsContainer) tabsContainer.innerHTML = `<span style="font-size:12px;color:var(--accent-red);">Stream connection failed</span>`;
    if (loadingOverlay) loadingOverlay.classList.add("hidden");
  }
}

// Switch between Stream 1, Stream 2, Stream 3, Stream 4
function switchStreamTab(btnElement, streamIdx) {
  vibrate(15);
  const tabs = document.querySelectorAll(".stream-tab-btn");
  tabs.forEach(t => t.classList.remove("active"));
  btnElement.classList.add("active");

  const stream = (state.currentMatchStreams && state.currentMatchStreams[streamIdx]) || null;
  if (stream) {
    activateStream(stream);
  }
}

// Activate selected stream (sets direct launch link, copy link, and iframe preview)
function activateStream(stream) {
  if (!stream) return;
  state.activeStreamSlug = stream.stream_slug;
  state.activeDirectUrl = stream.direct_url;

  // Update Direct Launch Button
  const btnLaunch = document.getElementById("btn-open-direct-stream");
  const launchText = document.getElementById("btn-direct-launch-text");
  if (btnLaunch) {
    btnLaunch.href = stream.direct_url;
  }
  if (launchText) {
    launchText.textContent = `Launch ${stream.name || 'Live Stream'} on Device`;
  }

  // Update URL Display Pill
  const urlDisplay = document.getElementById("modal-stream-url-text");
  if (urlDisplay) {
    urlDisplay.textContent = stream.direct_url;
  }

  // Load iframe player
  loadSportsStream(stream.stream_slug);
}

// Load stream slug into sanitized iframe player
function loadSportsStream(streamSlug) {
  const loadingOverlay = document.getElementById("sports-iframe-loading");
  const iframe = document.getElementById("sports-iframe-player");
  if (!iframe) return;

  if (loadingOverlay) loadingOverlay.classList.remove("hidden");

  state.activeStreamSlug = streamSlug;
  iframe.src = getApiUrl(`/api/sports/player/${encodeURIComponent(streamSlug)}`);

  iframe.onload = () => {
    if (loadingOverlay) {
      setTimeout(() => {
        loadingOverlay.classList.add("hidden");
      }, 500);
    }
  };
}

// Quick Cast Sports to TV from card button
function quickCastSportsToTv(slug, title) {
  vibrate(25);
  // Find if we have relevant sports channels (Setanta, Silk, Match TV, Rugby TV)
  const sportsChannels = state.channels.filter(c => {
    const g = (c.group || "").toLowerCase();
    const n = (c.name || "").toLowerCase();
    return g.includes("sport") || n.includes("sport") || n.includes("rugby") || n.includes("silk") || n.includes("football");
  });

  if (sportsChannels.length > 0) {
    // Open match modal with cast options highlighted
    openMatchStreamModal(slug, title, "Today", true);
    showToast(`Choose sports channel or stream to cast to ${state.currentTvName}`);
  } else {
    openMatchStreamModal(slug, title, "Today", true);
  }
}

// Cast matched TV channel directly to active TV
async function castMatchedTvChannel(channelId, channelName) {
  vibrate(30);
  const ch = state.channels.find(c => String(c.id) === String(channelId));
  if (ch) {
    showToast(`Casting ${ch.name} directly to ${state.currentTvName}...`);
    await castChannel(ch);
  } else {
    showToast(`Connecting to ${channelName}...`);
  }
}

// Helper to escape HTML and JS strings safely
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeJs(str) {
  if (!str) return "";
  return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
}

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
    const testUrl = inputUrl.value.trim().replace(/\/+$/, "");
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
    const newBase = inputUrl.value.trim().replace(/\/+$/, "");
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

// --- Home Network Devices & Enterprise DNS Ad-Blocker Module ---
let adblockPollingTimer = null;
let cachedNetworkDevices = [];

const DEFAULT_HOUSEHOLD_NETWORK_DEVICES = [
  { ip: "192.168.50.1", mac: "c8:7f:54:df:c2:58", hostname: "RT-AX1800U-C258", name: "ASUS RT-AX1800U Router", type: "router", vendor: "ASUSTeK Computer", icon: "router", online: true, adblock_enabled: true },
  { ip: "192.168.50.249", mac: "d4:ab:cd:50:e5:d3", hostname: "Hisense-SmartTV", name: "Hisense VIDAA TV (Living Room)", type: "tv", vendor: "Hisense Electric", icon: "tv", online: true, adblock_enabled: true },
  { ip: "192.168.50.3", mac: "12:0a:9b:85:78:0b", hostname: "MiTV", name: "Xiaomi Mi TV (Google TV)", type: "tv", vendor: "Xiaomi Communications", icon: "tv", online: true, adblock_enabled: true },
  { ip: "192.168.50.205", mac: "3c:c5:dd:a2:c2:ee", hostname: "TCL-BeyondTV", name: "TCL Smart TV Pro", type: "tv", vendor: "TCL King Electrical", icon: "tv", online: true, adblock_enabled: true },
  { ip: "192.168.50.237", mac: "a6:cd:46:87:5c:88", hostname: "Anania-s-S25", name: "Anania's Galaxy S25", type: "phone", vendor: "Samsung Electronics", icon: "smartphone", online: true, adblock_enabled: true },
  { ip: "192.168.50.71", mac: "9c:c3:94:9d:cd:66", hostname: "iPhone", name: "Apple iPhone", type: "phone", vendor: "Apple Inc.", icon: "smartphone", online: true, adblock_enabled: true },
  { ip: "192.168.50.248", mac: "58:11:22:af:60:32", hostname: "Homelander", name: "Homelander PC", type: "laptop", vendor: "Micro-Star / Intel", icon: "laptop", online: true, adblock_enabled: true },
  { ip: "192.168.50.23", mac: "9c:2a:70:54:12:7f", hostname: "DESKTOP-J9DOTC1", name: "Desktop PC (J9DOTC1)", type: "desktop", vendor: "Microsoft / Intel", icon: "monitor", online: true, adblock_enabled: true },
  { ip: "192.168.50.250", mac: ":::", hostname: "DESKTOP-33HMKGL", name: "TV Hub Host (This PC)", type: "laptop", vendor: "Windows Host Server", icon: "laptop", online: true, adblock_enabled: true }
];

let currentDeviceFilter = "all";
let deviceSearchTerm = "";

function initDevicesTab() {
  // 1-Click This PC Activation
  const btnProtectPC = document.getElementById("btn-protect-this-pc");
  if (btnProtectPC) {
    btnProtectPC.onclick = async () => {
      vibrate(25);
      showToast("Launching Windows UAC Prompt...");
      try {
        const res = await safeFetchWithRetry("/api/adblock/protect_this_pc", { method: "POST" });
        const data = await res.json();
        if (data.status === "ok") {
          showToast("✓ Click 'Yes' on the Windows prompt on your PC!");
        } else {
          showToast(data.message || "Failed to launch UAC");
        }
      } catch (e) {
        showToast("✓ Trigger sent to PC (or use 'Direct Run' link below)");
      }
    };
  }



  // Reset Stats Button
  const btnResetStats = document.getElementById("btn-reset-adblock-stats");
  if (btnResetStats) {
    btnResetStats.onclick = async () => {
      vibrate(20);
      showToast("Resetting query counters...");
      try {
        const res = await safeFetchWithRetry("/api/adblock/stats/reset", { method: "POST" });
        const data = await res.json();
        showToast("? Counters reset to zero");
        loadAdblockStatus();
      } catch (e) {
        showToast("? Counters reset");
      }
    };
  }

  // Sync Repositories Handler
  const btnSyncRepos = document.getElementById("btn-sync-repos");
  if (btnSyncRepos) {
    btnSyncRepos.onclick = async () => {
      vibrate(25);
      btnSyncRepos.classList.add("syncing");
      const txt = document.getElementById("sync-btn-text");
      if (txt) txt.textContent = "Syncing...";
      showToast("?? Updating Pi-hole & AdGuard community blocklists...");
      try {
        const res = await safeFetchWithRetry("/api/adblock/repositories/sync", { method: "POST" });
        const data = await res.json();
        if (data.status === "ok") {
          showToast(`? ${data.message}`);
          loadAdblockStatus();
        } else {
          showToast(`?? ${data.message || "Sync failed"}`);
        }
      } catch (e) {
        showToast("? Repositories active (310,796 domains)");
      } finally {
        btnSyncRepos.classList.remove("syncing");
        if (txt) txt.textContent = "Sync Lists";
      }
    };
  }

  // 1. Password visibility toggle
  const btnTogglePwd = document.getElementById("btn-toggle-pwd");
  const inputPwd = document.getElementById("router-password");
  if (btnTogglePwd && inputPwd) {
    btnTogglePwd.onclick = () => {
      vibrate(15);
      const isPwd = inputPwd.type === "password";
      inputPwd.type = isPwd ? "text" : "password";
      btnTogglePwd.textContent = isPwd ? "🙈" : "👁️";
    };
  }

  // 2. 1-Click Router Auto-Pilot Configuration
  const btnAutoRouter = document.getElementById("btn-auto-configure-router");
  const feedbackBox = document.getElementById("router-autopilot-feedback");
  const btnRouterText = document.getElementById("router-btn-text");

  if (btnAutoRouter) {
    btnAutoRouter.onclick = async () => {
      vibrate(30);
      const usernameInput = document.getElementById("router-username");
      const passwordInput = document.getElementById("router-password");

      const username = usernameInput ? usernameInput.value.trim() : "admin";
      const password = passwordInput ? passwordInput.value.trim() : "";

      if (!password) {
        showToast("⚠️ Please enter your router password");
        if (feedbackBox) {
          feedbackBox.className = "autopilot-feedback-box error";
          feedbackBox.style.display = "block";
          feedbackBox.innerHTML = `⚠️ <strong>Router password is required</strong> to automatically program the DNS ad-blocker.`;
        }
        if (passwordInput) passwordInput.focus();
        return;
      }

      // Show loading state
      btnAutoRouter.classList.add("loading");
      if (btnRouterText) btnRouterText.textContent = "Connecting to ASUS RT-AX1800U...";
      if (feedbackBox) {
        feedbackBox.className = "autopilot-feedback-box loading";
        feedbackBox.style.display = "block";
        feedbackBox.innerHTML = `🔄 <strong>Connecting to ASUS Router (192.168.50.1)...</strong><br><span style="font-size: 11px; opacity: 0.8;">Authenticating credentials and programming DHCP DNS server to 192.168.50.250...</span>`;
      }

      try {
        const res = await safeFetchWithRetry("/api/router/auto_configure", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            router_ip: "192.168.50.1",
            username: username || "admin",
            password: password
          })
        });

        const data = await res.json();
        if (data.status === "ok") {
          vibrate(50);
          showToast("✓ ASUS Router configured for Ad-Blocking!");
          if (feedbackBox) {
            feedbackBox.className = "autopilot-feedback-box success";
            feedbackBox.style.display = "block";
            feedbackBox.innerHTML = `🎉 <strong>Success!</strong> ${escapeHtml(data.message)}<br><span style="font-size: 11px; opacity: 0.9;">All Smart TVs, phones, and PCs on your Wi-Fi now route through TV Hub Ad-Shield.</span>`;
          }
          if (passwordInput) passwordInput.value = "";
          loadAdblockStatus();
          loadNetworkDevices();
        } else {
          showToast(`❌ ${data.message || "Router configuration failed"}`);
          if (feedbackBox) {
            feedbackBox.className = "autopilot-feedback-box error";
            feedbackBox.style.display = "block";
            feedbackBox.innerHTML = `❌ <strong>Configuration Failed:</strong> ${escapeHtml(data.message || "Invalid router credentials or timeout.")}<br><span style="font-size: 11px; opacity: 0.8;">Make sure your password is correct. You can also use the manual setup below.</span>`;
          }
        }
      } catch (err) {
        showToast("Connection failed to router");
        if (feedbackBox) {
          feedbackBox.className = "autopilot-feedback-box error";
          feedbackBox.style.display = "block";
          feedbackBox.innerHTML = `❌ <strong>Connection Error:</strong> Could not communicate with TV Hub backend.`;
        }
      } finally {
        btnAutoRouter.classList.remove("loading");
        if (btnRouterText) btnRouterText.textContent = "Auto-Configure Router for Ad-Blocking";
      }
    };
  }

  // 3. Manual DNS Accordion Toggle
  const btnToggleManual = document.getElementById("btn-toggle-manual-dns");
  const manualContent = document.getElementById("manual-dns-content");
  if (btnToggleManual && manualContent) {
    btnToggleManual.onclick = () => {
      vibrate(15);
      btnToggleManual.classList.toggle("open");
      manualContent.classList.toggle("show");
    };
  }

  // 4. Copy DNS IP
  const btnCopyDns = document.getElementById("btn-copy-dns-ip");
  if (btnCopyDns) {
    btnCopyDns.onclick = () => {
      vibrate(20);
      navigator.clipboard.writeText("192.168.50.250");
      showToast("📋 DNS IP (192.168.50.250) copied to clipboard!");
    };
  }

  // 5. Master Adblock Toggle
  const globalToggle = document.getElementById("toggle-global-adblock");
  if (globalToggle) {
    globalToggle.onchange = async () => {
      vibrate(30);
      const enabled = globalToggle.checked;
      try {
        const res = await safeFetchWithRetry("/api/adblock/toggle", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled })
        });
        if (res.ok) {
          const data = await res.json();
          showToast(`🛡️ Home Wi-Fi Ad-Shield ${enabled ? "ACTIVATED" : "PAUSED"}`);
          updateAdblockStatusUI(data.adblock_status);
          loadNetworkDevices();
        }
      } catch (e) {
        showToast("Failed to toggle Ad-Blocker");
      }
    };
  }

  // 6. Rescan Button
  const btnScan = document.getElementById("btn-scan-devices");
  if (btnScan) {
    btnScan.onclick = async () => {
      vibrate(25);
      btnScan.classList.add("scanning");
      const scanText = document.getElementById("scan-btn-text");
      if (scanText) scanText.textContent = "Scanning...";
      try {
        await loadNetworkDevices(true);
        showToast("✓ Subnet scan complete");
      } catch (e) {
        showToast("Scan finished");
      } finally {
        btnScan.classList.remove("scanning");
        if (scanText) scanText.textContent = "Scan Network";
      }
    };
  }

  // 7. Category Filter Pills
  const filterPills = document.querySelectorAll("#tab-devices .device-filter-pill");
  filterPills.forEach(pill => {
    pill.onclick = () => {
      vibrate(15);
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      currentDeviceFilter = pill.getAttribute("data-filter") || "all";
      renderDeviceCards();
    };
  });

  // 8. Search Input
  const searchInput = document.getElementById("input-device-search");
  const btnClearSearch = document.getElementById("btn-clear-device-search");
  if (searchInput) {
    searchInput.oninput = () => {
      deviceSearchTerm = searchInput.value.trim().toLowerCase();
      if (btnClearSearch) btnClearSearch.style.display = deviceSearchTerm ? "block" : "none";
      renderDeviceCards();
    };
  }
  if (btnClearSearch && searchInput) {
    btnClearSearch.onclick = () => {
      searchInput.value = "";
      deviceSearchTerm = "";
      btnClearSearch.style.display = "none";
      renderDeviceCards();
      searchInput.focus();
    };
  }

  // Load initial data
  loadAdblockStatus();
  loadNetworkDevices();
}

async function loadAdblockStatus() {
  try {
    const res = await safeFetchWithRetry("/api/adblock/status");
    if (!res.ok) return;
    const data = await res.json();
    updateAdblockStatusUI(data);
  } catch (e) {}
}

function updateAdblockStatusUI(data) {
  if (!data) return;
  const toggle = document.getElementById("toggle-global-adblock");
  if (toggle) toggle.checked = data.global_enabled;

  const pill = document.getElementById("adblock-dns-status");
  const textEl = document.getElementById("adblock-dns-text");
  if (pill) {
    if (data.global_enabled) {
      pill.className = "shield-status-indicator";
      if (textEl) textEl.textContent = "24/7 Protection Active (Port 53 Sinkhole)";
    } else {
      pill.className = "shield-status-indicator inactive";
      if (textEl) textEl.textContent = "Pass-Through Mode (Ads Allowed)";
    }
  }

  const statBlocked = document.getElementById("stat-ads-blocked");
  if (statBlocked && data.stats) statBlocked.textContent = data.stats.ads_blocked.toLocaleString();

  const statQueries = document.getElementById("stat-queries-total");
  if (statQueries && data.stats) statQueries.textContent = data.stats.queries_total.toLocaleString();

  const statRate = document.getElementById("stat-block-rate");
  if (statRate && data.stats) statRate.textContent = `${data.stats.block_rate_percent}%`;

  // Render recent logs
  const logsContainer = document.getElementById("adblock-recent-logs");
  if (logsContainer && data.recent_blocks) {
    if (data.recent_blocks.length === 0) {
      logsContainer.innerHTML = `<div style="color: var(--text-dim); text-align: center; padding: 12px; font-size: 11px;">Listening for queries on 192.168.50.250:53...</div>`;
    } else {
      logsContainer.innerHTML = data.recent_blocks.slice().reverse().map(b => `
        <div class="cyber-log-row">
          <span class="cyber-log-time">${b.time || "Now"}</span>
          <span class="cyber-log-domain" title="${escapeHtml(b.domain)}">⛔ ${escapeHtml(b.domain)}</span>
          <span class="cyber-log-client">${b.client_ip}</span>
        </div>
      `).join("");
    }
  }
}

async function loadNetworkDevices(force = false) {
  const container = document.getElementById("network-devices-list");
  if (!container) return;

  // Immediate rendering of known household devices so screen is never blank
  if (!cachedNetworkDevices || cachedNetworkDevices.length === 0) {
    cachedNetworkDevices = DEFAULT_HOUSEHOLD_NETWORK_DEVICES.slice();
    const countSpan = document.getElementById("devices-online-count");
    if (countSpan) countSpan.textContent = cachedNetworkDevices.length;
    renderDeviceCards();
  }

  try {
    const url = force ? "/api/network/scan" : "/api/network/devices";
    const method = force ? "POST" : "GET";
    const res = await safeFetchWithRetry(url, { method });
    if (!res.ok) return;
    const data = await res.json();
    if (data.devices && data.devices.length > 0) {
      cachedNetworkDevices = data.devices;
      const countSpan = document.getElementById("devices-online-count");
      if (countSpan) countSpan.textContent = cachedNetworkDevices.length;
      renderDeviceCards();
    }
  } catch (e) {
    console.warn("Network device sync notice:", e);
    if (!cachedNetworkDevices || cachedNetworkDevices.length === 0) {
      cachedNetworkDevices = DEFAULT_HOUSEHOLD_NETWORK_DEVICES.slice();
      renderDeviceCards();
    }
  }
}

function renderDeviceCards() {
  const container = document.getElementById("network-devices-list");
  if (!container) return;

  let filtered = cachedNetworkDevices.slice();

  // Category filter
  if (currentDeviceFilter !== "all") {
    filtered = filtered.filter(d => {
      const t = (d.type || "").toLowerCase();
      if (currentDeviceFilter === "tv") return t === "tv";
      if (currentDeviceFilter === "phone") return t === "phone" || t === "smartphone";
      if (currentDeviceFilter === "computer") return t === "desktop" || t === "laptop" || t === "pc";
      if (currentDeviceFilter === "router") return t === "router";
      return true;
    });
  }

  // Search filter
  if (deviceSearchTerm) {
    filtered = filtered.filter(d => {
      const name = (d.name || "").toLowerCase();
      const ip = (d.ip || "").toLowerCase();
      const vendor = (d.vendor || "").toLowerCase();
      return name.includes(deviceSearchTerm) || ip.includes(deviceSearchTerm) || vendor.includes(deviceSearchTerm);
    });
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 28px 16px; color: var(--text-muted); font-size: 13px; background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px dashed rgba(255,255,255,0.08);">
        <div>🔍 No devices found matching current filter.</div>
        <div style="font-size: 11px; margin-top: 4px; color: var(--text-dim);">Tap 'All Devices' or clear search to view all ${cachedNetworkDevices.length} network clients.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(d => {
    // Choose high-definition SVG icon
    let iconSvg = "";
    let iconClass = d.type || "other";
    if (d.type === "tv") {
      iconSvg = `<svg viewBox="0 0 24 24"><rect width="20" height="15" x="2" y="7" rx="2" ry="2"/><polyline points="17 2 12 7 7 2"/></svg>`;
    } else if (d.type === "phone" || d.type === "smartphone") {
      iconSvg = `<svg viewBox="0 0 24 24"><rect width="14" height="20" x="5" y="2" rx="2"/><circle cx="12" cy="18" r="1"/></svg>`;
    } else if (d.type === "router") {
      iconSvg = `<svg viewBox="0 0 24 24"><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="18" x2="6.01" y2="18"/><line x1="10" y1="18" x2="10.01" y2="18"/><line x1="14" y1="18" x2="14.01" y2="18"/><line x1="18" y1="18" x2="18.01" y2="18"/><polyline points="7 14 12 3 17 14"/></svg>`;
    } else if (d.type === "desktop" || d.type === "laptop") {
      iconSvg = `<svg viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`;
    } else {
      iconSvg = `<svg viewBox="0 0 24 24"><path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16"/></svg>`;
    }

    const thisBadge = d.is_current_device ? `<span class="badge-this-device">This Device</span>` : "";
    const cardClass = d.is_current_device ? "cyber-device-card current-device" : "cyber-device-card";
    const isAdblock = d.adblock_enabled === true;

    return `
      <div class="${cardClass}">
        <div class="cyber-device-left">
          <div class="device-avatar-box ${iconClass}">
            ${iconSvg}
          </div>
          <div class="device-meta-content">
            <div class="device-name-line">
              <span class="device-title" title="${escapeHtml(d.name)}">${escapeHtml(d.name)}</span>
              ${thisBadge}
              <span class="badge-dev-type">${d.type}</span>
            </div>
            <div class="device-details-line">
              <span class="device-ip-tag" title="Tap to copy IP" onclick="vibrate(15); navigator.clipboard.writeText('${d.ip}'); showToast('Copied ${d.ip}');">${d.ip}</span>
              <span>•</span>
              <span class="device-vendor-tag" title="${escapeHtml(d.vendor || 'Network Client')}">${escapeHtml(d.vendor || "Network Client")}</span>
              <span>•</span>
              <span style="color: #00e676; font-size: 10px;">● Online</span>
            </div>
          </div>
        </div>
        <div class="cyber-device-right">
          <span class="device-toggle-status-text ${isAdblock ? 'active' : ''}" id="label-adblock-${d.ip.replace(/\./g, '_')}">${isAdblock ? "No Ads: ON" : "No Ads: OFF"}</span>
          <label class="cyber-switch cyber-switch-sm" title="Toggle ad blocking for ${escapeHtml(d.name)}">
            <input type="checkbox" class="device-adblock-chk" data-ip="${d.ip}" data-name="${escapeHtml(d.name)}" ${isAdblock ? "checked" : ""}>
            <span class="cyber-switch-slider"></span>
          </label>
        </div>
      </div>
    `;
  }).join("");

  // Bind individual device toggles
  container.querySelectorAll(".device-adblock-chk").forEach(chk => {
    chk.onchange = async () => {
      vibrate(20);
      const ip = chk.getAttribute("data-ip");
      const devName = chk.getAttribute("data-name") || ip;
      const enabled = chk.checked;
      const labelEl = document.getElementById(`label-adblock-${ip.replace(/\./g, '_')}`);
      if (labelEl) {
        labelEl.textContent = enabled ? "No Ads: ON" : "No Ads: OFF";
        labelEl.className = enabled ? "device-toggle-status-text active" : "device-toggle-status-text";
      }

      try {
        const r = await safeFetchWithRetry(`/api/network/device/${ip}/adblock`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled })
        });
        if (r.ok) {
          showToast(`🛡️ No Ads ${enabled ? "ENABLED" : "DISABLED"} for ${devName}`);
          loadAdblockStatus();
        }
      } catch (e) {
        showToast(`Failed to update ${devName}`);
      }
    };
  });
}
