"""
Automated test script for cast serialization and versioning.
Tests rapid concurrent casts against a test instance (e.g. port 8000).
Verifies that:
1. Version numbers increment monotonically.
2. The final cast wins (last click wins).
3. Superseded casts do not overwrite current state or play on receivers.
4. /api/state/current reflects the latest channel and max version.
"""

import sys
import asyncio
import httpx


async def run_tests(base_url: str):
    print(f"[*] Running versioning and cast serialization tests against: {base_url}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Health check
        try:
            res = await client.get(f"{base_url}/api/state/current")
            assert res.status_code == 200, f"Expected 200, got {res.status_code}"
            initial_state = res.json()
            initial_version = initial_state.get("version", 0)
            print(f"[-] Initial server state: version={initial_version}, channel={initial_state.get('channel_id')}")
        except Exception as e:
            print(f"[!] Server not reachable at {base_url}: {e}")
            sys.exit(1)

        # 2. Fire 6 rapid cast commands in staggered order (simulate user tapping different channels quickly)
        test_channels = [
            "ge-formula",
            "ge-imedi",
            "ge-1tv",
            "ge-2tv",
            "ge-ertsulovneba",
            "ge-palitra"
        ]

        expected_winner = test_channels[-1]

        async def send_cast(idx: int, ch_id: str):
            await asyncio.sleep(idx * 0.02)  # 20ms stagger
            resp = await client.post(f"{base_url}/api/iptv/cast/{ch_id}")
            return idx, ch_id, resp.status_code, resp.json()

        print(f"[*] Firing {len(test_channels)} rapid casts...")
        tasks = [send_cast(i, ch) for i, ch in enumerate(test_channels)]
        results = await asyncio.gather(*tasks)

        for idx, ch_id, status_code, data in results:
            print(f"    Cast #{idx+1} ({ch_id}): HTTP {status_code} -> status={data.get('status')} version={data.get('version')}")

        # 3. Small pause to allow server task loops to settle
        await asyncio.sleep(0.5)

        # 4. Check final server state
        res = await client.get(f"{base_url}/api/state/current")
        assert res.status_code == 200
        final_state = res.json()
        final_version = final_state.get("version", 0)
        final_channel = final_state.get("channel_id")

        print(f"[*] Final server state: version={final_version}, channel={final_channel}")

        # Assertions
        assert final_version >= initial_version + len(test_channels), (
            f"Version did not monotonically increase: initial={initial_version}, final={final_version}"
        )
        assert final_channel == expected_winner, (
            f"Expected winning channel '{expected_winner}', but got '{final_channel}'"
        )

        # 5. Check debug receivers endpoint
        res = await client.get(f"{base_url}/api/debug/receivers")
        assert res.status_code == 200, f"Debug receivers returned {res.status_code}"
        debug_data = res.json()
        print(f"[*] Receiver count: {debug_data.get('count')}, cast_version: {debug_data.get('cast_version')}")
        assert debug_data.get("cast_version") == final_version

        print("\n[SUCCESS] All cast serialization and versioning checks passed!")


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    asyncio.run(run_tests(target_url))
