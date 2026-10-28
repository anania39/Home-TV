import asyncio
import httpx
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_channel_switching():
    base = 'http://127.0.0.1:8000'
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Fetch channel list
        r = await client.get(f'{base}/api/iptv/channels')
        assert r.status_code == 200
        channels = r.json()['channels']
        ch_a = channels[0] # Setanta 1
        ch_b = channels[1] # Setanta 2
        ch_c = channels[2] # Setanta 3

        print(f"Testing channel switch between:\n  1: {ch_a['name']}\n  2: {ch_b['name']}\n  3: {ch_c['name']}")

        # 2. Cast Channel A to web_receiver (fast & isolated)
        t0 = time.time()
        r_a = await client.post(f"{base}/api/iptv/cast/{ch_a['id']}?device_id=web_receiver", json={"device_id": "web_receiver"})
        elapsed_a = time.time() - t0
        assert r_a.status_code == 200, f"Cast A failed: {r_a.text}"
        data_a = r_a.json()
        print(f"  Cast A OK in {elapsed_a:.2f}s: version={data_a.get('version')}, url={data_a.get('url')[:60]}...")
        url_a = data_a.get('url')
        sid_a = url_a.split('sid=')[1].split('&')[0] if 'sid=' in url_a else None

        # Fetch manifest for Channel A
        r_man_a = await client.get(f"{base}{url_a}")
        print(f"  Manifest A HTTP {r_man_a.status_code}, len={len(r_man_a.content)}, cache-control={r_man_a.headers.get('cache-control')}")
        assert r_man_a.status_code == 200
        assert 'no-store' in r_man_a.headers.get('cache-control', '')

        # 3. Cast Channel B (Channel Switch!)
        t0 = time.time()
        r_b = await client.post(f"{base}/api/iptv/cast/{ch_b['id']}?device_id=web_receiver", json={"device_id": "web_receiver"})
        elapsed_b = time.time() - t0
        assert r_b.status_code == 200, f"Cast B failed: {r_b.text}"
        data_b = r_b.json()
        print(f"  Cast B OK in {elapsed_b:.2f}s: version={data_b.get('version')}, url={data_b.get('url')[:60]}...")
        url_b = data_b.get('url')
        sid_b = url_b.split('sid=')[1].split('&')[0] if 'sid=' in url_b else None

        assert sid_a != sid_b, f"SID must change on channel switch! ({sid_a} == {sid_b})"

        # 4. Request Channel A with old sid_a: MUST RETURN HTTP 410 GONE!
        r_stale = await client.get(f"{base}{url_a}")
        print(f"  Stale Channel A request with old SID {sid_a}: HTTP {r_stale.status_code}")
        assert r_stale.status_code == 410, f"Stale channel request must return 410 Gone, got {r_stale.status_code}"

        # Fetch manifest for Channel B: MUST RETURN HTTP 200
        r_man_b = await client.get(f"{base}{url_b}")
        print(f"  New Channel B manifest: HTTP {r_man_b.status_code}, len={len(r_man_b.content)}")
        assert r_man_b.status_code == 200

        # 5. Rapid switch to Channel C
        r_c = await client.post(f"{base}/api/iptv/cast/{ch_c['id']}")
        data_c = r_c.json()
        print(f"  Cast C OK: version={data_c.get('version')}, title={data_c.get('title')}")

        # Verify state endpoint
        r_state = await client.get(f"{base}/api/state/current")
        state_data = r_state.json()
        print(f"  State endpoint sync: title={state_data.get('title')}, version={state_data.get('version')}")
        assert state_data.get('channel_id') == ch_c['id']

        print("\n>>> ALL BACKEND SWITCHING & ISOLATION CHECKS PASSED SUCCESSFULLY! <<<")

if __name__ == '__main__':
    asyncio.run(test_channel_switching())
