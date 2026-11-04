with open('scripts/build_android_apk.sh', 'r', encoding='utf-8') as f:
    sh = f.read()

# 1. Bump version to 7.4.0
sh = sh.replace('v7.3.0', 'v7.4.0')
sh = sh.replace('android:versionCode="730"', 'android:versionCode="740"')
sh = sh.replace('android:versionName="7.3.0"', 'android:versionName="7.4.0"')
sh = sh.replace('TVHubHostApp/7.3', 'TVHubHostApp/7.4')
sh = sh.replace('?v=7.3.0', '?v=7.4.0')
sh = sh.replace('(v7.3.0)', '(v7.4.0)')

# 2. Replace castToGoogleTv with the complete bi-directional lifecycle engine
old_cast_start = "    // --- Google Cast V2 TLS Engine (Port 8009) with Persistent Heartbeat ---"
old_cast_end = "    private static void sendCastMsg(OutputStream out, String src, String dst, String ns, String payload) throws Exception {"

idx1 = sh.find(old_cast_start)
idx2 = sh.find(old_cast_end)
assert idx1 != -1 and idx2 != -1, "Cast engine boundaries not found"

new_cast_impl = """    // --- Google Cast V2 TLS Engine (Port 8009) with Bi-directional Heartbeat ---
    private synchronized boolean castToGoogleTv(String ip, String streamUrl, String title) {
        try {
            closeActiveCast();

            TrustManager[] trustAll = new TrustManager[]{
                new X509TrustManager() {
                    public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
                    public void checkClientTrusted(X509Certificate[] c, String a) {}
                    public void checkServerTrusted(X509Certificate[] c, String a) {}
                }
            };
            SSLContext sc = SSLContext.getInstance("TLS");
            sc.init(null, trustAll, new SecureRandom());
            SSLSocket socket = (SSLSocket) sc.getSocketFactory().createSocket(ip, 8009);
            socket.setSoTimeout(1500);
            socket.setKeepAlive(true);
            socket.setTcpNoDelay(true);
            socket.startHandshake();

            final OutputStream out = socket.getOutputStream();
            final InputStream in = socket.getInputStream();

            // 1. Send CONNECT to receiver-0
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\\"type\\":\\"CONNECT\\"}");

            // 2. Query status FIRST to check if Default Media Receiver (CC1AD845) is already running
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\\"type\\":\\"GET_STATUS\\",\\"requestId\\":1}");

            String transportId = null;
            long startWait = System.currentTimeMillis();
            boolean launchSent = false;

            while (System.currentTimeMillis() - startWait < 8500) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    int idx = text.indexOf("\\"transportId\\":\\"");
                    if (idx != -1) {
                        int endIdx = text.indexOf("\\"", idx + 15);
                        if (endIdx != -1) {
                            transportId = text.substring(idx + 15, endIdx);
                            break;
                        }
                    }
                    if (!launchSent && text.contains("RECEIVER_STATUS") && !text.contains("CC1AD845")) {
                        // CC1AD845 not running on TV -> Launch it now
                        sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\\"type\\":\\"LAUNCH\\",\\"appId\\":\\"CC1AD845\\",\\"requestId\\":2}");
                        launchSent = true;
                    }
                } catch (java.net.SocketTimeoutException ste) {
                    if (!launchSent) {
                        sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\\"type\\":\\"LAUNCH\\",\\"appId\\":\\"CC1AD845\\",\\"requestId\\":2}");
                        launchSent = true;
                    } else {
                        try {
                            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\\"type\\":\\"GET_STATUS\\",\\"requestId\\":3}");
                        } catch (Exception ignored) {}
                    }
                } catch (Exception ignored) {
                    break;
                }
            }

            if (transportId == null || transportId.isEmpty()) {
                notifyUser("⚠️ Smart TV Cast receiver not ready. Retrying...");
                closeActiveCast();
                return false;
            }

            // 3. Connect to media transport endpoint
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.tp.connection", "{\\"type\\":\\"CONNECT\\"}");

            // 4. Send LOAD command with stream URL
            boolean isHls = streamUrl.contains(".m3u8") || streamUrl.contains("/proxy?url=");
            String mime = isHls ? "application/x-mpegurl" : "video/mp4";
            String loadJson = "{\\"type\\":\\"LOAD\\",\\"requestId\\":3,\\"autoplay\\":true,\\"media\\":{\\"contentId\\":\\"" + escapeJson(streamUrl) + "\\",\\"streamType\\":\\"LIVE\\",\\"contentType\\":\\"" + mime + "\\",\\"metadata\\":{\\"metadataType\\":0,\\"title\\":\\"" + escapeJson(title) + "\\"} } }";
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.media", loadJson);

            // 5. Keep connection alive with FULL BI-DIRECTIONAL PING/PONG READER THREAD
            activeCastSocket = socket;
            activeCastOut = out;
            activeCastIp = ip;
            currentTransportId = transportId;

            final SSLSocket liveSocket = socket;
            final String activeTid = transportId;
            final InputStream activeIn = in;
            final OutputStream activeOut = out;

            activeCastHeartbeat = new Thread(new Runnable() {
                @Override
                public void run() {
                    long lastPingSent = System.currentTimeMillis();
                    try {
                        while (!Thread.currentThread().isInterrupted() && liveSocket != null && !liveSocket.isClosed()) {
                            long now = System.currentTimeMillis();
                            if (now - lastPingSent >= 4000) {
                                synchronized (MainActivity.this) {
                                    if (liveSocket.isClosed()) break;
                                    sendCastMsg(activeOut, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\\"type\\":\\"PING\\"}");
                                    sendCastMsg(activeOut, "sender-0", activeTid, "urn:x-cast:com.google.cast.tp.heartbeat", "{\\"type\\":\\"PING\\"}");
                                }
                                lastPingSent = now;
                            }
                            try {
                                byte[] raw = readCastMsg(activeIn);
                                if (raw != null) {
                                    String text = new String(raw, "UTF-8");
                                    if (text.contains("\\"PING\\"")) {
                                        synchronized (MainActivity.this) {
                                            if (liveSocket.isClosed()) break;
                                            sendCastMsg(activeOut, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\\"type\\":\\"PONG\\"}");
                                            sendCastMsg(activeOut, "sender-0", activeTid, "urn:x-cast:com.google.cast.tp.heartbeat", "{\\"type\\":\\"PONG\\"}");
                                        }
                                    }
                                }
                            } catch (java.net.SocketTimeoutException ste) {
                                // Normal read timeout, continue loop to keep sending heartbeats
                            }
                        }
                    } catch (Exception ignored) {}
                }
            });
            activeCastHeartbeat.start();

            return true;
        } catch (Exception e) {
            e.printStackTrace();
            closeActiveCast();
            return false;
        }
    }

"""

sh = sh[:idx1] + new_cast_impl + sh[idx2:]

with open('scripts/build_android_apk.sh', 'w', encoding='utf-8') as f:
    f.write(sh)

print("scripts/build_android_apk.sh successfully patched for v7.4.0!")
