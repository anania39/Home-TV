def format_quality_display(q):
    if not q or q == 'Auto': return {'value': 'Auto', 'tier': 'Auto', 'label': 'Auto (Smooth Playback)'}
    clean = str(q).strip()
    num = int(''.join(c for c in clean if c.isdigit()) or 0)
    if clean == '4K' or num >= 2000: return {'value': q, 'tier': '4K', 'label': '4K (Ultra HD)'}
    if clean == '1440p' or (num >= 1400 and num < 2000): return {'value': q, 'tier': '1440p', 'label': '1440p (2K Quad HD)'}
    if clean == '1080p' or (num >= 750 and num < 1400): return {'value': q, 'tier': '1080p', 'label': '1080p (Full HD)'}
    if clean == '720p' or (num >= 500 and num < 750): return {'value': q, 'tier': '720p', 'label': '720p (HD)'}
    if clean == '480p' or (num >= 340 and num < 500): return {'value': q, 'tier': '480p', 'label': '480p (SD)'}
    if clean == '360p' or (num >= 240 and num < 340): return {'value': q, 'tier': '360p', 'label': '360p (Data Saver)'}
    if clean == '240p' or (num >= 160 and num < 240): return {'value': q, 'tier': '240p', 'label': '240p (Low)'}
    return {'value': q, 'tier': 'SD', 'label': clean}

incoming = ['Auto', '804p', '536p', '358p', '268p', '178p']
for q in incoming:
    res = format_quality_display(q)
    print(f"{q:10} -> {res['label']}")
