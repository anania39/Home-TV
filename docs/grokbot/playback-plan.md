# TV Hub playback plan — failover + Hisense VIDAA bug fixes

Generated: 2026-10-27 Asia/Tbilisi  
Project: `C:\Users\Anania Light Laptop\Downloads\tv hub`  
Receiver page: `static/tv.html` (Hisense VIDAA browser)  
Controller: `static/app.js`  
Backend: `backend/iptv_manager.py`, `backend/stream_proxy.py`, `backend/app.py`

Legal rule: only broadcaster / FAST / free-to-air sources. No mcquack / unpaid sports-movie restreams. Pack: `docs/grokbot/channels-with-backups.json`.

---

## 1. Root causes found in current code

### 1.1 Previous channel flashes back / blinks

| Cause | Where | Why it blinks |
|---|---|---|
| **No play-session token** | `static/tv.html` `playStream` ~378–450 | Fatal HLS errors schedule `setTimeout` retries (lines 428–442). After a channel switch, `destroyPlayers()` nulls `hls` then creates a **new** `hls`. The stale timeout sees a non-null `hls` and calls `hls.startLoad()` / `recoverMediaError()` / or `playStream(currentPlayingUrl, …)` on the **new** session → brief flash of wrong buffers / restart. |
| **Listeners not gated** | `MANIFEST_PARSED` / `ERROR` handlers ~404–450 | Handlers close over `title`/`logoUrl` from the old call; destroy() usually removes them, but any in-flight callback + the setTimeout race is enough on slow VIDAA MSE. |
| **HTTP 410 path incomplete** | ~417–421 | Stale proxy sessions correctly get 410, then `destroyPlayers()` runs, but there is no session id on the client to ignore further events, and no immediate attach of the new source coordination. |
| **Duplicate play guard is URL-only** | ~380–383 | `currentPlayingUrl === url && (hls \|\| mpegtsPlayer \|\| !video.paused)` — rapid WS `play` with a new URL while old destroy is mid-flight can interleave. |
| **Controller pre-warm** | `static/app.js` ~506–512 | Hover `HEAD` to `/api/stream/proxy` is fine (does not attach to the TV `<video>`), but rapid clicks only debounce 350ms (`isCasting`, ~559). Double-taps can still enqueue two casts. |
| **Backend session kill** | `backend/stream_proxy.py` ~23–87, ~326–335 | Session manager returns 410 for stale `sid` — good. Client must treat 410 as “stop this session only”, not “retry same URL”. |

**Fix:** introduce `playSessionId` (monotonic int). Every `playStream` increments it; capture `const session = playSessionId` in closures; ignore events / timeouts when `session !== playSessionId`. Cancel pending retry timers in `destroyPlayers`. Debounce casts to ≥500ms and ignore WS play if identical URL+session already loading.

### 1.2 Lag / stalls on Hisense

| Cause | Where | Why |
|---|---|---|
| **Buffers too large for TV RAM** | `buildHlsConfig` ~351–354 | `maxBufferLength` 40–60, `maxMaxBufferLength` 90–120, `backBufferLength` 30, `maxBufferSize` 30–60MB — VIDAA MSE runs out of memory → stalls / decoder resets. |
| **Worker may hurt on VIDAA** | ~349 `enableWorker: true` | Some Hisense browsers mishandle HLS worker; prefer auto-detect / false on TV UA. |
| **No stall watchdog → source failover** | ERROR handler only | Non-fatal stalls / waiting-for-data never trigger quality drop or source switch. |
| **mpegts latency chasing** | ~466 `liveBufferLatencyChasing: true` | Chases live edge aggressively → more stalls on weak Wi-Fi. |
| **No 1080p hard cap for TV** | ABR only | 1440p TRT / heavy 1080p on weak CPU causes lag. Cap `maxLevel` / filter levels >1080. |

**Fix (TV profile):** `maxBufferLength: 24`, `maxMaxBufferLength: 48`, `backBufferLength: 10`, `maxBufferSize: 20*1024*1024`, `liveSyncDurationCount: 5`, `enableWorker: false` on Hisense UA, `capLevelToPlayerSize: true`, hard cap height ≤1080.

### 1.3 Audio drifts behind video

