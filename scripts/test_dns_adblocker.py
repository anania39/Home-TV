import asyncio
import socket
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.dns_adblocker import dns_adblocker

async def test_engine():
    print("Starting DNS Ad-Blocker on 0.0.0.0:53...")
    await dns_adblocker.start("0.0.0.0", 53)
    assert dns_adblocker._running, "DNS Ad-Blocker failed to start!"
    print("DNS Ad-Blocker running successfully!")
    
    # Send test query for doubleclick.net (should be blocked to 0.0.0.0)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(2.0)
    query_ad = b"\xaa\xbb\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0bdoubleclick\x03net\x00\x00\x01\x00\x01"
    client.sendto(query_ad, ("127.0.0.1", 53))
    resp_ad, _ = client.recvfrom(1024)
    print("Ad query response length:", len(resp_ad))
    print("Ad query sinkhole IP:", [int(b) for b in resp_ad[-4:]])
    assert resp_ad[-4:] == b"\x00\x00\x00\x00", "Expected 0.0.0.0 sinkhole response!"
    
    # Send test query for google.com (should be resolved upstream)
    query_clean = b"\xcc\xdd\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01"
    client.sendto(query_clean, ("127.0.0.1", 53))
    resp_clean, _ = client.recvfrom(1024)
    print("Clean query response length:", len(resp_clean), "TXID match:", resp_clean[:2] == b"\xcc\xdd")
    assert resp_clean[:2] == b"\xcc\xdd", "Expected matching TXID!"
    
    # Test per-device toggle: disable for 127.0.0.1
    dns_adblocker.set_device_enabled("127.0.0.1", False)
    client.sendto(query_ad, ("127.0.0.1", 53))
    resp_unblocked, _ = client.recvfrom(1024)
    print("Unblocked device response length:", len(resp_unblocked))
    
    status = dns_adblocker.get_status()
    print("DNS AdBlocker status:", status["stats"])
    
    client.close()
    dns_adblocker.stop()
    print("ALL DNS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_engine())
