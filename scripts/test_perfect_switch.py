import asyncio
import time
import httpx
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.dlna_controller import dlna_controller

async def run_switch_test():
    av_url = "http://192.168.50.249:38400/upnp/control/mingusavtr"
    base = "http://127.0.0.1:8000"
    
    print("=== STEP 1: Cast Setanta Sports 1 ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r1 = await client.post(f"{base}/api/iptv/cast/ge-setanta1?device_id=tv_192_168_50_249")
        print("  Setanta 1 Cast:", r1.status_code, r1.json().get("title"))
    
    for i in range(4):
        await asyncio.sleep(1.0)
        info = await dlna_controller.get_transport_info(av_url)
        print(f"  T+{i+1}s: state={info.get('state')}")
        
    print("\n=== STEP 2: Smooth Clean Switch to Match Premier ===")
    t0 = time.time()
    # 1. Send Stop
    stop_ok = await dlna_controller.stop(av_url)
    print(f"  Stop sent: {stop_ok}")
    # 2. Poll for STOPPED state
    for _ in range(8):
        await asyncio.sleep(0.15)
        info = await dlna_controller.get_transport_info(av_url)
        if info.get("state") in ["STOPPED", "NO_MEDIA_PRESENT"]:
            print(f"  TV confirmed STOPPED in {time.time() - t0:.2f}s")
            break
            
    # 3. Cast Match Premier
    async with httpx.AsyncClient(timeout=10.0) as client:
        r2 = await client.post(f"{base}/api/iptv/cast/ru-matchpremier?device_id=tv_192_168_50_249")
        print(f"  Match Premier Cast: {r2.status_code} in {time.time() - t0:.2f}s")
        
    for i in range(5):
        await asyncio.sleep(1.0)
        info = await dlna_controller.get_transport_info(av_url)
        pos = await dlna_controller.get_position_info(av_url)
        print(f"  T+{i+1}s: state={info.get('state')} uri={pos.get('uri')[-45:]}")

if __name__ == "__main__":
    asyncio.run(run_switch_test())
