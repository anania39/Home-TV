from pathlib import Path

def patch_app():
    p = Path("backend/app.py")
    text = p.read_text(encoding="utf-8")

    target = '''        # Extract full metadata (audio tracks, subtitles, duration) from HLS manifest
        hls_meta = await media_resolver.extract_hls_metadata(manifest_url, custom_headers or {})
        if hls_meta.get("audio_tracks") and not resolved.get("audio_tracks"):
            resolved["audio_tracks"] = hls_meta["audio_tracks"]
        if hls_meta.get("subtitles") and not resolved.get("subtitles"):
            resolved["subtitles"] = hls_meta["subtitles"]
        if hls_meta.get("duration", 0) > 0 and resolved.get("duration", 0) <= 0:
            resolved["duration"] = hls_meta["duration"]
            resolved["duration_str"] = media_resolver._format_duration(hls_meta["duration"])'''

    replacement = '''        # Extract full metadata (audio tracks, subtitles, duration, standard qualities) from HLS manifest
        hls_meta = await media_resolver.extract_hls_metadata(manifest_url, custom_headers or {})
        if hls_meta.get("audio_tracks") and not resolved.get("audio_tracks"):
            resolved["audio_tracks"] = hls_meta["audio_tracks"]
        if hls_meta.get("subtitles") and not resolved.get("subtitles"):
            resolved["subtitles"] = hls_meta["subtitles"]
        if hls_meta.get("duration", 0) > 0 and resolved.get("duration", 0) <= 0:
            resolved["duration"] = hls_meta["duration"]
            resolved["duration_str"] = media_resolver._format_duration(hls_meta["duration"])
        if hls_meta.get("qualities") and len(hls_meta["qualities"]) > 1:
            resolved["qualities"] = hls_meta["qualities"]
            for q in hls_meta["qualities"]:
                if q not in q_urls:
                    if q == "Auto":
                        q_urls[q] = f"http://{SERVER_IP}:{PORT}/api/stream/proxy?url={quote(manifest_url, safe='')}&sid={active_sid}"
                    else:
                        q_urls[q] = f"http://{SERVER_IP}:{PORT}/api/stream/proxy?url={quote(manifest_url, safe='')}&q={q}&sid={active_sid}"
            tier_alias_map = {"1080p": "804p", "720p": "536p", "480p": "358p", "360p": "268p", "240p": "178p"}
            for std_q, wide_q in tier_alias_map.items():
                if std_q in q_urls and wide_q not in q_urls:
                    q_urls[wide_q] = q_urls[std_q]
                elif wide_q in q_urls and std_q not in q_urls:
                    q_urls[std_q] = q_urls[wide_q]
            resolved["quality_urls"] = q_urls'''

    if target in text:
        text = text.replace(target, replacement)
        p.write_text(text, encoding="utf-8")
        print("backend/app.py updated successfully")
    else:
        print("Error: target not found in backend/app.py")

if __name__ == "__main__":
    patch_app()
