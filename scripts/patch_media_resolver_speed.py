import re

with open("backend/media_resolver.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update extractor args
old_opts = "'extractor_args': {'youtube': {'player_client': ['web', 'web_embedded', 'mweb', 'android', 'ios']}},"
new_opts = "'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'tv', 'web_embedded']}},"
if old_opts in code:
    code = code.replace(old_opts, new_opts)
    print("Updated extractor_args in media_resolver.py")
else:
    print("Warning: old_opts not matched")

# 2. Reduce residential tunnel timeout from 35.0 to 2.5
old_timeout = 'async with httpx.AsyncClient(timeout=35.0, verify=False) as c:'
new_timeout = 'async with httpx.AsyncClient(timeout=2.5, verify=False) as c:'
if old_timeout in code:
    code = code.replace(old_timeout, new_timeout)
    print("Reduced relay timeout to 2.5s in media_resolver.py")

# 3. Add youtube_id in cloud fallback
old_fb = '''        if yt_id_match:
            vid_id = yt_id_match.group(1)
            return {
                "resolved": True,
                "stream_url": f"https://www.youtube.com/watch?v={vid_id}",
                "title": preferred_title or "YouTube Video",'''

new_fb = '''        if yt_id_match:
            vid_id = yt_id_match.group(1)
            return {
                "resolved": True,
                "stream_url": f"https://www.youtube.com/watch?v={vid_id}",
                "youtube_id": vid_id,
                "title": preferred_title or "YouTube Video",'''

if old_fb in code:
    code = code.replace(old_fb, new_fb)
    print("Added youtube_id to cloud fallback")

with open("backend/media_resolver.py", "w", encoding="utf-8") as f:
    f.write(code)

print("media_resolver patch complete.")
with open("backend/app.py", "r", encoding="utf-8") as f:
    code = f.read()

target = '"stream_url": final_stream_url,'
replacement = '"stream_url": final_stream_url,\n                "youtube_id": resolved.get("youtube_id") or "",'

if target in code:
    code = code.replace(target, replacement, 1)
    with open("backend/app.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Added youtube_id to backend/app.py")
else:
    print("Warning: target stream_url not found in backend/app.py")
