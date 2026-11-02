tunnel_file = r"backend/tunnel.py"
with open(tunnel_file, "r", encoding="utf-8") as f:
    text = f.read()

crlf = "\r\n" in text
text_lf = text.replace("\r\n", "\n")

target = """    data = {
        "hub_url": public_url,
        "local_url": f"http://{SERVER_IP}:{PORT}","""

replacement = """    data = {
        "hub_url": public_url,
        "cloud_hub_url": "https://tvhub.92.5.71.162.sslip.io",
        "local_url": f"http://{SERVER_IP}:{PORT}","""

if target in text_lf:
    text_lf = text_lf.replace(target, replacement)
    if crlf:
        text_lf = text_lf.replace("\n", "\r\n")
    with open(tunnel_file, "w", encoding="utf-8") as f:
        f.write(text_lf)
    print("Successfully updated backend/tunnel.py!")
else:
    print("Target already updated or not found.")
