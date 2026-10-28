# 📺 TV Hub — Smart TV Cast & Remote Control

**TV Hub** is a lightweight, local-network media casting and remote control web application tailored for older smart TVs (such as Hisense VIDAA OS, Opera TV, and standard DLNA/UPnP TVs) that no longer receive firmware updates or lack modern streaming apps.

---

## ⚡ Permanent Access Links

| Interface | Description | Permanent URL |
|---|---|---|
| 🌟 **Permanent Web Controller (Phone / PC)** | Hosted on GitHub Pages CDN — **never expires** | **[https://anania39.github.io/Home-TV/](https://anania39.github.io/Home-TV/)** |
| 📺 **Permanent TV Web Receiver** | Fullscreen player for TV browser | **[https://anania39.github.io/Home-TV/tv.html](https://anania39.github.io/Home-TV/tv.html)** |
| 🏠 **Local Wi-Fi Hub** | Ultra-low latency direct LAN connection | **[http://192.168.50.250:8000](http://192.168.50.250:8000)** |
| 🌐 **GitHub Repository** | Full source code, channels & assets | **[https://github.com/anania39/Home-TV](https://github.com/anania39/Home-TV)** |

---

## 🏆 NEW: Live Sports Streaming Aggregator (FBStream Integration)

Integrated live sports match streaming aggregator with zero ads and automated conversion to **Tbilisi Local Time** (`Asia/Tbilisi`, UTC+4):

1. **8 Sport Categories**:
   - ⚽ **Football** (Premier League, Champions League, La Liga, Serie A, etc.)
   - 🏉 **Rugby** (Fox NRL, Top 14, Six Nations)
   - 🏀 **Basketball** (NBA, EuroLeague)
   - 🎾 **Tennis** (ATP & WTA Tournaments)
   - 🏎️ **Formula 1** (Practice, Qualifying, Grand Prix)
   - 🥊 **MMA & UFC** (UFC Fight Nights, Pay-per-views)
   - 🥊 **Boxing** (Championship Bouts)
   - 🎮 **Cyber Sport / Others** (Esports, Darts, Cricket, Golf)

2. **Live & Upcoming Match Scheduling**:
   - **🔴 Live Now Filter**: Pulsing indicator badge displaying currently live fixtures.
   - **⏳ Upcoming Schedule Filter**: Displays matches scheduled for Today, Tomorrow, and upcoming dates with exact Tbilisi kickoff times.
   - **🕒 Real-Time Tbilisi Clock (UTC+4)**: Synchronized status banner showing live Tbilisi time.

3. **Ad-Free Clean Player & Multi-Stream Selection**:
   - **Zero Popups / Zero Redirects**: Embedded through a sanitized proxy (`/api/sports/player/{stream_slug}`) stripping malicious scripts, ad trackers (`eludestop.cyou`, `budgetezy.org`), and popunders (`popundersPerIP`).
   - **Multiple Stream Links**: Instant switcher for Stream 1 (Primary 🌟), Stream 2, Stream 3, Stream 4.
   - **📺 1-Tap Big Screen TV Cast**: Direct shortcut from any match card to cast relevant high-definition native sports channels (Setanta Sports 1/2 HD, Silk Universal HD, Georgian Rugby TV, Match TV, etc.) directly to your Hisense VIDAA TV or Google TV!

---

## 📺 Curated 98 Free Working IPTV Channels Included

* **🇬🇪 Georgian (ქართული არხები - 17 Channels)**:
  - **Setanta Sports 1 HD** (`ge-setanta1`)
  - **Setanta Sports 2 HD** (`ge-setanta2`)
  - **Silk Universal HD** (`ge-silkuniversal`)
  - **Rugby TV (რაგბი TV)** (`ge-rugby`)
  - **Imedi HD (იმედი)** (`ge-imedi`)
  - **Rustavi 2 HD (რუსთავი 2)** (`ge-rustavi2`)
  - **1TV პირველი არხი** (`ge-1tv`)
  - **Formula TV (ფორმულა)** (`ge-formula`)
  - **GDS TV (ჯიდიესი)** (`ge-gds`)
  - **Comedy Channel (კომედი)** (`ge-comedy`)
  - **POSTV** (`ge-postv`)
  - **Marao TV (მარაო)** (`ge-marao`)
  - **Adjara TV (აჭარა)** (`ge-adjara`)
  - **Palitra TV (პალიტრა)** (`ge-palitra`)
  - **Kavkasia TV (კავკასია)** (`ge-kavkasia`)
  - **Rioni TV (რიონი)** (`ge-rioni`)
  - **Ertsulovneba (ერთსულოვნება)** (`ge-ertsulovneba`)

* **⚽ Sports Feeds (24 Channels)**:
  - **Setanta Sports 1 HD & 2 HD**
  - **Матч Премьер HD & Матч ТВ HD**
  - **Матч! Футбол 1 HD, 2 HD, 3 HD**
  - **Матч! Игра HD, Арена HD, Боец HD, Страна HD**
  - **KHL ТВ HD & KHL Prime HD**
  - **Viju+ Sport HD**
  - **Extreme Sports HD**
  - **UDAR HD & Бокс ТВ HD**
  - **Sport 1 HD, Sport 2 HD, Sport 3 HD, Sport 1 Baltic HD**
  - **Red Bull TV HD**

* **🎬 Movies & Series (27 Channels)**:
  - **Дом Кино HD & Дом Кино Премиум HD**
  - **Кинохит HD, Киномикс HD, Киносемья HD**
  - **Кинокомедия HD, Киносвидание HD, Киноужас HD**
  - **Viju TV 1000 HD, Viju TV 1000 Action HD**
  - **Viju+ Premiere HD, Megahit HD, Comedy HD, Serial HD**
  - **Amedia Premium HD, Amedia 1 HD, Amedia Hit HD**
  - **Fox HD & Fox Life HD**
  - **КиноТВ HD, Кинопоказ HD, Мужское кино HD, Родное кино HD**
  - **Еврокино HD, Русский Бестселлер HD, Русский Детектив HD**

* **🧠 Documentaries & Science (18 Channels)**:
  - **Discovery Channel HD, National Geographic HD, Nat Geo Wild HD**
  - **Animal Planet HD, Investigation Discovery HD, TLC HD**
  - **Наука 2.0 HD, Travel Channel HD, Travel XP HD**
  - **Viju Explore HD, Viju History HD, Viju+ Planet HD, Da Vinci HD**
  - **Доктор HD, Глазами Туриста HD, В мире животных HD, 365 дней ТВ**

* **🇬🇧 English Global & Music (12 Channels)**:
  - **BBC News UK HD, Bloomberg TV HD, DW News English HD**
  - **Stingray CMusic HD, Music Box HD, Red Bull TV HD**

---

## 🌟 Key Features

### 1. 📡 Universal DLNA / UPnP Casting
* **Zero TV App Installation**: Uses your TV's built-in **Digital Media Renderer (DMR)**. Your Hisense TV at `192.168.50.249:38400` automatically switches and plays streams sent from your phone!
* **Stream Compatibility Proxy**: Older TVs often fail when playing modern IPTV or HTTPS streams due to expired root certificates, CORS issues, or strict headers. TV Hub automatically routes streams through a built-in proxy (`/api/stream/proxy`) ensuring smooth playback on legacy TV hardware.

### 2. 📺 Full IPTV Player (VLC-Like Streaming)
* **Curated Channels**: Pre-loaded with working global live channels (NASA TV HD, Red Bull TV, DW English News, CBC News, Heartland 24/7, Murdoch Mysteries, Comedy, Kids).
* **M3U / M3U8 Playlist Import**: Upload your own IPTV `.m3u` file, paste M3U text, or provide an M3U URL.
* **Instant Zapping**: Tap any channel on your smartphone to play it immediately on the TV.

### 3. 🎮 Smartphone Virtual Remote Control
* **Tactile D-Pad**: Directional arrows (Up, Down, Left, Right) + center **OK** button with haptic feedback vibration.
* **Navigation Keys**: Back, Home, Menu, Input/Source, Power.
* **Playback Controls**: Play, Pause, Stop, Seek (-15s Rewind / +30s Fast Forward).
* **Dual Rockers**: Volume Up/Down + Mute, Channel Up/Down.
* **Dual Protocol**: Communicates via **UPnP RenderingControl** for instant volume & playback, plus **Hisense VIDAA RemoteNow MQTT** on port `36669`.

### 4. 🔒 Zero-Friction Wi-Fi Authentication
* **Local Subnet Trust**: As long as your smartphone and your TV sit on the same Wi-Fi network (`192.168.50.x`), you are automatically authenticated. No login forms, passwords, or cloud accounts needed.
* **Private & Offline-Capable**: Runs entirely on your local home network without external cloud tracking.

### 5. 🖥️ TV Web Receiver Mode (`/tv`)
* If you open `http://192.168.50.250:8000/tv` in the TV's built-in web browser, the TV turns into an interactive 10-foot screen with an ambient clock, HLS.js video player, and auto-fading On-Screen Display (OSD) channel banner.

---

## 🚀 How to Run

### Option A: Double-Click (Windows)
Double-click `run.bat` in this folder.

### Option B: Terminal Command
```powershell
python run.py
```

The server starts on port `8000` and automatically scans your local Wi-Fi network for your Hisense TV and other DLNA renderers.

---

## 🛠️ Stream Playback & Architecture Specifications

### 1. Strict Channel Switch Isolation (`ActiveStreamSessionManager`)
* **Root Cause Solved**: On Hisense VIDAA OS, calling UPnP `Stop` followed quickly by `SetAVTransportURI` does not immediately kill the previous media player process (`mediaPlayerId`). The TV's old player continues fetching its HLS playlist and video segments concurrently on its open TCP sockets while the new player begins fetching its stream, causing the TV hardware decoder to alternate between frames from the old channel and new channel for several minutes.
* **Instant Termination (HTTP 410 Gone)**: The backend proxy tracks active stream sessions per device IP (`target_ip -> {sid, stream_url}`). Every rewritten `.m3u8` segment is tagged with `&sid=...`. As soon as a channel switch occurs, any subsequent segment requests from the old session or obsolete channel path are immediately rejected with **HTTP 410 (Gone)** and TCP connection close. This triggers an instant fatal error in the TV's old background player, forcing it to tear down within 50ms.
* **HTML5 MediaSource Flush**: In `/tv`, `destroyPlayers()` performs a complete pipeline flush (`video.pause(); video.removeAttribute('src'); video.src = ''; video.load()`) before attaching a new HLS session, preventing browser MSE buffer corruption.

### 2. Same-Origin Stream Proxy (`/api/stream/proxy` and `/proxy`)
* **Relative URLs by Default**: Upstream HLS playlists (`.m3u8`) are rewritten so segment and key URLs use same-origin relative paths (e.g. `/api/stream/proxy?url=...`). This guarantees that when accessed via Cloudflare Tunnels (`trycloudflare.com`) or off-LAN, no requests fail against an unreachable private LAN IP (`192.168.50.250`).
* **Config Flag**: Setting `FORCE_ABSOLUTE_LAN_URL=true` in the environment restores absolute LAN URLs if explicitly needed for legacy hardware renderers.

### 2. Tuned HLS Player (`/tv` Web Receiver)
* **Pinned Version**: Standardized on stable `hls.js@1.5.17`.
* **Standard Non-LL Live Mode**: `lowLatencyMode` is set to `false`. Live IPTV streams are not low-latency LL-HLS; standard non-LL mode with deeper buffers (`maxBufferLength: 40-60`, `liveSyncDurationCount: 4`) avoids continuous buffering on weak Wi-Fi.
* **Network-Aware ABR**: Caps level to player dimensions (`capLevelToPlayerSize: true`), starts at lowest/second-lowest level on multi-bitrate streams (`startLevel: 0`), and dynamically adjusts bandwidth estimation via `navigator.connection`.
* **Resilience & Backoff**: Exponential backoff retries (1s, 2s, 4s) on network/media errors, with clear visual error state if upstream feeds are unreachable.

### 3. MPEG-TS vs HLS Stream Transmuxing
* **Browser MSE Support**: Raw MPEG-TS streams (such as `.itdc.ge/.../mpegts`) cannot be natively played inside HTML5 `<video>` tags.
* **Lightweight Transmuxing**: The TV receiver incorporates `mpegts.js@1.7.3`, a lightweight client-side MSE demuxer that transmuxes raw MPEG-TS into fragmented MP4 in real-time. If the browser lacks MSE or the stream is dead, an informative OSD notification guides the user.

### 4. Verified Brand Channel Logos
* Real, HTTP-verified brand logos from Wikimedia Commons, Imgur, and iptv-org replace all placeholder SVGs.
* **Initials Fallback**: If a remote logo fails to load, a clean 2-letter monogram avatar (derived strictly from the channel name) is displayed.

---

## 📂 Project Structure

```text
tv hub/
├── backend/
│   ├── app.py                 # FastAPI server, REST API, WebSocket sync & static routes
│   ├── config.py              # Local IP detection & subnet authentication
│   ├── discovery.py           # Multicast SSDP device discovery scanner
│   ├── dlna_controller.py     # UPnP AVTransport & RenderingControl SOAP client
│   ├── hisense_remote.py      # Hisense VIDAA MQTT protocol handler (port 36669)
│   ├── iptv_manager.py        # M3U playlist parser, channel catalog & filters
│   ├── stream_proxy.py        # CORS & legacy TLS streaming proxy
│   └── websocket_manager.py   # Real-time WebSocket sync between Phone & TV
├── static/
│   ├── index.html             # Smartphone Web App (Mobile Controller)
│   ├── tv.html                # TV Browser Receiver Screen
│   ├── style.css              # Dark glassmorphism responsive theme
│   └── app.js                 # Frontend touch & WebSocket controller logic
├── playlists/
│   └── default_channels.m3u   # Pre-configured working live IPTV channels
├── media/                     # Directory for uploaded local videos/music
├── run.py                     # Python server launcher
├── run.bat                    # 1-click Windows starter
└── README.md                  # Documentation
```
