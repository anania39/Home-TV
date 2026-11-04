import socket, ssl, json, time, requests, re

def encode_cast_msg(src, dst, ns, payload_str):
    def varint(n):
        res = bytearray()
        while n > 0x7f:
            res.append((n & 0x7f) | 0x80)
            n >>= 7
        res.append(n)
        return bytes(res)
    def str_field(field_num, s):
        raw = s.encode('utf-8')
        tag = (field_num << 3) | 2
        return bytes([tag]) + varint(len(raw)) + raw
    body = (
        b'\x08\x00' +
        str_field(2, src) +
        str_field(3, dst) +
        str_field(4, ns) +
        b'\x28\x00' +
        str_field(6, payload_str)
    )
    return len(body).to_bytes(4, byteorder='big') + body

def recv_msg(s):
    hdr = s.recv(4)
    if len(hdr) < 4: return None
    l = int.from_bytes(hdr, 'big')
    raw = b''
    while len(raw) < l:
        chunk = s.recv(l - len(raw))
        if not chunk: break
        raw += chunk
    return raw

def extract_transport_id_for_app(text, target_app_id):
    try:
        idx = text.find('{')
        if idx == -1: return None
        data = json.loads(text[idx:])
        if data.get('type') == 'RECEIVER_STATUS':
            apps = data.get('status', {}).get('applications', [])
            for app in apps:
                if app.get('appId') == target_app_id:
                    return app.get('transportId')
    except Exception:
        pass
    return None

