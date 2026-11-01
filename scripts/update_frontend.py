from pathlib import Path

def update_html():
    idx_path = Path("index.html")
    text = idx_path.read_text(encoding="utf-8")

    # 1. Add head scripts
    head_scripts = '''  <!-- Google Cast Web SDK & Hls.js for In-Browser Casting & Playback on ANY Wi-Fi -->
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.17"></script>
  <script src="https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1"></script>
  <link rel="stylesheet" href="static/style.css?v=5.0">'''
    if "cast_sender.js" not in text:
        text = text.replace('<link rel="stylesheet" href="static/style.css?v=3.7">', head_scripts)
        text = text.replace('<link rel="stylesheet" href="static/style.css?v=4.2">', head_scripts)

    # 2. Add web cast button to header
    header_btn = '''          <button id="btn-web-cast" class="btn-icon" title="Cast directly from Browser to any TV on this Wi-Fi">
            <svg viewBox="0 0 24 24"><path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6M2 20h.01"/></svg>
          </button>
          <button id="btn-hub-settings" class="btn-icon" title="Hub Server Connection">'''
    if "btn-web-cast" not in text:
        text = text.replace('<button id="btn-hub-settings" class="btn-icon" title="Hub Server Connection">', header_btn)

    # 3. Add In-App Mobile Video Player Modal
    inapp_modal = '''  <!-- In-App Mobile Video Player (Play channels directly on phone without TV) -->
  <div id="modal-inapp-player" class="modal-backdrop" style="display: none;">
    <div class="modal-card inapp-player-card">
      <div class="modal-header">
        <h3 id="inapp-player-title" style="margin: 0; font-size: 15px; display: flex; align-items: center; gap: 8px;">
          <span style="color: var(--accent-cyan);">📺</span> <span id="inapp-channel-name">Channel Player</span>
        </h3>
        <button id="btn-close-inapp-player" class="btn-icon">✕</button>
      </div>
      <div class="video-container" style="position: relative; width: 100%; background: #000; border-radius: 12px; overflow: hidden; margin: 12px 0;">
        <video id="inapp-video" playsinline controls style="width: 100%; max-height: 280px; display: block;"></video>
      </div>
      <div style="display: flex; gap: 8px; justify-content: space-between; align-items: center;">
        <span id="inapp-stream-status" style="font-size: 12px; color: var(--accent-cyan);">● Direct Stream (Ad-Free)</span>
        <button type="button" id="btn-inapp-switch-tv" class="btn-secondary" style="font-size: 12px; padding: 6px 12px; width: auto;">📺 Cast to TV Instead</button>
      </div>
    </div>
  </div>

  <!-- Hub Connection Modal -->'''
    if "modal-inapp-player" not in text:
        text = text.replace('  <!-- Hub Connection Modal -->', inapp_modal)

    # 4. Bump app.js version
    text = text.replace('static/app.js?v=4.5', 'static/app.js?v=5.0')
    text = text.replace('static/app.js?v=3.9', 'static/app.js?v=5.0')

    idx_path.write_text(text, encoding="utf-8")
    Path("static/index.html").write_text(text, encoding="utf-8")
    print("index.html and static/index.html updated successfully")

if __name__ == "__main__":
    update_html()
