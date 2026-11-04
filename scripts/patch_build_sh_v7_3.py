with open('scripts/build_android_apk.sh', 'r', encoding='utf-8') as f:
    sh = f.read()

# 1. Bump version to 7.3.0
sh = sh.replace('android:versionCode="720"', 'android:versionCode="730"')
sh = sh.replace('android:versionName="7.2.0"', 'android:versionName="7.3.0"')
sh = sh.replace('TVHubHostApp/7.2', 'TVHubHostApp/7.3')
sh = sh.replace('?v=7.2.0', '?v=7.3.0')
sh = sh.replace('(v7.2.0)', '(v7.3.0)')

# 2. Add defensive streamUrl absolute check to performDirectCast
old_target_ip = '        String targetIp = (ip != null && !ip.isEmpty()) ? ip : "192.168.50.205";'
new_target_ip = """        String targetIp = (ip != null && !ip.isEmpty()) ? ip : "192.168.50.205";
        if (streamUrl != null && streamUrl.startsWith("/")) {
            streamUrl = "https://tvhub.92.5.71.162.sslip.io" + streamUrl;
        }"""
assert old_target_ip in sh, "old_target_ip not found"
sh = sh.replace(old_target_ip, new_target_ip, 1)

# 3. Update castToGoogleTv with robust 8-second transportId polling
old_read_loop = """            // 3. Read response for real transportId
            String transportId = null;
            for (int i = 0; i < 6; i++) {
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
                } catch (java.net.SocketTimeoutException ste) {
                    break;
                } catch (Exception ignored) {
                    break;
                }
            }

            if (transportId == null || transportId.isEmpty()) {
                transportId = "web-1";
            }"""

new_read_loop = """            // 3. Read responses until real transportId is found (up to 8 seconds)
            String transportId = null;
            long startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 8000) {
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
                } catch (java.net.SocketTimeoutException ste) {
                    try {
                        sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\\"type\\":\\"GET_STATUS\\",\\"requestId\\":3}");
                    } catch (Exception ignored) {}
                } catch (Exception ignored) {
                    break;
                }
            }

            if (transportId == null || transportId.isEmpty() || transportId.equals("web-1")) {
                sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\\"type\\":\\"GET_STATUS\\",\\"requestId\\":4}");
                for (int j = 0; j < 6; j++) {
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
                    } catch (Exception ignored) {}
                }
            }

            if (transportId == null || transportId.isEmpty()) {
                notifyUser("⚠️ Smart TV Cast receiver not ready. Retrying...");
                closeActiveCast();
                return false;
            }"""

assert old_read_loop in sh, "old_read_loop not found"
sh = sh.replace(old_read_loop, new_read_loop, 1)

with open('scripts/build_android_apk.sh', 'w', encoding='utf-8') as f:
    f.write(sh)

print("scripts/build_android_apk.sh patched for v7.3.0!")
