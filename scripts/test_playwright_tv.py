import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def test_tv_receiver():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # Open TV Web Receiver
        await page.goto('http://127.0.0.1:8000/tv', wait_until='networkidle')
        title = await page.title()
        print('Page title:', title)
        assert 'TV Hub' in title

        # Check Hls is loaded
        hls_supported = await page.evaluate("() => typeof window.Hls !== 'undefined' && window.Hls.isSupported()")
        print('Hls.js supported:', hls_supported)
        assert hls_supported

        # Simulate playStream for Channel 1
        await page.evaluate("""() => {
            playStream('/api/stream/proxy?url=http%3A%2F%2Fstream.mcquack.net%2F234%2Findex.m3u8&sid=s_test_1', 'Setanta Sports 1 HD', './static/logos/setanta-1.png', {
                sources: [{ url: '/api/stream/proxy?url=http%3A%2F%2Fstream.mcquack.net%2F234%2Findex.m3u8&sid=s_test_1', type: 'hls' }],
                sourceIndex: 0,
                channelId: 'setanta-1'
            });
        }""")
        await asyncio.sleep(2)

        # Verify OSD shows Setanta Sports 1
        osd_text = await page.locator('#osd-title').text_content()
        print('OSD Title after Play 1:', osd_text)
        assert osd_text == 'Setanta Sports 1 HD'

        # Now simulate switching to Channel 2 (Silk Universal)
        await page.evaluate("""() => {
            playStream('/api/stream/proxy?url=https%3A%2F%2Fstreaming-hls2.televiziebi.org%2Fhls%2Fsilk.m3u8&sid=s_test_2', 'Silk Universal', './static/logos/silk-universal.png', {
                sources: [{ url: '/api/stream/proxy?url=https%3A%2F%2Fstreaming-hls2.televiziebi.org%2Fhls%2Fsilk.m3u8&sid=s_test_2', type: 'hls' }],
                sourceIndex: 0,
                channelId: 'silk-universal'
            });
        }""")
        await asyncio.sleep(2)

        osd_text_2 = await page.locator('#osd-title').text_content()
        print('OSD Title after Play 2:', osd_text_2)
        assert osd_text_2 == 'Silk Universal'

        # Check that no unexpected failovers were logged
        failovers = [l for l in console_logs if 'failover' in l.lower()]
        print('Failover logs:', failovers)
        assert len(failovers) == 0, 'No unexpected failovers occurred'

        await browser.close()
        print('\n>>> ALL PLAYWRIGHT RECEIVER CHECKS PASSED! <<<')

if __name__ == '__main__':
    asyncio.run(test_tv_receiver())
