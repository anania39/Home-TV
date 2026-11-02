media_file = r"backend/media_resolver.py"
with open(media_file, "r", encoding="utf-8") as f:
    text = f.read()

crlf = "\r\n" in text
text_lf = text.replace("\r\n", "\n")

target = """            try:
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
                logger.debug(f"Home hub delegation notice: {relay_err}")"""

replacement = """            try:
                hub_tunnel = None
                ep_file = Path(__file__).resolve().parent.parent / "endpoint.json"
                if ep_file.exists():
                    ep_data = json.loads(ep_file.read_text(encoding="utf-8"))
                    cand = ep_data.get("hub_url")
                    if cand and "trycloudflare.com" in cand:
                        hub_tunnel = cand
                if not hub_tunnel:
                    async with httpx.AsyncClient(timeout=3.0) as gc:
                        gr = await gc.get("https://raw.githubusercontent.com/anania39/Home-TV/main/endpoint.json?t=" + str(int(time.time())))
                        if gr.status_code == 200:
                            g_data = gr.json()
                            cand = g_data.get("hub_url")
                            if cand and "trycloudflare.com" in cand:
                                hub_tunnel = cand

                if hub_tunnel:
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
                logger.debug(f"Home hub delegation notice: {relay_err}")"""

assert target in text_lf, "Target not found in media_resolver.py"
text_lf = text_lf.replace(target, replacement)
if crlf:
    text_lf = text_lf.replace("\n", "\r\n")

with open(media_file, "w", encoding="utf-8") as f:
    f.write(text_lf)

print("Successfully updated backend/media_resolver.py with GitHub endpoint raw fallback!")
