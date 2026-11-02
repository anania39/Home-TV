import re

app_file = r"static/app.js"
with open(app_file, "r", encoding="utf-8") as f:
    text = f.read()

crlf = "\r\n" in text
text_lf = text.replace("\r\n", "\n")

target = """let HUB_BASE = localStorage.getItem("tvhub_backend_url") || "";

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
}"""

replacement = """let HUB_BASE = localStorage.getItem("tvhub_backend_url") || "";
let _activeHubType = "cloud"; // "local_wifi", "pc_tunnel", "cloud"
let _cachedEndpointData = null;

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
    throw new Error("TV Hub server is connecting. Please wait a moment.");
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
    console.warn(`Request to ${url} failed, attempting failover recovery...`, err);
    if (isGithubPages) {
      const recovered = await autoDetectHub(true);
      if (recovered && getHubBase()) {
        const retryUrl = getApiUrl(path);
        if (retryUrl) {
          try {
            const retryRes = await fetch(retryUrl, options);
            if (retryRes.status !== 405 && retryRes.status !== 502 && retryRes.status !== 504 && retryRes.status !== 503) {
              return retryRes;
            }
          } catch (e2) {}
        }
      }
    }
    throw new Error("Unable to reach TV Hub server. Check your connection or restart TV Hub.");
  }
}"""

target_auto = """function updateHubStatusBadge(isOnline, labelText = null) {
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
}"""

replacement_auto = """function updateHubStatusBadge(isOnline, labelText = null) {
  const badge = document.getElementById("network-badge-text");
  if (!badge) return;
  if (!window.location.hostname.includes("github.io")) {
    const localHost = window.location.hostname;
    badge.innerHTML = `<span style="color: var(--accent-cyan); font-weight: 600;" title="Running on Local Wi-Fi Host">🟢 Wi-Fi Host (${localHost})</span>`;
    return;
  }
  const base = getHubBase();
  let label = labelText;
  if (!label) {
    if (isOnline) {
      label = _activeHubType === "pc_tunnel" ? "PC Hub Linked" : (_activeHubType === "local_wifi" ? "Wi-Fi Host" : "Cloud Online");
    } else {
      label = base ? "Reconnecting..." : "Hub Offline";
    }
  }
  const color = isOnline ? "var(--accent-cyan)" : (base ? "#f59e0b" : "#ef4444");
  badge.innerHTML = `<span style="color: ${color}; cursor: pointer; font-weight: 500;" title="Tap to view Wi-Fi & Cloud Host Info">🌐 GitHub (${label})</span>`;
}

async function autoDetectHub(forceRefresh = false) {
  const isGithubPages = window.location.hostname.includes("github.io");
  if (!isGithubPages) {
    _activeHubType = "local_wifi";
    updateHubStatusBadge(true, `Wi-Fi Host (${window.location.hostname})`);
    state.hubOnline = true;
    return true;
  }

  // 1. Fetch fresh endpoint.json (direct + GitHub raw fallback)
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

  _cachedEndpointData = endpointData;
  const pcTunnel = endpointData && endpointData.hub_url ? endpointData.hub_url : null;
  const cloudHub = (endpointData && endpointData.cloud_hub_url) ? endpointData.cloud_hub_url : "https://tvhub.92.5.71.162.sslip.io";

  // Fast verify existing cached HUB_BASE if healthy and not forceRefresh
  if (!forceRefresh) {
    let currentBase = localStorage.getItem("tvhub_backend_url") || HUB_BASE;
    if (currentBase && !currentBase.includes("github.io")) {
      const isAlive = await probeEndpoint(currentBase, 1500);
      if (isAlive) {
        HUB_BASE = currentBase.replace(/\\/+$/, "");
        _activeHubType = HUB_BASE.includes("sslip.io") ? "cloud" : "pc_tunnel";
        updateHubStatusBadge(true);
        state.hubOnline = true;
        return true;
      }
    }
  }

  // Priority 1: Check PC Hub Tunnel (user's home laptop with TVs & unblocked residential YouTube)
  if (pcTunnel && !pcTunnel.includes("github.io")) {
    const pcAlive = await probeEndpoint(pcTunnel, 1800);
    if (pcAlive) {
      setHubBase(pcTunnel);
      _activeHubType = "pc_tunnel";
      console.log("Connected to Home PC Hub via Public Tunnel:", pcTunnel);
      updateHubStatusBadge(true, "PC Hub Linked");
      state.hubOnline = true;
      return true;
    }
  }

  // Priority 2: Failover to 24/7 Cloud Hub
  if (cloudHub && !cloudHub.includes("github.io")) {
    const cloudAlive = await probeEndpoint(cloudHub, 2000);
    if (cloudAlive) {
      setHubBase(cloudHub);
      _activeHubType = "cloud";
      console.log("Connected to 24/7 Cloud Server:", cloudHub);
      updateHubStatusBadge(true, "Cloud Online");
      state.hubOnline = true;
      return true;
    }
  }

  updateHubStatusBadge(false, "Hub Offline");
  state.hubOnline = false;
  return false;
}"""

assert target in text_lf, "target not found in static/app.js"
assert target_auto in text_lf, "target_auto not found in static/app.js"

text_lf = text_lf.replace(target, replacement).replace(target_auto, replacement_auto)
if crlf:
    text_lf = text_lf.replace("\n", "\r\n")

with open(app_file, "w", encoding="utf-8") as f:
    f.write(text_lf)

print("Successfully updated static/app.js with dual-host auto-detection and resilient failover!")
