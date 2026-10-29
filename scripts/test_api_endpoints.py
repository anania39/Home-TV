import sys
import urllib.request
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import json
import socket

# 1. Test /api/adblock/status
res = urllib.request.urlopen("http://127.0.0.1:8000/api/adblock/status")
status = json.loads(res.read())
print("Adblock status:", status.get("global_enabled"), "running:", status.get("running"), "port:", status.get("port"))
print("Blocked domains in memory:", status.get("blocked_domains_count"))

# 2. Test /api/network/devices
res = urllib.request.urlopen("http://127.0.0.1:8000/api/network/devices")
data = json.loads(res.read())
devices = data.get("devices", [])
print(f"\nDiscovered {len(devices)} network devices:")
for d in devices:
    print(f"  * {d['ip']} | {d['name']} | type: {d['type']} | adblock: {d['adblock_enabled']}")

# 3. Test DNS query to port 53 (sinkhole check for ad domain)
def build_query(domain):
    txn_id = b"\xaa\xbb"
    flags = b"\x01\x00"
    counts = b"\x00\x01\x00\x00\x00\x00\x00\x00"
    qname = b""
    for part in domain.split("."):
        qname += bytes([len(part)]) + part.encode("ascii")
    qname += b"\x00"
    qtype_qclass = b"\x00\x01\x00\x01"
    return txn_id + flags + counts + qname + qtype_qclass

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(2.0)
client.sendto(build_query("doubleclick.net"), ("127.0.0.1", 53))
resp, _ = client.recvfrom(512)
print(f"\nDNS Sinkhole Query for 'doubleclick.net': response length {len(resp)} bytes")
if b"\x00\x00\x00\x00" in resp[-4:]:
    print("✓ VERIFIED: Sinkholed to 0.0.0.0 (Ad blocked successfully!)")

# 4. Check status update
res = urllib.request.urlopen("http://127.0.0.1:8000/api/adblock/status")
status = json.loads(res.read())
print("Live stats after ad query:", status.get("stats"))
print("Recent blocks log:", status.get("recent_blocks"))

# 5. Test individual device adblock toggle
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/network/device/192.168.50.237/adblock",
    data=json.dumps({"enabled": False}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
res = urllib.request.urlopen(req)
toggle_resp = json.loads(res.read())
print("\nDevice toggle response for 192.168.50.237 (off):", toggle_resp)

req2 = urllib.request.Request(
    "http://127.0.0.1:8000/api/network/device/192.168.50.237/adblock",
    data=json.dumps({"enabled": True}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
res2 = urllib.request.urlopen(req2)
toggle_resp2 = json.loads(res2.read())
print("Device toggle response for 192.168.50.237 (back on):", toggle_resp2)
