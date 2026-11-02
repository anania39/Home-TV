media_file = r"backend/media_resolver.py"
with open(media_file, "r", encoding="utf-8") as f:
    text = f.read()

crlf = "\r\n" in text
text_lf = text.replace("\r\n", "\n")

target = """        def _extract():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'socket_timeout': 8,
            }
            node_exe = r"C:\\Users\\Anania Light Laptop\\Downloads\\Blue Ocean\\.tools\\node\\node.exe"
            if os.path.exists(node_exe):
                node_dir = os.path.dirname(node_exe)
                if node_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")
                ydl_opts['js_runtimes'] = {'node': {'path': node_exe}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(_extract)"""

replacement = """        def _extract():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'socket_timeout': 8,
                'remote_components': ['ejs:github'],
                'extractor_args': {'youtube': {'player_client': ['web', 'web_embedded', 'mweb', 'android', 'ios']}},
            }
            node_exe = r"C:\\Users\\Anania Light Laptop\\Downloads\\Blue Ocean\\.tools\\node\\node.exe"
            if os.path.exists(node_exe):
                node_dir = os.path.dirname(node_exe)
                if node_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")
                ydl_opts['js_runtimes'] = {'node': {'path': node_exe}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(_extract)"""

target_except = """        except Exception as e:
            logger.warning(f"YouTube extraction error for {url}: {e}")

        return {"resolved": False, "error": "Failed to extract YouTube stream"}"""

replacement_except = """        except Exception as e:
            logger.warning(f"Local YouTube extraction notice for {url}: {e}")
            # Residential relay fallback for Cloud VPS instances:
            # If running on cloud and hit by YouTube datacenter IP challenge,
            # query the Home PC Hub residential tunnel to resolve without bot blocks.
            try:
                ep_file = Path(__file__).resolve().parent.parent / "endpoint.json"
                if ep_file.exists():
                    ep_data = json.loads(ep_file.read_text(encoding="utf-8"))
                    hub_tunnel = ep_data.get("hub_url")
                    if hub_tunnel and "trycloudflare.com" in hub_tunnel:
                        async with httpx.AsyncClient(timeout=9.0, verify=False) as c:
                            r = await c.get(
                                f"{hub_tunnel}/api/media/resolve",
                                params={"url": url},
                                headers={"bypass-tunnel-reminder": "true"}
                            )
                            if r.status_code == 200:
                                data = r.json()
                                if data.get("resolved") and data.get("stream_url"):
                                    logger.info(f"YouTube stream resolved via Home PC Hub residential tunnel: {data.get('title')}")
                                    return data
            except Exception as relay_err:
                logger.debug(f"Home hub delegation notice: {relay_err}")

        return {"resolved": False, "error": "Failed to extract YouTube stream"}"""

assert target in text_lf, "Target not found in media_resolver.py"
assert target_except in text_lf, "Target_except not found in media_resolver.py"

text_lf = text_lf.replace(target, replacement).replace(target_except, replacement_except)
if crlf:
    text_lf = text_lf.replace("\n", "\r\n")

with open(media_file, "w", encoding="utf-8") as f:
    f.write(text_lf)

print("Successfully updated backend/media_resolver.py!")
