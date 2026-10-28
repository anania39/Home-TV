# TV Hub — Deep Dive Analysis

**App:** https://analytical-proteins-military-indices.trycloudflare.com/  
**Probed:** 2026-10-27 (Asia/Tbilisi)  
**Scope:** read-only (no TV MQTT commands, no Homelander deploys)

---

## 1. What the app is

**TV Hub** is a FastAPI-backed mobile web UI + TV browser receiver:

| Surface | Path | Role |
|---------|------|------|
| Phone / control UI | `/` + `/static/app.js` | Channel grid, remote, cast, settings |
| TV receiver | `/tv` | Full-screen `<video>` + **hls.js@latest** over WebSocket `/ws/receiver` |
| Channel API | `GET /api/iptv/channels` | 62 curated channels (Georgian / Russian / English) |
| Stream proxy | `/api/stream/proxy?url=` | Rewrites HLS playlists so segments go through the hub |
| OpenAPI | `/docs`, `/openapi.json` | Full API map |

Local LAN URL shown in Settings: `http://192.168.50.250:8000` (Homelander). Public access is a **Cloudflare quick tunnel** (hostname can change when the tunnel restarts).

---

## 2. Channel / stream findings

| Metric | Count |
|--------|------:|
| Total channels | **62** |
| Logos HTTP-verified | **62 / 62** (see `channel-logos.*`) |
| Live direct from internet | **18** |
| Live only via hub proxy | **40** |
| Dead / broken | **4** |

### Dead streams (replace or remove)

| ID | Name | Why |
|----|------|-----|
| `ge-pirveli` | TV Pirveli | `http://nue01-edge01.itdc.ge/pirvelitv/mpegts` → HTTP 500 |
| `ge-euronews` | Euronews Georgia | same host, MPEG-TS → HTTP 500 |
| `ru-rossiya24` | Россия 24 | direct timeout; proxy 502 |
| `ru-rossiya1` | Россия 1 | proxy returns **HTML error page** wrapped as fake playlist |

MPEG-TS URLs are also a player problem: `/tv` only special-cases `.m3u8` for hls.js; bare MPEG-TS goes to `video.src` and will fail on most browsers.

### Proxy-dependent groups

- **televiziebi.org / televizia.org** — HTTP **403** direct (CDN referrer/geo). Hub proxy returns valid live playlists (~2 KB media playlists with `.ts` segments).
- **stream.mcquack.net** — HTTP **500** direct from this probe network. Via proxy, returns a **valid HLS master** (~310 B, single 1080p variant). Treat as geo/IP sensitive; may die for some viewers.
- **Official Georgian CDNs** (`tv.cdn.xsg.ge`, `c4635.cdn.xsg.ge`, `stream.sstv.ge`) and **English public HLS** (DW, Red Bull, Bloomberg, CBC Amagi) work **direct**.

### Current logos are wrong by design

`/static/logos/*.svg` are Antigravity-drawn placeholders (gradient tile + initials / fake icon). Bloomberg is mapped to **`en-nasa.svg`** (NASA meatball + “NASA TELEVISION HD”). Full replacement pack is in `channel-logos.json`.

---

## 3. Player architecture (`/tv`)

```js
// Current hls.js config (tv.html)
hls = new Hls({
  enableWorker: true,
  lowLatencyMode: true,      // ← bad for unstable IPTV
  maxBufferLength: 30,
  maxMaxBufferLength: 60,
  backBufferLength: 30,
  liveSyncDuration: 3,
  liveMaxLatencyDuration: 10
});
```

**Library:** `hls.js@latest` from jsDelivr (unpinned — can break overnight).  
**Transport:** WebSocket commands (`play` / `pause` / `stop` / `volume` / `seek`) from phone → receiver.  
**Phone UI** does not play video itself; it calls `/api/iptv/cast/{id}` and updates a bottom “now playing” bar.

### Top issues (priority)

1. **Proxy rewrites playlists to LAN IP `http://192.168.50.250:8000/...`**  
   When the phone/TV is on the Cloudflare tunnel hostname, rewritten segment URLs point at Homelander’s private IP. Remote viewers (or the TV using the tunnel URL) get broken segments. **Fix:** rewrite using `request.base_url` / public tunnel host / relative `/api/stream/proxy?...` URLs.

2. **`lowLatencyMode: true` on non-LL-HLS IPTV**  
   Forces aggressive live edge (3s sync / 10s max latency). On weak Wi‑Fi this causes endless stalls and quality oscillation. Prefer `false` + deeper buffer for IPTV.

