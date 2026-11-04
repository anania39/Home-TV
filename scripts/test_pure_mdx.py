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

def cast_youtube(ip, video_id):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    s = socket.socket()
    s.settimeout(2.5)
    tls = ctx.wrap_socket(s)
    tls.connect((ip, 8009))

    # 1. Connect and Launch 233637DE
    tls.sendall(encode_cast_msg('sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.tp.connection', json.dumps({'type': 'CONNECT'})))
    tls.sendall(encode_cast_msg('sender-0', 'receiver-0', 'urn:x-cast:com.google.cast.receiver', json.dumps({'type': 'LAUNCH', 'appId': '233637DE', 'requestId': 1})))

    transport_id = None
    start = time.time()
    while time.time() - start < 8:
        try:
            raw = recv_msg(tls)
            if raw:
                text = raw.decode('utf-8', errors='ignore')
                idx = text.find('"transportId":"')
                if idx != -1:
                    end = text.find('"', idx + 15)
                    transport_id = text[idx + 15:end]
                    print('Found transport ID:', transport_id)
                    break
        except socket.timeout:
            pass

    if not transport_id:
        print('Failed to get transport ID')
        return False

    # 2. Connect to transport and request screenId
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
                    print('Found screen ID:', screen_id)
                    break
        except socket.timeout:
            pass

    if not screen_id:
        print('Failed to get screen ID')
        return False

    # 3. Lounge Token
    headers = {'Origin': 'https://www.youtube.com', 'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch', data={'screen_ids': screen_id}, headers=headers, timeout=5)
    lounge_token = r.json()['screens'][0]['loungeToken']
    print('Got lounge token:', lounge_token[:15] + '...')

    # 4. Bind
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
    print('Bound session! SID:', sid, 'GSESSIONID:', gsessionid)

    # 5. Play Video
    play_data = {
        'req0__videoId': video_id,
        'req0__currentTime': '0',
        'req0__currentIndex': '-1',
        'req0__audioOnly': 'false',
        'req0__listId': '',
        'count': 1,
        'req0___sc': 'setPlaylist'
    }
    # Wait, let's check exact keys from casttube:
    # LIST_ID = "_listId" -> req0_listId
    # ACTION = "__sc" -> req0__sc
    # CURRENT_TIME = "_currentTime" -> req0_currentTime
    # CURRENT_INDEX = "_currentIndex" -> req0_currentIndex
    # AUDIO_ONLY = "_audioOnly" -> req0_audioOnly
    # VIDEO_ID = "_videoId" -> req0_videoId
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
    print('Play command response:', r3.status_code, r3.text)

    tls.close()
    return r3.status_code == 200

if __name__ == '__main__':
    ok = cast_youtube('192.168.50.205', 'hC1MeW-IMdw')
    print('CAST RESULT:', ok)
