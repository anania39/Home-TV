#!/bin/bash
set -e
echo '=== Building Fully Autonomous TV Hub Android Host App (v7.2.0) ==='

BUILD_DIR=/home/ubuntu/tvhub_apk_build
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR/src/com/tvhub/app
mkdir -p $BUILD_DIR/res/values
mkdir -p $BUILD_DIR/res/mipmap-hdpi
mkdir -p $BUILD_DIR/res/mipmap-xhdpi
mkdir -p $BUILD_DIR/res/mipmap-xxhdpi
mkdir -p $BUILD_DIR/res/mipmap-xxxhdpi
mkdir -p $BUILD_DIR/assets
mkdir -p $BUILD_DIR/bin

# 1. Bundle Complete Offline Assets & Channel Logos into APK
echo '=== Bundling Web Assets, Playlists and Channel Logos into APK ==='
cp -r /home/ubuntu/Home-TV/static/* $BUILD_DIR/assets/ || true
mkdir -p $BUILD_DIR/assets/playlists
cp -r /home/ubuntu/Home-TV/playlists/* $BUILD_DIR/assets/playlists/ || true

# 2. Generate App Icons (Vibrant Cyan TV Hub Icon)
python3 - << 'PYEOF'
import struct, zlib

def make_png(w, h, r, g, b):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = b''
    for y in range(h):
        raw += b'\x00'
        for x in range(w):
            dx = min(x, w - 1 - x)
            dy = min(y, h - 1 - y)
            # Rounded corners
            if dx * dx + dy * dy < (w // 6) * (w // 6) and (x < w // 6 or x > w - w // 6) and (y < h // 6 or y > h - h // 6):
                raw += bytes([11, 15, 25])
            # Center screen (white screen preview)
            elif x > w // 5 and x < w - w // 5 and y > h // 5 and y < h - h // 3:
                raw += bytes([255, 255, 255])
            # TV stand
            elif x > w // 3 and x < w - w // 3 and y > h - h // 4 and y < h - h // 6:
                raw += bytes([56, 189, 248])
            else:
                raw += bytes([r, g, b])
    idat = zlib.compress(raw)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')

with open('/home/ubuntu/tvhub_apk_build/res/mipmap-hdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(72, 72, 14, 165, 233))
with open('/home/ubuntu/tvhub_apk_build/res/mipmap-xhdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(96, 96, 14, 165, 233))
with open('/home/ubuntu/tvhub_apk_build/res/mipmap-xxhdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(144, 144, 14, 165, 233))
with open('/home/ubuntu/tvhub_apk_build/res/mipmap-xxxhdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(192, 192, 14, 165, 233))
PYEOF

# 3. Strings
cat << 'STRINGS' > $BUILD_DIR/res/values/strings.xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TV Hub</string>
</resources>
STRINGS

# 4. AndroidManifest.xml (Target SDK 34, Min SDK 26 for Android 14 compatibility)
cat << 'MANIFEST' > $BUILD_DIR/AndroidManifest.xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.tvhub.app"
    android:versionCode="720"
    android:versionName="7.2.0">

    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />

    <application
        android:label="@string/app_name"
        android:icon="@mipmap/ic_launcher"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="true"
        android:allowBackup="true"
        android:supportsRtl="true">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
MANIFEST

# 5. MainActivity.java with High-Speed Google Cast V2 + DLNA + DIAL Controller
cat << 'JAVA' > $BUILD_DIR/src/com/tvhub/app/MainActivity.java
package com.tvhub.app;

import android.app.Activity;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.security.SecureRandom;
import java.security.cert.X509Certificate;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

public class MainActivity extends Activity {
    private WebView webView;
    private FrameLayout rootLayout;
    private View customView;
    private WebChromeClient.CustomViewCallback customViewCallback;
    private FrameLayout customViewContainer;
    private WifiManager.MulticastLock multicastLock;
    private Handler mainHandler;
    private SSLSocket activeCastSocket = null;
    private OutputStream activeCastOut = null;
    private Thread activeCastHeartbeat = null;
    private String activeCastIp = null;
    private String currentTransportId = null;

    private synchronized void closeActiveCast() {
        if (activeCastHeartbeat != null) {
            try { activeCastHeartbeat.interrupt(); } catch (Exception ignored) {}
            activeCastHeartbeat = null;
        }
        if (activeCastSocket != null) {
            try { activeCastSocket.close(); } catch (Exception ignored) {}
            activeCastSocket = null;
            activeCastOut = null;
            activeCastIp = null;
            currentTransportId = null;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mainHandler = new Handler(Looper.getMainLooper());

        // Keep screen awake while streaming TV
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // Unlock Wi-Fi multicast so phone talks directly to local Smart TVs
        try {
            WifiManager wm = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            if (wm != null) {
                multicastLock = wm.createMulticastLock("TVHubMulticastLock");
                multicastLock.setReferenceCounted(true);
                multicastLock.acquire();
            }
        } catch (Exception ignored) {}

        rootLayout = new FrameLayout(this);
        rootLayout.setBackgroundColor(0xFF0B0F19);

        webView = new WebView(this);
        webView.setLayoutParams(new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        rootLayout.addView(webView);

        customViewContainer = new FrameLayout(this);
        customViewContainer.setBackgroundColor(0xFF000000);
        customViewContainer.setVisibility(View.GONE);
        rootLayout.addView(customViewContainer, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        setContentView(rootLayout);

        // Clear stale WebView cache so latest features take effect immediately
        try {
            webView.clearCache(true);
        } catch (Exception ignored) {}

        // Maximum Performance WebSettings
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setUserAgentString("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 TVHubHostApp/7.2");

        // Expose Native TV Hub Android Host Bridge
        webView.addJavascriptInterface(new TVHubBridge(), "TVHubAndroid");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                view.loadUrl(url);
                return true;
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                view.postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        view.loadUrl("https://tvhub.92.5.71.162.sslip.io?v=7.2.0");
                    }
                }, 2000);
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onShowCustomView(View view, CustomViewCallback callback) {
                if (customView != null) {
                    onHideCustomView();
                    return;
                }
                customView = view;
                customViewCallback = callback;
                customViewContainer.addView(view);
                customViewContainer.setVisibility(View.VISIBLE);
                webView.setVisibility(View.GONE);
                setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);
            }

            @Override
            public void onHideCustomView() {
                if (customView == null) return;
                customViewContainer.removeView(customView);
                customViewContainer.setVisibility(View.GONE);
                customView = null;
                webView.setVisibility(View.VISIBLE);
                if (customViewCallback != null) {
                    customViewCallback.onCustomViewHidden();
                }
                setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
            }

            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                request.grant(request.getResources());
            }
        });

        webView.loadUrl("https://tvhub.92.5.71.162.sslip.io?v=7.2.0");
    }

    // --- Native Android Host Bridge Exposed to JavaScript ---
    public class TVHubBridge {
        @JavascriptInterface
        public boolean isNativeApp() {
            return true;
        }

        @JavascriptInterface
        public void toast(final String msg) {
            mainHandler.post(new Runnable() {
                @Override
                public void run() {
                    Toast.makeText(MainActivity.this, msg, Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public void sendWakeOnLan() {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    sendWakeOnLanPacket();
                }
            }).start();
        }

        @JavascriptInterface
        public void castToTv(final String ip, final String devType, final String streamUrl, final String title, final String mimeType, final String youtubeId) {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    performDirectCast(ip, devType, streamUrl, title, mimeType, youtubeId);
                }
            }).start();
        }
    }

    private void performDirectCast(String ip, String devType, String streamUrl, String title, String mimeType, String youtubeId) {
        String targetIp = (ip != null && !ip.isEmpty()) ? ip : "192.168.50.205";
        String type = (devType != null) ? devType.toLowerCase() : "";

        // 1. Wake TV from standby via direct local UDP magic packet
        sendWakeOnLanPacket();

        // 2. Google Cast V2 Protocol for TCL Smart TV Pro (192.168.50.205:8009) & Google TVs
        if (type.contains("google_tv") || targetIp.endsWith(".205") || targetIp.endsWith(".3")) {
            notifyUser("Connecting to TCL Smart TV Pro via Cast V2...");
            boolean castOk = castToGoogleTv(targetIp, streamUrl, title);
            if (castOk) {
                notifyUser("🎉 Now Playing " + title + " on TCL Smart TV Pro!");
                return;
            }
        }

        // 3. DIAL for Hisense VIDAA TV (192.168.50.249) if YouTube ID present
        if (youtubeId != null && !youtubeId.isEmpty() && (type.contains("hisense") || targetIp.endsWith(".249"))) {
            boolean dialOk = launchDialYouTube(targetIp, youtubeId);
            if (dialOk) {
                notifyUser("Playing YouTube on Hisense VIDAA TV!");
                return;
            }
        }

        // 4. DLNA AVTransport for Hisense VIDAA TV (192.168.50.249:38400)
        if (type.contains("hisense") || targetIp.endsWith(".249")) {
            notifyUser("Connecting to Hisense VIDAA TV via DLNA...");
            String controlUrl = "http://" + targetIp + ":38400/upnp/control/mingusavtr";
            boolean dlnaOk = sendDlnaCast(controlUrl, streamUrl, title);
            if (dlnaOk) {
                notifyUser("🎉 Now Playing " + title + " on Hisense TV!");
                return;
            }
        }

        // 5. Universal Fallback: Try Cast V2 on 8009 then DLNA on 38400
        boolean castFallback = castToGoogleTv(targetIp, streamUrl, title);
        if (castFallback) {
            notifyUser("🎉 Playing " + title + " on Smart TV!");
            return;
        }

        boolean dlnaFallback = sendDlnaCast("http://" + targetIp + ":38400/upnp/control/mingusavtr", streamUrl, title);
        if (dlnaFallback) {
            notifyUser("🎉 Playing " + title + " on TV!");
            return;
        }

        notifyUser("⚡ Power signal sent to TV. If TV is off, please turn it on.");
    }

    private void notifyUser(final String msg) {
        mainHandler.post(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(MainActivity.this, msg, Toast.LENGTH_SHORT).show();
            }
        });
    }

    // --- Google Cast V2 TLS Engine (Port 8009) with Persistent Heartbeat ---
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
            socket.setSoTimeout(3500);
            socket.setKeepAlive(true);
            socket.setTcpNoDelay(true);
            socket.startHandshake();

            final OutputStream out = socket.getOutputStream();
            final InputStream in = socket.getInputStream();

            // 1. Send CONNECT to receiver-0
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");

            // 2. Launch Default Media Receiver (CC1AD845)
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"LAUNCH\",\"appId\":\"CC1AD845\",\"requestId\":1}");

            // 3. Read response for real transportId
            String transportId = null;
            for (int i = 0; i < 6; i++) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    int idx = text.indexOf("\"transportId\":\"");
                    if (idx != -1) {
                        int endIdx = text.indexOf("\"", idx + 15);
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
            }

            // 4. Connect to media transport
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");

            // 5. Send LOAD
            boolean isHls = streamUrl.contains(".m3u8") || streamUrl.contains("/proxy?url=");
            String mime = isHls ? "application/x-mpegurl" : "video/mp4";
            String loadJson = "{\"type\":\"LOAD\",\"requestId\":2,\"autoplay\":true,\"media\":{\"contentId\":\"" + escapeJson(streamUrl) + "\",\"streamType\":\"LIVE\",\"contentType\":\"" + mime + "\",\"metadata\":{\"metadataType\":0,\"title\":\"" + escapeJson(title) + "\"}}}";
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.media", loadJson);

            // Keep connection alive in background with Cast heartbeat PING every 4.5 seconds
            activeCastSocket = socket;
            activeCastOut = out;
            activeCastIp = ip;
            currentTransportId = transportId;

            final SSLSocket liveSocket = socket;
            activeCastHeartbeat = new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        while (!Thread.currentThread().isInterrupted() && liveSocket != null && !liveSocket.isClosed()) {
                            Thread.sleep(4500);
                            synchronized (MainActivity.this) {
                                if (liveSocket.isClosed()) break;
                                sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PING\"}");
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

    private static void sendCastMsg(OutputStream out, String src, String dst, String ns, String payload) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        baos.write(new byte[]{0x08, 0x00});
        writeField(baos, 2, src);
        writeField(baos, 3, dst);
        writeField(baos, 4, ns);
        baos.write(new byte[]{0x28, 0x00});
        writeField(baos, 6, payload);

        byte[] body = baos.toByteArray();
        int len = body.length;
        out.write((len >> 24) & 0xff);
        out.write((len >> 16) & 0xff);
        out.write((len >> 8) & 0xff);
        out.write(len & 0xff);
        out.write(body);
        out.flush();
    }

    private static void writeField(ByteArrayOutputStream out, int fieldNum, String val) throws Exception {
        byte[] b = val.getBytes("UTF-8");
        out.write((fieldNum << 3) | 2);
        int n = b.length;
        while ((n & ~0x7F) != 0) {
            out.write((n & 0x7F) | 0x80);
            n >>>= 7;
        }
        out.write(n);
        out.write(b);
    }

    private static byte[] readCastMsg(InputStream in) throws Exception {
        byte[] hdr = new byte[4];
        int read = 0;
        while (read < 4) {
            int r = in.read(hdr, read, 4 - read);
            if (r < 0) return null;
            read += r;
        }
        int len = ((hdr[0] & 0xff) << 24) | ((hdr[1] & 0xff) << 16) | ((hdr[2] & 0xff) << 8) | (hdr[3] & 0xff);
        if (len <= 0 || len > 65536) return null;
        byte[] body = new byte[len];
        int bodyRead = 0;
        while (bodyRead < len) {
            int r = in.read(body, bodyRead, len - bodyRead);
            if (r < 0) return null;
            bodyRead += r;
        }
        return body;
    }

    // --- DIAL YouTube Engine (Port 56789 / 8008) ---
    private boolean launchDialYouTube(String ip, String vidId) {
        int[] ports = new int[]{56789, 8008};
        for (int p : ports) {
            try {
                URL url = new URL("http://" + ip + ":" + p + "/apps/YouTube");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setConnectTimeout(800);
                conn.setReadTimeout(800);
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                byte[] data = ("v=" + vidId).getBytes("UTF-8");
                conn.setFixedLengthStreamingMode(data.length);
                OutputStream os = conn.getOutputStream();
                os.write(data);
                os.flush();
                os.close();
                int rc = conn.getResponseCode();
                conn.disconnect();
                if (rc == 200 || rc == 201) return true;
            } catch (Exception ignored) {}
        }
        return false;
    }

    // --- DLNA AVTransport Engine (Port 38400) ---
    private boolean sendDlnaCast(String controlUrl, String mediaUrl, String title) {
        try {
            boolean isHls = mediaUrl.contains(".m3u8");
            String proto = isHls ? "http-get:*:application/vnd.apple.mpegurl:DLNA.ORG_OP=00;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000" : "http-get:*:video/mp4:*";
            String itemClass = isHls ? "object.item.videoItem.videoBroadcast" : "object.item.videoItem";

            String didl = "&lt;DIDL-Lite xmlns=\"urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:upnp=\"urn:schemas-upnp-org:metadata-1-0/upnp/\"&gt;"
                    + "&lt;item id=\"1\" parentID=\"0\" restricted=\"1\"&gt;"
                    + "&lt;dc:title&gt;" + escapeXml(title) + "&lt;/dc:title&gt;"
                    + "&lt;upnp:class&gt;" + itemClass + "&lt;/upnp:class&gt;"
                    + "&lt;res protocolInfo=\"" + proto + "\"&gt;" + escapeXml(mediaUrl) + "&lt;/res&gt;"
                    + "&lt;/item&gt;&lt;/DIDL-Lite&gt;";

            String setUriBody = "<InstanceID>0</InstanceID>"
                    + "<CurrentURI>" + escapeXml(mediaUrl) + "</CurrentURI>"
                    + "<CurrentURIMetaData>" + didl + "</CurrentURIMetaData>";

            boolean uriSet = sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "SetAVTransportURI", setUriBody);
            if (!uriSet) return false;

            Thread.sleep(100);

            String playBody = "<InstanceID>0</InstanceID><Speed>1</Speed>";
            return sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Play", playBody);
        } catch (Exception e) {
            return false;
        }
    }

    private boolean sendSoap(String controlUrl, String serviceType, String action, String bodyArgs) {
        try {
            URL url = new URL(controlUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setConnectTimeout(2000);
            conn.setReadTimeout(2000);
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "text/xml; charset=\"utf-8\"");
            conn.setRequestProperty("SOAPAction", "\"" + serviceType + "#" + action + "\"");

            String envelope = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n"
                    + "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\r\n"
                    + "  <s:Body>\r\n"
                    + "    <u:" + action + " xmlns:u=\"" + serviceType + "\">\r\n"
                    + "      " + bodyArgs + "\r\n"
                    + "    </u:" + action + ">\r\n"
                    + "  </s:Body>\r\n"
                    + "</s:Envelope>";

            byte[] b = envelope.getBytes("UTF-8");
            conn.setFixedLengthStreamingMode(b.length);
            OutputStream os = conn.getOutputStream();
            os.write(b);
            os.flush();
            os.close();

            int rc = conn.getResponseCode();
            conn.disconnect();
            return (rc >= 200 && rc < 300);
        } catch (Exception e) {
            return false;
        }
    }

    // --- Wake-on-LAN UDP Broadcast ---
    private void sendWakeOnLanPacket() {
        String[] macs = new String[]{"18:30:0c:9e:7e:fc", "3c:c5:dd:00:00:00", "ffffffffffff"};
        for (String mac : macs) {
            try {
                String clean = mac.replace(":", "").replace("-", "");
                if (clean.length() != 12) continue;
                byte[] macBytes = new byte[6];
                for (int i = 0; i < 6; i++) {
                    macBytes[i] = (byte) Integer.parseInt(clean.substring(i * 2, i * 2 + 2), 16);
                }
                byte[] bytes = new byte[102];
                for (int i = 0; i < 6; i++) bytes[i] = (byte) 0xff;
                for (int i = 6; i < 102; i++) bytes[i] = macBytes[i % 6];

                DatagramSocket socket = new DatagramSocket();
                socket.setBroadcast(true);
                DatagramPacket packet = new DatagramPacket(bytes, bytes.length, InetAddress.getByName("255.255.255.255"), 9);
                socket.send(packet);
                socket.close();
            } catch (Exception ignored) {}
        }
    }

    private static String escapeXml(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;");
    }

    private static String escapeJson(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r");
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (customView != null) {
                customViewContainer.removeView(customView);
                customViewContainer.setVisibility(View.GONE);
                customView = null;
                webView.setVisibility(View.VISIBLE);
                setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
                return true;
            }
            if (webView.canGoBack()) {
                webView.goBack();
                return true;
            }
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        closeActiveCast();
        if (multicastLock != null && multicastLock.isHeld()) {
            multicastLock.release();
        }
    }
}
JAVA

echo '=== Packaging resources and assets with aapt ==='
ANDROID_JAR=/usr/lib/android-sdk/platforms/android-23/android.jar
aapt package -f -m -J $BUILD_DIR/src -M $BUILD_DIR/AndroidManifest.xml -S $BUILD_DIR/res -A $BUILD_DIR/assets -I $ANDROID_JAR

echo '=== Compiling Java sources ==='
javac -source 8 -target 8 -bootclasspath $ANDROID_JAR -d $BUILD_DIR/bin $BUILD_DIR/src/com/tvhub/app/*.java

echo '=== Converting bytecode to Dalvik DEX ==='
dalvik-exchange --dex --output=$BUILD_DIR/bin/classes.dex $BUILD_DIR/bin

echo '=== Creating unaligned APK with assets ==='
aapt package -f -M $BUILD_DIR/AndroidManifest.xml -S $BUILD_DIR/res -A $BUILD_DIR/assets -I $ANDROID_JAR -F $BUILD_DIR/bin/unaligned.apk $BUILD_DIR/bin

echo '=== Aligning APK with zipalign ==='
zipalign -f -p 4 $BUILD_DIR/bin/unaligned.apk $BUILD_DIR/bin/aligned.apk

echo '=== Generating Keystore & Signing APK (v1 + v2 + v3) ==='
KEYSTORE=$BUILD_DIR/release.jks
if [ ! -f $KEYSTORE ]; then
    keytool -genkeypair -v -keystore $KEYSTORE -alias tvhub -keyalg RSA -keysize 2048 -validity 10000 -storepass tvhubpass -keypass tvhubpass -dname 'CN=TVHub, OU=Home, O=TVHub, L=Tbilisi, ST=Tbilisi, C=GE'
fi

apksigner sign --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --ks $KEYSTORE --ks-key-alias tvhub --ks-pass pass:tvhubpass --key-pass pass:tvhubpass --out $BUILD_DIR/TVHub.apk $BUILD_DIR/bin/aligned.apk

echo '=== Verifying APK Signature ==='
apksigner verify --verbose $BUILD_DIR/TVHub.apk

cp $BUILD_DIR/TVHub.apk /home/ubuntu/Home-TV/static/TVHub.apk
cp $BUILD_DIR/TVHub.apk /home/ubuntu/Home-TV/TVHub.apk

echo '=== Done! Autonomous Host APK successfully created at /home/ubuntu/Home-TV/TVHub.apk ==='
ls -lh /home/ubuntu/Home-TV/TVHub.apk