3. **No ABR / network-aware startup**  
   Missing `startLevel`, `capLevelToPlayerSize`, `abrEwmaDefaultEstimate`. On a phone hotspot or congested 2.4 GHz Wi‑Fi the player may jump to 1080p (mcquack masters advertise ~7.5 Mbps) and buffer forever.

4. **hls.js loaded as `@latest` + no preload / preconnect**  
   First channel wait includes CDN RTT for the library. Pin a version (`hls.js@1.5.x`) and `<link rel="preconnect">` to stream hosts / jsDelivr.

5. **Cloudflare quick tunnel bandwidth + double-hop**  
   Phone → CF edge → Homelander → origin CDN → back through proxy → TV. Every segment pays tunnel overhead. Settings UI claims “0ms Local RAM Serving / 40 Segments Ring-Buffer” — that is marketing copy in HTML; the receiver itself does **not** implement a 40-segment ring buffer (only standard hls.js buffers).

---

## 4. Concrete playback improvements (low bandwidth)

### 4.1 Recommended hls.js config (IPTV / weak Wi‑Fi)

```js
function buildHlsConfig() {
  const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  const saveData = !!(conn && conn.saveData);
  const slow = saveData || (conn && ['slow-2g','2g','3g'].includes(conn.effectiveType));
  const downlink = conn && conn.downlink; // Mbps estimate

  return {
    enableWorker: true,
    lowLatencyMode: false,          // IPTV ≠ LL-HLS
    backBufferLength: 30,           // free RAM behind playhead
    maxBufferLength: slow ? 60 : 40,
    maxMaxBufferLength: slow ? 120 : 90,
    maxBufferSize: slow ? 30e6 : 60e6,
    maxBufferHole: 0.5,
    highBufferWatchdogPeriod: 3,
    nudgeMaxRetry: 8,
    fragLoadingTimeOut: 20000,
    manifestLoadingTimeOut: 15000,
    levelLoadingTimeOut: 15000,
    fragLoadingMaxRetry: 6,
    manifestLoadingMaxRetry: 4,
    startLevel: -1,                 // auto, but…
    testBandwidth: true,
    abrEwmaDefaultEstimate: slow ? 300000 : (downlink ? downlink * 400000 : 500000),
    abrEwmaFastLive: 3.0,
    abrEwmaSlowLive: 9.0,
    abrBandWidthFactor: 0.7,        // stay under estimate
    abrBandWidthUpFactor: 0.5,      // climb slowly
    capLevelToPlayerSize: true,     // don't fetch 1080p for 720p video element
    capLevelOnFPSDrop: true,
    liveSyncDurationCount: 3,
    liveMaxLatencyDurationCount: 10,
    liveDurationInfinity: true,
  };
}
```

On `MANIFEST_PARSED`, optionally force a safe start:

```js
hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
  if (data.levels.length > 1) {
    // start at lowest or second-lowest, then let ABR climb
    hls.startLevel = 0;
    hls.loadLevel = 0;
  }
  video.play().catch(() => {});
});
```

### 4.2 Always cast through the hub proxy (but fix host rewriting)

Phone already has “Compatibility Stream Proxy” for manual cast. Channel cast should **always** use:

` /api/stream/proxy?url=<encoded>`  

and the proxy must emit **same-origin** segment URLs (path-only or current public host), never hard-coded `192.168.50.250`.

### 4.3 Failover / backups

Per channel store `url` + `backup_urls[]`. On fatal `NETWORK_ERROR` after N retries, switch source. Mark dead channels in the API (`alive: false`) so the UI can grey them out (Pirveli, Euronews GE, Rossiya 1/24 today).

### 4.4 Channel switch UX

You already destroy HLS on each play (good). Add:

- **Stop-before-play flush** (you advertise this — keep it).
- **Hover / focus prefetch:** on channel-card `pointerenter` / focus, `fetch(proxyUrl, {method:'HEAD'})` or warm DNS.
- **Instant OSD** with logo from `channel-logos` while buffer fills.
- Debounce rapid CH+/CH− so you don't open 5 HLS sessions.

### 4.5 Network hints in the phone UI

```js
const conn = navigator.connection;
if (conn) {
  conn.addEventListener('change', () => {
    // push quality preference to receiver over WS: {type:'abr_hint', maxHeight: 480}
  });
}
```

Show a “Low data mode” toggle that caps `hls.autoLevelCapping` to 480p / 720p.

### 4.6 HTML head performance

```html
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="dns-prefetch" href="https://tv.cdn.xsg.ge">
<link rel="dns-prefetch" href="https://streaming-hls3.televiziebi.org">
<link rel="dns-prefetch" href="https://amagi-streams.akamaized.net">
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.17"></script> <!-- pin -->
```

### 4.7 Error handling