| Cause | Where | Why |
|---|---|---|
| **No A/V drift options** | `buildHlsConfig` | Missing `maxAudioFramesDrift`, `stretchShortVideoTrack`. |
| **No drift monitor** | — | Never compares `video.buffered` vs audio; never seeks to resync. |
| **mpegts.js on TV** | CASE 2 ~457–479 | JS demux of MPEG-TS on weak MSE is a common A/V desync source. Prefer backend remux to HLS (`ffmpeg -c copy`) and play HLS on TV. |
| **Native HLS not tried** | Always Hls.js if `Hls.isSupported()` | VIDAA often has usable native HLS (`video.canPlayType('application/vnd.apple.mpegurl')`). Native can sync A/V better; keep Hls.js as fallback. |

**Fix:** add `maxAudioFramesDrift: 1`, `stretchShortVideoTrack: true`, `nudgeMaxRetry: 8` (already), `maxBufferHole: 0.5` (already). Every 5s while playing, if `|audioEnd - videoEnd| > 0.35s` for 2 samples → small `video.currentTime = video.currentTime` nudge or `hls.recoverMediaError()`; if still drifting → reload current source. Prefer native HLS on Hisense; for `/mpegts` URLs use backend remux endpoint instead of mpegts.js on TV.

### 1.4 No multi-source failover yet

Channels expose a single `url`. Error path retries the **same** URL 3 times then shows standby (~443–447). No ordered backup list, no health score, no S1/S2 badge.

---

## 2. Data: channels-with-backups.json

Path: `docs/grokbot/channels-with-backups.json` (also `/workspace/tvapp/free-iptv/`).

Schema per channel:
```json
{
  "id": "en-dw",
  "name": "DW English",
  "group": "English-News",
  "language": "English",
  "logo": "https://...",
  "tvg_id": "DWEnglish.de",
  "sources": [
    {"url": "...", "type": "hls", "max_res": "1080p", "headers": {}},
    {"url": "...", "type": "hls", "max_res": "1080p", "headers": {}}
  ],
  "primary_res": "1080p",
  "source_count": 2,
  "legitimacy": "official"
}
```

Stats (probed 2026-10-27): **47** legal channels; **14** with 2–3 live backups (Formula, Imedi, 1TV, 2TV, DW RU/EN, Current Time, Smotrim×5, TRT, Al Jazeera). Others have one verified source — quality downgrade inside the master still applies; background health can later discover alts.

**Drop from default playlist:** any channel with no legal source (mcquack Match/Setanta/etc., dead Pirveli / Euronews GE / Rossiya 1/24 unless a legal URL appears). Keep them only if user explicitly re-adds as Custom.

---

## 3. Failover design

### 3.1 Per-channel source list
- Load `sources[]` ordered by probed height desc.
- Runtime state: `sourceIndex`, `lastGoodIndex`, health map.

### 3.2 Health scoring (client + optional backend)
Per source, maintain:
- `startupMs` (manifest→first frame)
- `stallCount` (rolling 30s)
- `fragErrors` / `manifestErrors`
- `estimatedBitrate`
- `score = 100 - stalls*15 - fragErrors*5 - clamp(startupMs/1000,0,30)`  
Promote `lastGood` when score ≥ 70 after 20s stable play.

### 3.3 Automatic switch triggers
Switch to next source when any of:
1. Fatal HLS/mpegts error after quality already at lowest level  
2. `stallCount > 2` in 30s  
3. `video.readyState < 3` and `currentTime` unchanged for **8s** while not paused  
4. Manifest/playlist HTTP **4xx/5xx** (except intentional **410** = stop, do not failover)  
5. Client retries on **same** source exhausted (2 attempts) after ABR already floored

**Before switching sources:** drop one quality level (or jump to lowest) and wait 3s. Only then advance `sourceIndex`.

Wrap around once; then show “Stream unavailable” OSD. Never call `playStream` with a stale session.

### 3.4 Backend
- Extend channel objects from backups JSON: `sources`, `logo`, drop illegal-only entries.
- `GET /api/iptv/channels` returns `sources` array (and keep `url` = sources[0].url for compat).
- `GET /api/stream/health?channel_id=&url=` — HEAD/GET first 2KB of manifest, return `{ok, http, ttfb_ms}`. Cache 60s.
- Persist `last_good_source` per channel in memory (or small JSON under `backend/.stream_health.json`).
- Background task every 5–10 min re-probes sources marked dead; revive if ok.
- Cast path: pick `last_good` or sources[0]; include `source_index` + `sources_total` in WS `playback_command` so TV can badge S1/S2.

### 3.5 UI badge
On TV OSD and phone now-playing: small `S1` / `S2` / `S3` badge = active source index+1. Update on failover.

---

## 4. Concrete code changes for Antigravity

