with open('backend/stream_proxy.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''                    "Cache-Control": f"public, max-age={max_age_val}, stale-while-revalidate=2",
                    "Pragma": "no-cache",
                    "X-Cache": "MISS"'''

replacement = '''                    "Cache-Control": f"public, max-age={max_age_val}, stale-while-revalidate=2",
                    "Accept-Ranges": "bytes",
                    "Connection": "keep-alive",
                    "X-Cache": "MISS"'''

if target in text:
    text = text.replace(target, replacement)
    with open('backend/stream_proxy.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated MISS headers successfully!')
else:
    print('Target not found in stream_proxy.py')