def cast_channel(ip, stream_url, title):
    print(f"\n[CAST CHANNEL] Casting '{title}' to {ip}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    s = socket.socket()
    s.settimeout(2.5)
    tls = ctx.wrap_socket(s)
    tls.connect((ip, 8009))

    tls.sendall(encode_cast_msg('sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.tp.connection', json.dumps({'type': 'CONNECT'})))
    tls.sendall(encode_cast_msg('sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.receiver', json.dumps({'type': 'LAUNCH', 'appId': 'CC1AD845', 'requestId': 1})))

    transport_id = None
    start = time.time()
    while time.time() - start < 8:
        try:
            raw = recv_msg(tls)
            if raw:
                text = raw.decode('utf-8', errors='ignore')
                tid = extract_transport_id_for_app(text, 'CC1AD845')
                if tid:
                    transport_id = tid
                    print(f"CC1AD845 ready! transportId: {tid}")
                    break
        except socket.timeout:
            pass

    if not transport_id:
        print("Failed to get CC1AD845 transportId")
        tls.close()
        return False

    tls.sendall(encode_cast_msg('sender-0', transport_id, 'urn:x-cast:com.google.cast.tp.connection', json.dumps({'type': 'CONNECT'})))
    load_msg = {
        'type': 'LOAD',
        'requestId': 2,
        'autoplay': True,
        'media': {
            'contentId': stream_url,
            'streamType': 'LIVE',
            'contentType': 'application/x-mpegurl',
            'metadata': {'metadataType': 0, 'title': title}
        }
    }
    tls.sendall(encode_cast_msg('sender-0', transport_id, 'urn:x-cast:com.google.cast.media', json.dumps(load_msg)))
    print(f"LOAD sent for channel {title}!")
    tls.close()
    return True

def cast_youtube(ip, video_id):
    print(f"\n[CAST YOUTUBE] Casting video {video_id} to {ip}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    s = socket.socket()
    s.settimeout(2.5)
    tls = ctx.wrap_socket(s)
    tls.connect((ip, 8009))

    tls.sendall(encode_cast_msg('sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.tp.connection', json.dumps({'type': 'CONNECT'})))
    tls.sendall(encode_cast_msg('sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.receiver', json.dumps({'type': 'LAUNCH', 'appId': '233637DE', 'requestId': 1})))

    transport_id = None
    start = time.time()
    while time.time() - start < 8:
        try:
            raw = recv_msg(tls)
            if raw:
                text = raw.decode('utf-8', errors='ignore')
                tid = extract_transport_id_for_app(text, '233637DE')
                if tid:
                    transport_id = tid
                    print(f"233637DE ready! transportId: {tid}")
                    break
        except socket.timeout:
            pass

    if not transport_id:
        print("Failed to get 233637DE transportId")
        tls.close()
        return False

    tls.sendall(encode_cast_msg('sender-0', transport_id, 'urn:x-cast:com.google.cast.tp.connection', json.dumps({'type': 'CONNECT'})))
    tls.sendall(encode_cast_msg('sender-0', transport_id, 'urn:x-cast:com.google.youtube.mdx', json.dumps({'type': 'getMdxSessionStatus'})))

    screen_id = None
    start = time.time()
    while time.time() - start < 6:
        try:
            raw = recv_msg(tls)
            if raw:
                text = raw.decode('utf-8', errors='ignore')
                m = re.search(r'"screenId":"([^"]+)"', text)
                if m:
                    screen_id = m.group(1)
                    print(f"Screen ID obtained: {screen_id[:15]}...")
                    break
        except socket.timeout:
            pass

    tls.close()

    if not screen_id:
        print("Failed to get screenId")
        return False

    headers = {'Origin': 'https://www.youtube.com', 'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch', data={'screen_ids': screen_id}, headers=headers, timeout=5)
    lounge_token = r.json()['screens'][0]['loungeToken']

    bind_headers = dict(headers)
    bind_headers['X-YouTube-LoungeId-Token'] = lounge_token
    bind_data = {
        'device': 'REMOTE_CONTROL',
        'id': 'tvhubandroid123456789',
        'name': 'Android',
        'mdx-version': 3,
        'pairing_type': 'cast',
        'app': 'android-phone-13.14.55'
    }
    r2 = requests.post('https://www.youtube.com/api/lounge/bc/bind', params={'RID': 0, 'VER': 8, 'CVER': 1}, data=bind_data, headers=bind_headers, timeout=5)
    raw_bind = r2.text
    sid = re.search(r'"c","(.*?)",\"', raw_bind).group(1)
    gsessionid = re.search(r'"S","(.*?)"\]', raw_bind).group(1)

    play_data = {
        'req0_videoId': video_id,
        'req0_currentTime': '0',
        'req0_currentIndex': '-1',
        'req0_audioOnly': 'false',
        'req0_listId': '',
        'count': 1,
        'req0__sc': 'setPlaylist'
    }
    r3 = requests.post('https://www.youtube.com/api/lounge/bc/bind', params={'SID': sid, 'gsessionid': gsessionid, 'RID': 1, 'VER': 8, 'CVER': 1}, data=play_data, headers=bind_headers, timeout=5)
    print(f"Play response: {r3.status_code}")
    return r3.status_code == 200

if __name__ == '__main__':
    ip = '192.168.50.205'
    # 1. Cast YouTube (hC1MeW-IMdw)
    r1 = cast_youtube(ip, 'hC1MeW-IMdw')
    assert r1, "Step 1 failed"
    time.sleep(3)

    # 2. Cast Channel (Setanta 1)
    ch_url = 'https://tvhub.92.5.71.162.sslip.io/proxy?url=http%3A%2F%2Fstream.mcquack.net%2F170%2Findex.m3u8'
    r2 = cast_channel(ip, ch_url, 'Setanta Sports 1 HD')
    assert r2, "Step 2 failed"
    time.sleep(3)

    # 3. Cast YouTube Again (Rick Astley)
    r3 = cast_youtube(ip, 'dQw4w9WgXcQ')
    assert r3, "Step 3 failed"
    time.sleep(3)

    # 4. Cast Channel Again (Setanta 2)
    ch2_url = 'https://tvhub.92.5.71.162.sslip.io/proxy?url=http%3A%2F%2Fstream.mcquack.net%2F151%2Findex.m3u8'
    r4 = cast_channel(ip, ch2_url, 'Setanta Sports 2 HD')
    assert r4, "Step 4 failed"

    print("\n🎉 ALL 4 TRANSITIONS WORKED 100% FLAWLESSLY!")
