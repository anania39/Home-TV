import asyncio
import time
import sys
import os
sys.path.insert(0, os.path.abspath("."))
import httpx
from backend.dlna_controller import dlna_controller

async def switch_channel_smooth(from_cid, to_cid):
    base = "http://127.0.0.1:8000"
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Cast first channel to TV
        print(f"\n[1] Casting first channel: {from_cid}...")
        r1 = await client.post(f"{base}/api/iptv/cast/{from_cid}?device_id=tv_192_168_50_249")
        print(f"  First channel response: {r1.status_code} {r1.json()}")
        
        # Let it play for 5 seconds
        print("  Playing for 5s...")
        await asyncio.sleep(5.0)
        
        # Now switch to second channel
        print(f"\n[2] Switching to second channel: {to_cid}...")
        t0 = time.time()
        r2 = await client.post(f"{base}/api/iptv/cast/{to_cid}?device_id=tv_192_168_50_249")
        elapsed = time.time() - t0
        print(f"  Second channel switch response in {elapsed:.2f}s: {r2.status_code} {r2.json()}")
        
        # Monitor TV state for 5 seconds
        av_url = "http://192.168.50.249:38400/upnp/control/mingusavtr"
        for i in range(5):
            await asyncio.sleep(1.0)
            info = await dlna_controller.get_transport_info(av_url)
            pos = await dlna_controller.get_position_info(av_url)
            print(f"  T+{i+1}s: state={info.get('state')} uri={pos.get('uri')[-40:]}")

if __name__ == "__main__":
    asyncio.run(switch_channel_smooth("ge-imedi", "ge-setanta1"))