### 4.1 `static/tv.html`
1. Add `let playSessionId = 0`, `let retryTimer = null`, `let stallTimer = null`, `let driftTimer = null`, `let sourceIndex = 0`, `let sourceList = []`.
2. Rewrite `destroyPlayers()` to:
   - `clearTimeout(retryTimer); clearInterval(stallTimer); clearInterval(driftTimer)`
   - stop/detach/destroy hls + mpegts (existing)
   - `video.pause(); video.removeAttribute('src'); video.load()`
   - do **not** clear `playSessionId` (callers bump it)
3. `playStream(url, title, logoUrl, opts)` where `opts = {sources, sourceIndex, session}`:
   - bump `playSessionId`; capture `const session = ++playSessionId`
   - set `sourceList` / `sourceIndex`
   - destroyPlayers(); then attach
4. Prefer **native HLS** on Hisense if `video.canPlayType('application/vnd.apple.mpegurl')` and URL is m3u8; else Hls.js with TV config:
```js
{
  enableWorker: false,
  lowLatencyMode: false,
  maxBufferLength: 24,
  maxMaxBufferLength: 48,
  backBufferLength: 10,
  maxBufferSize: 20*1024*1024,
  maxBufferHole: 0.5,
  nudgeMaxRetry: 8,
  maxAudioFramesDrift: 1,
  stretchShortVideoTrack: true,
  capLevelToPlayerSize: true,
  capLevelOnFPSDrop: true,
  startLevel: 0,
  abrBandWidthFactor: 0.7,
  abrBandWidthUpFactor: 0.5,
  liveSyncDurationCount: 5,
  liveMaxLatencyDurationCount: 14,
  liveDurationInfinity: true,
}
```
   After MANIFEST_PARSED: remove levels with height > 1080; start at lowest.
5. Gate every handler: `if (session !== playSessionId) return;`
6. Stall watchdog + drift check intervals (clear on destroy).
7. `failoverToNextSource(session, reason)` — downgrade first, then next source, update OSD `S2`.
8. Treat HTTP 410 as session end only (no failover, no retry).
9. MPEG-TS on TV: if URL looks like mpegts, request `/api/stream/remux?url=…` HLS instead of mpegts.js when endpoint exists; else keep mpegts.js with `liveBufferLatencyChasing: false`, `enableWorker: false`, `enableStashBuffer: true`, modest stash.

### 4.2 `static/app.js`
- Render channels from `sources`; show backup count.
- `castChannel`: send channel id (backend picks source); debounce 500ms.
- Show S-badge from playback status events if available.
- Pre-warm: only HEAD `sources[0]` (or last-good), still `{once:true}`.

### 4.3 Backend
- `iptv_manager.load_default_playlist`: merge `docs/grokbot/channels-with-backups.json` (or `playlists/channels-with-backups.json`). Set `url`, `sources`, `logo`. Exclude channels not in pack unless Custom.
- `/api/stream/health` probe + last-good cache.
- Optional `/api/stream/remux` ffmpeg `-c copy` to HLS in temp (if ffmpeg present); document if missing.
- WS play payload: `{type, action, url, title, logo, source_index, sources_total, channel_id}`.

### 4.4 Self-test
Add `scripts/selftest_playback.py` or `static/selftest.html` that:
- GETs `/api/iptv/channels` and asserts every channel has `sources` length ≥ 1
- Probes health for first 5 channels
- Unit-tests session token logic if extracted to a small JS module  
Print tunnel / LAN URL when backend runs.

---

## 5. Test checklist (Hisense + phone)

1. Cold start backend; open `/tv` on Hisense, phone controller on same network / tunnel.  
2. Play DW English → OSD shows channel + `S1`.  
3. Rapidly switch DW → Al Jazeera → Formula (5×): **no flash of previous channel**, no wrong audio.  
4. Kill Wi-Fi briefly or block CDN: within ~8–12s quality drops then `S2` if backup exists; OSD updates.  
5. Leave a channel 10+ minutes: no growing A/V drift; if drift forced (throttle), auto-resync within ~15s.  
6. `/api/iptv/channels` JSON includes `sources` arrays.  
7. Dead/illegal-only channels absent from default list.  
8. Memory: after 20 switches, TV still responsive (no MSE crash).  
9. 410 on channel switch: old segments stop; no reconnect storm in backend logs.

---

## 6. Out of scope / notes
- Do not send MQTT/remote commands to the Hisense system UI.  
- Do not reintroduce pirated sports/movie restreams.  
- Georgian CDNs may be geo-sensitive; backups probed from outside GE still returned 200 for Formula/Imedi/1TV/2TV on 2026-10-27.
