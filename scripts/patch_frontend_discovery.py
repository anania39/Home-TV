import re
from pathlib import Path

def patch_html(file_path):
    p = Path(file_path)
    content = p.read_text(encoding="utf-8")

    old_banner = """      <!-- Real Hardware TV Status Banner -->
      <div class="tv-status-banner standby" id="tv-status-banner">
        <div class="status-indicator">
          <span class="status-dot red" id="tv-status-dot"></span>
          <span id="tv-status-text">Detecting TV Hardware...</span>
        </div>
        <button id="btn-quick-wake" class="btn-wake-quick" title="Send Wake-on-LAN power packet">
          ⚡ Turn On TV
        </button>
      </div>

      <!-- TV Selector Bar -->
      <div class="tv-selector-bar">
        <select id="tv-dropdown" class="selector-dropdown" aria-label="Select Target TV">
          <option value="" disabled selected>Connecting to TV...</option>
        </select>
      </div>"""

    new_banner = """      <!-- Real Hardware TV Status Banner -->
      <div class="tv-status-banner active" id="tv-status-banner">
        <div class="status-indicator">
          <span class="status-dot green" id="tv-status-dot"></span>
          <span id="tv-status-text">Hisense VIDAA TV (Living Room) Ready</span>
        </div>
        <button id="btn-quick-wake" class="btn-wake-quick" style="display: none;" title="Send Wake-on-LAN power packet">
          ⚡ Turn On TV
        </button>
      </div>

      <!-- TV Selector Bar -->
      <div class="tv-selector-bar">
        <select id="tv-dropdown" class="selector-dropdown" aria-label="Select Target TV">
          <option value="tv_192_168_50_249" selected>Hisense VIDAA TV (Living Room)</option>
          <option value="tv_192_168_50_3">Xiaomi Mi TV (Google TV)</option>
          <option value="tv_192_168_50_205">TCL Smart TV Pro (Google TV)</option>
          <option value="web_receiver">TV Web Receiver (Browser at /tv)</option>
        </select>
      </div>"""

    if old_banner in content:
        content = content.replace(old_banner, new_banner)
        p.write_text(content, encoding="utf-8")
        print(f"Patched {file_path}")
    else:
        print(f"Old banner pattern not found in {file_path}, skipping.")

def patch_app_js():
    p = Path("static/app.js")
    code = p.read_text(encoding="utf-8")

    # Replace autoDetectHub and related functions
    old_hub_detection = """async function autoDetectHub() {
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
}"""

    new_hub_detection = """async function probeEndpoint(url, timeoutMs = 2000) {
  if (!url) return false;
  const cleanUrl = url.replace(/\\/+$/, "");
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    const res = await fetch(`${cleanUrl}/api/auth/status`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      const data = await res.json();
      return data.authenticated === true;
    }
  } catch (e) {}
  return false;
}

function setHubBase(url) {
  HUB_BASE = (url || "").replace(/\\/+$/, "");
  if (HUB_BASE) {
    localStorage.setItem("tvhub_backend_url", HUB_BASE);
  } else {
    localStorage.removeItem("tvhub_backend_url");
  }
}

async function autoDetectHub() {
  const isGithubPages = window.location.hostname.includes("github.io");
  if (!isGithubPages) return true;

  // 1. Verify if existing cached HUB_BASE is actually online right now
  let currentBase = localStorage.getItem("tvhub_backend_url") || HUB_BASE;
  if (currentBase) {
    const isAlive = await probeEndpoint(currentBase, 1800);
    if (isAlive) {
      HUB_BASE = currentBase.replace(/\\/+$/, "");
      console.log("Current Hub confirmed responsive:", HUB_BASE);
      return true;
    }
    console.warn("Cached Hub URL is offline or expired. Purging stale link:", currentBase);
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
}"""

    code = code.replace(old_hub_detection, new_hub_detection)

    # Device list population and fallback
    old_fetch_devices = """// --- Device Discovery & Hardware Status ---
async function fetchDevices() {
  const dropdown = document.getElementById("tv-dropdown");
  try {
    const res = await fetch(getApiUrl("/api/devices"));
    const data = await res.json();
    dropdown.innerHTML = "";

    data.devices.forEach(dev => {
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
      if (dev.id === data.selected_device_id) {
        opt.selected = true;
        state.currentTvId = dev.id;
        state.currentTvName = dev.name;
        document.getElementById("info-active-tv").textContent = dev.name;
      }
      dropdown.appendChild(opt);
    });

    if (!state.currentTvId && data.devices.length > 0) {
      state.currentTvId = data.devices[0].id;
      state.currentTvName = data.devices[0].name;
      document.getElementById("info-active-tv").textContent = data.devices[0].name;
    }
  } catch (e) {
    console.error("Device fetch error:", e);
  }
}"""

    new_fetch_devices = """// Known household TVs for instant zero-wait selection
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
}"""

    code = code.replace(old_fetch_devices, new_fetch_devices)

    # In DOMContentLoaded, call fetchHardwareStatus as well
    old_init = """  checkAuth();
  fetchDevices();
  fetchChannels();"""

    new_init = """  populateDevicesList(DEFAULT_HOUSEHOLD_DEVICES, "tv_192_168_50_249");
  checkAuth();
  fetchDevices();
  fetchHardwareStatus();
  fetchChannels();"""

    code = code.replace(old_init, new_init)

    # State defaults: Hisense TV pre-selected
    code = code.replace('currentTvName: "Scanning...",', 'currentTvName: "Hisense VIDAA TV (Living Room)",\n  currentTvId: "tv_192_168_50_249",')

    p.write_text(code, encoding="utf-8")
    print("Patched static/app.js successfully!")

if __name__ == "__main__":
    patch_html("index.html")
    patch_html("static/index.html")
    patch_app_js()