Current fatal handler only `startLoad` / `recoverMediaError` / destroy. Improve:

- Exponential backoff on `NETWORK_ERROR` (1s, 2s, 4s).
- After 3 fatals → try backup URL → toast “Channel unavailable”.
- Surface `data.details` in OSD for debugging (`manifestLoadError`, `fragLoadError`).

### 4.8 TV remote / D-pad

Phone remote tab already sends keys via `/api/remote/key`. On `/tv` receiver, also handle keyboard / HID:

- Arrow keys move a focus ring across a mini channel strip.
- OK = play focused; Back = stop → standby.
- Keep `requestFullscreen` but don't require a click every time (auto on first play).

### 4.9 Cloudflare tunnel caveats

- Quick tunnels are **temporary** and rate/bandwidth limited — fine for demos, poor for 1080p IPTV to multiple devices.
- Prefer LAN URL `http://192.168.50.250:8000` when phone + TV are on `192.168.50.x`.
- For stable remote access: named Cloudflare Tunnel + optional Bitrate cap, or WireGuard/Tailscale to Homelander (no CF middlebox).
- Don't double-proxy: if TV browser is on LAN, cast **direct LAN** URLs; only use CF hostname for off-network phones.

### 4.10 Settings page honesty

The “High-Tech Streaming Engine Status” card claims Adaptive Lookahead Prefetch (40 segments), 0ms RAM serving, preroll suppressor. Either **implement** a server-side segment cache (e.g. ring buffer of last N `.ts` on Homelander) or tone down the copy so it matches hls.js reality.

---

## 5. Security / hygiene (brief)

- IPTV credentialed / redistributed streams (mcquack etc.) may violate provider ToS — keep the hub **private** (auth already has `/api/auth/status`; enforce it on cast/proxy).
- Proxy is an open relay if exposed on the tunnel without auth — **require auth** on `/api/stream/proxy` and `/api/iptv/cast/*`.
- Don't log full stream URLs publicly.

---

## 6. Antigravity prompt — performance pass

```text
You are editing my TV Hub app (FastAPI backend on Homelander + static app.js + /tv receiver).

Read /workspace/tvapp/analysis.md and apply these changes:

1) PROXY HOST BUG (critical)
   In /api/stream/proxy playlist rewriting, NEVER hardcode http://192.168.50.250:8000.
   Rewrite segment/master URLs to same-origin relative paths:
     /api/stream/proxy?url=<urlencoded>
   using the current request public base URL when an absolute URL is required.

2) HLS.JS CONFIG on /tv
   - Pin hls.js to a fixed version (e.g. 1.5.17), not @latest
   - Replace config with lowLatencyMode:false, deeper buffers, startLevel:-1,
     capLevelToPlayerSize:true, abrEwmaDefaultEstimate based on navigator.connection
   - On MANIFEST_PARSED for multi-level streams, start at level 0 then allow ABR up
   - Better fatal error retries + backup URL support

3) CHANNEL HEALTH
   - Mark ge-pirveli, ge-euronews, ru-rossiya1, ru-rossiya24 as offline in the API
     (or replace with working HLS mirrors)
   - Prefer HLS (.m3u8) over raw MPEG-TS for browser playback
   - Always cast IPTV channels through the stream proxy

4) LOW BANDWIDTH UX
   - Add a "Low data / 480p cap" toggle in Settings that sets autoLevelCapping on the receiver via WebSocket
   - Prefetch DNS / preconnect for major CDNs
   - Debounce rapid channel switches; destroy previous Hls before loading next
   - Keep monogram logo fallback; wire real logos from channel-logos.json

5) TUNNEL vs LAN
   - In Settings, detect whether the page is opened via trycloudflare.com vs LAN IP
   - Prefer LAN base URL for cast targets when both phone and TV are local
   - Warn that quick tunnels add latency and may throttle HD

Do not send any MQTT/remote keys to the Hisense TV as part of this task.
Do not deploy unrelated services. Keep changes in the TV Hub codebase only.
```

---

## 7. File index

| File | Purpose |
|------|---------|
| `/workspace/tvapp/channel-logos.md` | Human table + Antigravity logo prompt |
| `/workspace/tvapp/channel-logos.csv` | Spreadsheet-friendly |
| `/workspace/tvapp/channel-logos.json` | Machine mapping + stream_status |
| `/workspace/tvapp/analysis.md` | This document |
| `/workspace/tvapp/channels_raw.json` | Raw API dump |
| `/workspace/tvapp/stream_status.json` | Per-URL direct/proxy probes |
| `/workspace/tvapp/app.js` / `tv.html` / `index.html` | Saved copies of live assets |
