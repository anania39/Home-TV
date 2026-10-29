import asyncio
import time
import httpx
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.dlna_controller import dlna_controller

async def test_live_transitions():
    av_url = "http://192.168.50.249:38400/upnp/control/mingusavtr"
    base = "http://127.0.0.1:8000"
    
    channels = [
        ("ge-setanta1", "Setanta Sports 1 HD"),
        ("ru-matchpremier", "Match Premier HD"),
        ("ge-setanta2", "Setanta Sports 2 HD"),
        ("ge-silkuniversal", "Silk Universal HD"),
    ]
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for idx, (cid, cname) in enumerate(channels):
            print(f"\n==========================================")
            print(f"[{idx+1}/{len(channels)}] Switching to: {cname} ({cid})")
            print(f"==========================================")
            t0 = time.time()
            res = await client.post(f"{base}/api/iptv/cast/{cid}?device_id=tv_192_168_50_249")
            elapsed = time.time() - t0
            print(f"  Switch API response in {elapsed:.2f}s: {res.status_code}")
            data = res.json()
            print(f"  Mode: {data.get('mode')}, URL: {data.get('url')[:60]}...")
            
            # Monitor playback state for 4 seconds
            for s in range(4):
                await asyncio.sleep(1.0)
                info = await dlna_controller.get_transport_info(av_url)
                pos = await dlna_controller.get_position_info(av_url)
                state = info.get("state")
                uri = pos.get("uri", "")[-55:]
                print(f"  T+{s+1}s: state={state} | uri={uri}")
                assert state in ("PLAYING", "TRANSITIONING"), f"Expected PLAYING but got {state}"
                
    print("\n==========================================")
    print("ALL 4 CHANNEL SWITCHES COMPLETED WITH 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(test_live_transitions())
