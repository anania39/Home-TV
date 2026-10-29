import asyncio
import time
import httpx
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.dlna_controller import dlna_controller
from backend.discovery import device_manager

async def run_clean_switch_test():
    av_url = "http://192.168.50.249:38400/upnp/control/mingusavtr"
    base = "http://127.0.0.1:8000"
    
    print("--- [TEST 1] Ensure TV is stopped and clean ---")
    await dlna_controller.stop(av_url)
    for _ in range(10):
        await asyncio.sleep(0.2)
        info = await dlna_controller.get_transport_info(av_url)
        if info.get("state") in ["STOPPED", "NO_MEDIA_PRESENT"]:
            print(f"  TV successfully reached clean STOPPED state: {info}")
            break
            
    print("\n--- [TEST 2] Cast Channel A (Silk Universal) ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r1 = await client.post(f"{base}/api/iptv/cast/ge-silkuniversal?device_id=tv_192_168_50_249")
        print(f"  Cast Silk response: {r1.status_code} {r1.json()}")
        
    # Wait and check playback
    for i in range(4):
        await asyncio.sleep(1.0)
        info = await dlna_controller.get_transport_info(av_url)
        print(f"  Playback Silk T+{i+1}s: {info}")
        
    print("\n--- [TEST 3] Switch to Channel B (Imedi) using CLEAN STOP & FLUSH ---")
    t0 = time.time()
    
    # Clean STOP
    stop_ok = await dlna_controller.stop(av_url)
    print(f"  Stop command sent: {stop_ok}")
    for attempt in range(12):
        await asyncio.sleep(0.15)
        info = await dlna_controller.get_transport_info(av_url)
        if info.get("state") in ["STOPPED", "NO_MEDIA_PRESENT"]:
            print(f"  TV stopped and flushed after {(attempt + 1) * 0.15:.2f}s (state={info.get('state')})")
            break
            
    # Now cast Imedi
    async with httpx.AsyncClient(timeout=10.0) as client:
        r2 = await client.post(f"{base}/api/iptv/cast/ge-imedi?device_id=tv_192_168_50_249")
        print(f"  Cast Imedi response: {r2.status_code} {r2.json()} in {time.time() - t0:.2f}s")
        
    # Monitor Imedi playback for 6 seconds
    for i in range(6):
        await asyncio.sleep(1.0)
        info = await dlna_controller.get_transport_info(av_url)
        pos = await dlna_controller.get_position_info(av_url)
        print(f"  Imedi playback T+{i+1}s: state={info.get('state')} uri={pos.get('uri')[-50:]}")

if __name__ == "__main__":
    asyncio.run(run_clean_switch_test())
