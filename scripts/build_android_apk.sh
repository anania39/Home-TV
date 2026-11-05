#!/bin/bash
set -e
echo '=== Building Fully Autonomous TV Hub Android Host App (v7.8.1) ==='

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
rm -f $BUILD_DIR/assets/TVHub.apk $BUILD_DIR/assets/*.apk
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
    android:versionCode="793"
    android:versionName="7.9.3">

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
            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="text/plain" />
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

import org.json.JSONObject;
import org.json.JSONArray;
import android.content.ClipboardManager;
import android.content.ClipData;
import android.content.Intent;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.URLEncoder;
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
import java.util.Map;
import java.util.HashMap;

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
    private int activeMediaSessionId = 1;
    private double liveTvCurrentTime = 0.0;
    private double liveTvDuration = 0.0;
    private int castRequestId = 10;
    private String lastCastType = "";
    private String lastCastIp = "192.168.50.205";
    private String lastLoungeToken = null;
    private String lastSid = null;
    private String lastGsessionId = null;
    private int loungeRid = 2;

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

    private String pendingSharedUrl = "";

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIncomingIntent(intent);
    }

    private void handleIncomingIntent(Intent intent) {
        if (intent != null && Intent.ACTION_SEND.equals(intent.getAction()) && "text/plain".equals(intent.getType())) {
            String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (sharedText != null && !sharedText.isEmpty()) {
                pendingSharedUrl = sharedText.trim();
                if (webView != null) {
                    webView.post(new Runnable() {
                        @Override
                        public void run() {
                            webView.evaluateJavascript("if (typeof handleSharedUrl === 'function') { handleSharedUrl('" + escapeJson(pendingSharedUrl) + "'); }", null);
                        }
                    });
                }
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        handleIncomingIntent(getIntent());
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
        settings.setUserAgentString("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 TVHubHostApp/7.8.5");

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
                        view.loadUrl("https://tvhub.92.5.71.162.sslip.io?v=7.9.1");
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

        webView.loadUrl("https://tvhub.92.5.71.162.sslip.io?v=7.9.1");
    }

    // --- Native Android Host Bridge Exposed to JavaScript ---
    public class TVHubBridge {
        @JavascriptInterface
        public boolean isNativeApp() {
            return true;
        }

        @JavascriptInterface
        public String getClipboardText() {
            final String[] result = new String[]{""};
            final java.util.concurrent.CountDownLatch latch = new java.util.concurrent.CountDownLatch(1);
            mainHandler.post(new Runnable() {
                @Override
                public void run() {
                    try {
                        ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                        if (cm != null && cm.hasPrimaryClip()) {
                            ClipData clip = cm.getPrimaryClip();
                            if (clip != null && clip.getItemCount() > 0) {
                                CharSequence text = clip.getItemAt(0).getText();
                                if (text != null) result[0] = text.toString();
                            }
                        }
                    } catch (Exception ignored) {}
                    finally {
                        latch.countDown();
                    }
                }
            });
            try {
                latch.await(600, java.util.concurrent.TimeUnit.MILLISECONDS);
            } catch (Exception ignored) {}
            return result[0];
        }

        @JavascriptInterface
        public String getPendingSharedUrl() {
            String url = pendingSharedUrl;
            pendingSharedUrl = "";
            return url;
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

        @JavascriptInterface
        public void controlPlayback(final String action, final String value) {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    performPlaybackControl(action, value);
                }
            }).start();
        }
    }

    // --- Structured Cast V2 Media Status Data Model & JSON Parser ---
    private static class MediaStatusInfo {
        int mediaSessionId = 0;
        double currentTime = 0.0;
        double duration = 0.0;
        double playbackRate = 1.0;
        String playerState = "";
    }

    private static MediaStatusInfo parseMediaStatus(String text) {
        if (text == null) return null;
        try {
            int brace = text.indexOf('{');
            if (brace == -1) return null;
            JSONObject root = new JSONObject(text.substring(brace));
            if ("MEDIA_STATUS".equals(root.optString("type")) || root.has("status")) {
                JSONArray arr = root.optJSONArray("status");
                if (arr != null && arr.length() > 0) {
                    JSONObject item = arr.getJSONObject(0);
                    MediaStatusInfo info = new MediaStatusInfo();
                    info.mediaSessionId = item.optInt("mediaSessionId", 0);
                    info.currentTime = item.optDouble("currentTime", 0.0);
                    info.playbackRate = item.optDouble("playbackRate", 1.0);
                    info.playerState = item.optString("playerState", "");
                    JSONObject media = item.optJSONObject("media");
                    if (media != null && media.has("duration")) {
                        info.duration = media.optDouble("duration", 0.0);
                    }
                    if (info.duration <= 0) {
                        JSONArray items = item.optJSONArray("items");
                        if (items != null && items.length() > 0) {
                            JSONObject m0 = items.getJSONObject(0).optJSONObject("media");
                            if (m0 != null && m0.has("duration")) {
                                info.duration = m0.optDouble("duration", 0.0);
                            }
                        }
                    }
                    return info;
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    // --- Native Direct Playback & Speed Control Engine ---
    private void performPlaybackControl(String action, String value) {
        if (action == null) return;
        action = action.toLowerCase().trim();

        if (lastCastType == null || lastCastType.isEmpty()) {
            if (activeCastOut != null) {
                lastCastType = "cast";
            } else if (lastLoungeToken != null) {
                lastCastType = "youtube";
            }
        }

        // 1. YouTube MDX Lounge Control (Strictly Isolated - NEVER send Cast V2 media to YouTube)
        if ("youtube".equals(lastCastType)) {
            ensureLoungeSession();
            if (lastLoungeToken != null && lastSid != null && lastGsessionId != null) {
                if ("play".equals(action)) {
                    sendLoungeCommand("playVideo", null);
                    notifyUser("▶️ Playing YouTube on TV");
                } else if ("pause".equals(action)) {
                    sendLoungeCommand("pauseVideo", null);
                    notifyUser("⏸️ Paused YouTube on TV");
                } else if ("stop".equals(action)) {
                    sendLoungeCommand("stopVideo", null);
                    notifyUser("⏹️ Stopped YouTube Cast");
                } else if ("speed".equals(action) || "rate".equals(action)) {
                    Map<String, String> p = new HashMap<>();
                    p.put("req0_playbackRate", value);
                    p.put("req0_rate", value);
                    p.put("req0_playbackSpeed", value);
                    p.put("req0_speed", value);
                    sendLoungeCommand("setPlaybackRate", p);
                    sendLoungeCommand("setPlaybackSpeed", p);
                    notifyUser("⚡ Playback Speed: " + value + "x on TV");
                } else if ("seek".equals(action) || "seek_relative".equals(action)) {
                    int sec = 0;
                    if ("seek_relative".equals(action) || (value != null && (value.startsWith("+") || value.startsWith("-")))) {
                        double delta = Double.parseDouble(value);
                        sec = (int) Math.max(0.0, liveTvCurrentTime + delta);
                        notifyUser((delta < 0 ? "⏪ Rewound " + (int)Math.abs(delta) : "⏩ Forward " + (int)delta) + "s on TV");
                    } else {
                        try { sec = (int) Double.parseDouble(value); } catch (Exception ignored) {}
                        int mins = sec / 60;
                        int remSecs = sec % 60;
                        String timeStr = String.format("%02d:%02d", mins, remSecs);
                        notifyUser("⏩ Jumped to " + timeStr + " on TV");
                    }
                    liveTvCurrentTime = sec;
                    Map<String, String> p = new HashMap<>();
                    p.put("req0_newTime", String.valueOf(Math.max(0, sec)));
                    sendLoungeCommand("seekTo", p);
                }
            }
            return; // Finished YouTube control! NEVER fall through to sendCastDirectControl!
        }

        // 2. Cast V2 Active Socket for Default Media Receiver (CC1AD845) - Movies & Channels
        if (activeCastOut != null && currentTransportId != null) {
            try {
                int reqId = ++castRequestId;
                String msgJson = null;
                int sessId = activeMediaSessionId > 0 ? activeMediaSessionId : 1;
                if ("speed".equals(action) || "rate".equals(action)) {
                    double r = Double.parseDouble(value);
                    msgJson = "{\"type\":\"SET_PLAYBACK_RATE\",\"playbackRate\":" + r + ",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("⚡ Playback Speed: " + value + "x on TV");
                } else if ("play".equals(action)) {
                    msgJson = "{\"type\":\"PLAY\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("▶️ Playing on TV");
                } else if ("pause".equals(action)) {
                    msgJson = "{\"type\":\"PAUSE\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("⏸️ Paused on TV");
                } else if ("stop".equals(action)) {
                    msgJson = "{\"type\":\"STOP\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("⏹️ Stopped TV Cast");
                } else if ("seek".equals(action) || "seek_relative".equals(action)) {
                    double targetSec = 0.0;
                    if ("seek_relative".equals(action) || (value != null && (value.startsWith("+") || value.startsWith("-")))) {
                        double delta = Double.parseDouble(value);
                        targetSec = Math.max(0.0, liveTvCurrentTime + delta);
                        notifyUser((delta < 0 ? "⏪ Rewound " + (int)Math.abs(delta) : "⏩ Forward " + (int)delta) + "s on TV");
                    } else {
                        targetSec = Math.max(0.0, Double.parseDouble(value));
                        notifyUser("⏩ Seeked to " + (int) targetSec + "s on TV");
                    }
                    liveTvCurrentTime = targetSec;
                    msgJson = "{\"type\":\"SEEK\",\"currentTime\":" + targetSec + ",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                } else if ("subtitles".equals(action)) {
                    if ("off".equalsIgnoreCase(value) || "0".equals(value)) {
                        msgJson = "{\"type\":\"EDIT_TRACKS_INFO\",\"activeTrackIds\":[],\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                        notifyUser("💬 Subtitles: Off");
                    } else {
                        try {
                            int tId = Integer.parseInt(value);
                            msgJson = "{\"type\":\"EDIT_TRACKS_INFO\",\"activeTrackIds\":[" + tId + "],\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                            notifyUser("💬 Subtitles Enabled");
                        } catch (Exception ex) {
                            msgJson = "{\"type\":\"EDIT_TRACKS_INFO\",\"activeTrackIds\":[1],\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                            notifyUser("💬 Subtitles Enabled");
                        }
                    }
                } else if ("quality".equals(action)) {
                    notifyUser("📺 Quality: " + value);
                    return;
                }
                if (msgJson != null) {
                    synchronized (MainActivity.this) {
                        sendCastMsg(activeCastOut, "sender-0", currentTransportId, "urn:x-cast:com.google.cast.media", msgJson);
                    }
                    return;
                }
            } catch (Exception ignored) {}
        }

        // 3. Fallback direct Cast V2 (Only for CC1AD845, never for YouTube)
        sendCastDirectControl(action, value);
        // 3. DLNA Control for Hisense TV
        if ("dlna".equals(lastCastType) || (lastCastIp != null && (lastCastIp.endsWith(".249") || lastCastIp.contains("hisense")))) {
            String controlUrl = "http://" + lastCastIp + ":38400/upnp/control/mingusavtr";
            if ("play".equals(action)) {
                sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Play", "<InstanceID>0</InstanceID><Speed>1</Speed>");
            } else if ("pause".equals(action)) {
                sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Pause", "<InstanceID>0</InstanceID>");
            } else if ("stop".equals(action)) {
                sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Stop", "<InstanceID>0</InstanceID>");
            }
        }
    }

    private synchronized boolean sendLoungeCommand(String sc, Map<String, String> extraParams) {
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                if (lastLoungeToken == null || lastSid == null || lastGsessionId == null) {
                    if (!ensureLoungeSession()) return false;
                }
                int rid = loungeRid++;
                URL cmdUrl = new URL("https://www.youtube.com/api/lounge/bc/bind?SID=" + URLEncoder.encode(lastSid, "UTF-8") + "&gsessionid=" + URLEncoder.encode(lastGsessionId, "UTF-8") + "&RID=" + rid + "&VER=8&CVER=1");
                HttpURLConnection conn = (HttpURLConnection) cmdUrl.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setConnectTimeout(4000);
                conn.setReadTimeout(4000);
                conn.setRequestProperty("Origin", "https://www.youtube.com");
                conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                conn.setRequestProperty("X-YouTube-LoungeId-Token", lastLoungeToken);

                StringBuilder sb = new StringBuilder();
                sb.append("count=1&req0__sc=").append(URLEncoder.encode(sc, "UTF-8"));
                if (extraParams != null) {
                    for (Map.Entry<String, String> entry : extraParams.entrySet()) {
                        sb.append("&").append(URLEncoder.encode(entry.getKey(), "UTF-8")).append("=").append(URLEncoder.encode(entry.getValue(), "UTF-8"));
                    }
                }
                byte[] postData = sb.toString().getBytes("UTF-8");
                conn.setFixedLengthStreamingMode(postData.length);
                OutputStream os = conn.getOutputStream();
                os.write(postData);
                os.flush();
                os.close();

                int respCode = conn.getResponseCode();
                if (respCode == 200) return true;
                lastLoungeToken = null;
                lastSid = null;
                lastGsessionId = null;
            } catch (Exception e) {
                lastLoungeToken = null;
                lastSid = null;
                lastGsessionId = null;
            }
        }
        return false;
    }

    private synchronized boolean ensureLoungeSession() {
        if (lastLoungeToken != null && lastSid != null && lastGsessionId != null) return true;
        try {
            String ip = (lastCastIp != null && !lastCastIp.isEmpty()) ? lastCastIp : "192.168.50.205";
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
            socket.setSoTimeout(4000);
            socket.startHandshake();

            OutputStream out = socket.getOutputStream();
            InputStream in = socket.getInputStream();

            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"GET_STATUS\",\"requestId\":1}");

            String transportId = null;
            long startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 6000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    String tid = extractTransportIdForApp(text, "233637DE");
                    if (tid != null && !tid.isEmpty()) {
                        transportId = tid;
                        break;
                    }
                } catch (java.net.SocketTimeoutException ste) {
                    continue;
                } catch (Exception ignored) {
                    break;
                }
            }

            if (transportId == null) {
                socket.close();
                return false;
            }

            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.youtube.mdx", "{\"type\":\"getMdxSessionStatus\"}");

            String screenId = null;
            startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 6000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    int idx = text.indexOf("\"screenId\":\"");
                    if (idx != -1) {
                        int endIdx = text.indexOf("\"", idx + 12);
                        if (endIdx != -1) {
                            screenId = text.substring(idx + 12, endIdx);
                            break;
                        }
                    }
                } catch (java.net.SocketTimeoutException ste) {
                    continue;
                } catch (Exception ignored) {
                    break;
                }
            }
            socket.close();

            if (screenId == null || screenId.isEmpty()) return false;

            URL tokenUrl = new URL("https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch");
            HttpURLConnection conn1 = (HttpURLConnection) tokenUrl.openConnection();
            conn1.setRequestMethod("POST");
            conn1.setDoOutput(true);
            conn1.setConnectTimeout(4000);
            conn1.setReadTimeout(4000);
            conn1.setRequestProperty("Origin", "https://www.youtube.com");
            conn1.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            byte[] postData1 = ("screen_ids=" + URLEncoder.encode(screenId, "UTF-8")).getBytes("UTF-8");
            conn1.setFixedLengthStreamingMode(postData1.length);
            OutputStream os1 = conn1.getOutputStream();
            os1.write(postData1);
            os1.flush();
            os1.close();

            BufferedReader br1 = new BufferedReader(new InputStreamReader(conn1.getInputStream(), "UTF-8"));
            StringBuilder sb1 = new StringBuilder();
            String line;
            while ((line = br1.readLine()) != null) sb1.append(line);
            br1.close();

            String tokenResp = sb1.toString();
            int tIdx = tokenResp.indexOf("\"loungeToken\":\"");
            if (tIdx == -1) return false;
            int tEnd = tokenResp.indexOf("\"", tIdx + 15);
            String loungeToken = tokenResp.substring(tIdx + 15, tEnd);

            URL bindUrl = new URL("https://www.youtube.com/api/lounge/bc/bind?RID=0&VER=8&CVER=1");
            HttpURLConnection conn2 = (HttpURLConnection) bindUrl.openConnection();
            conn2.setRequestMethod("POST");
            conn2.setDoOutput(true);
            conn2.setConnectTimeout(4000);
            conn2.setReadTimeout(4000);
            conn2.setRequestProperty("Origin", "https://www.youtube.com");
            conn2.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            conn2.setRequestProperty("X-YouTube-LoungeId-Token", loungeToken);
            String bindBody = "device=REMOTE_CONTROL&id=tvhubandroid123456789&name=Android&mdx-version=3&pairing_type=cast&app=android-phone-13.14.55";
            byte[] bindBytes = bindBody.getBytes("UTF-8");
            conn2.setFixedLengthStreamingMode(bindBytes.length);
            OutputStream os2 = conn2.getOutputStream();
            os2.write(bindBytes);
            os2.flush();
            os2.close();

            BufferedReader br2 = new BufferedReader(new InputStreamReader(conn2.getInputStream(), "UTF-8"));
            StringBuilder sb2 = new StringBuilder();
            while ((line = br2.readLine()) != null) sb2.append(line);
            br2.close();

            String bindResp = sb2.toString();
            int sidIdx = bindResp.indexOf("\"c\",\"");
            if (sidIdx == -1) return false;
            int sidEnd = bindResp.indexOf("\"", sidIdx + 5);
            String sid = bindResp.substring(sidIdx + 5, sidEnd);

            int gIdx = bindResp.indexOf("\"S\",\"");
            if (gIdx == -1) return false;
            int gEnd = bindResp.indexOf("\"", gIdx + 5);
            String gsessionid = bindResp.substring(gIdx + 5, gEnd);

            lastLoungeToken = loungeToken;
            lastSid = sid;
            lastGsessionId = gsessionid;
            loungeRid = 2;
            lastCastType = "youtube";
            return true;
        } catch (Exception ignored) {}
        return false;
    }

    private synchronized void sendCastDirectControl(String action, String value) {
        try {
            String ip = (lastCastIp != null && !lastCastIp.isEmpty()) ? lastCastIp : "192.168.50.205";
            TrustManager[] trustAll = new TrustManager[]{
                new X509TrustManager() {
                    public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
                    public void checkClientTrusted(X509Certificate[] c, String a) {}
                    public void checkServerTrusted(X509Certificate[] c, String a) {}
                }
            };
            SSLContext sc = SSLContext.getInstance("TLS");
            sc.init(null, trustAll, new SecureRandom());
            SSLSocket s = (SSLSocket) sc.getSocketFactory().createSocket(ip, 8009);
            s.setSoTimeout(2500);
            s.startHandshake();

            OutputStream o = s.getOutputStream();
            InputStream i = s.getInputStream();

            String ctlSender = "sender-ctl-" + (System.currentTimeMillis() % 100000);
            sendCastMsg(o, ctlSender, "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(o, ctlSender, "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"GET_STATUS\",\"requestId\":1}");

            String tid = null;
            long startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 3000) {
                try {
                    byte[] raw = readCastMsg(i);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    String[] appInfo = extractActiveMediaApp(text);
                    if (appInfo != null) {
                        if ("233637DE".equals(appInfo[0])) {
                            // YouTube app is running - do not send Cast V2 media namespace commands!
                            s.close();
                            return;
                        }
                        tid = appInfo[1];
                        break;
                    }
                } catch (Exception ignored) {}
            }

            if (tid != null) {
                sendCastMsg(o, ctlSender, tid, "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
                sendCastMsg(o, ctlSender, tid, "urn:x-cast:com.google.cast.media", "{\"type\":\"GET_STATUS\",\"requestId\":2}");
                long waitSt = System.currentTimeMillis();
                while (System.currentTimeMillis() - waitSt < 2000) {
                    try {
                        byte[] raw = readCastMsg(i);
                        if (raw == null) break;
                        String text = new String(raw, "UTF-8");
                        MediaStatusInfo st = parseMediaStatus(text);
                        if (st != null && st.mediaSessionId > 0) {
                            activeMediaSessionId = st.mediaSessionId;
                            liveTvCurrentTime = st.currentTime;
                            break;
                        }
                    } catch (Exception ignored) { break; }
                }
                String payload = null;
                int reqId = ++castRequestId;
                int sessId = activeMediaSessionId > 0 ? activeMediaSessionId : 1;
                if ("speed".equals(action) || "rate".equals(action)) {
                    double r = Double.parseDouble(value);
                    payload = "{\"type\":\"SET_PLAYBACK_RATE\",\"playbackRate\":" + r + ",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("⚡ Playback Speed: " + value + "x on TV");
                } else if ("play".equals(action)) {
                    payload = "{\"type\":\"PLAY\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("▶️ Playing on TV");
                } else if ("pause".equals(action)) {
                    payload = "{\"type\":\"PAUSE\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("⏸️ Paused on TV");
                } else if ("stop".equals(action)) {
                    payload = "{\"type\":\"STOP\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                    notifyUser("⏹️ Stopped TV Cast");
                } else if ("seek".equals(action) || "seek_relative".equals(action)) {
                    double targetSec = 0.0;
                    if ("seek_relative".equals(action) || (value != null && (value.startsWith("+") || value.startsWith("-")))) {
                        double delta = Double.parseDouble(value);
                        targetSec = Math.max(0.0, liveTvCurrentTime + delta);
                        notifyUser((delta < 0 ? "⏪ Rewound " + (int)Math.abs(delta) : "⏩ Forward " + (int)delta) + "s on TV");
                    } else {
                        targetSec = Math.max(0.0, Double.parseDouble(value));
                        notifyUser("⏩ Seeked to " + (int) targetSec + "s on TV");
                    }
                    liveTvCurrentTime = targetSec;
                    payload = "{\"type\":\"SEEK\",\"currentTime\":" + targetSec + ",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                } else if ("subtitles".equals(action)) {
                    if ("off".equalsIgnoreCase(value) || "0".equals(value)) {
                        payload = "{\"type\":\"EDIT_TRACKS_INFO\",\"activeTrackIds\":[],\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                        notifyUser("💬 Subtitles: Off");
                    } else {
                        try {
                            int tId = Integer.parseInt(value);
                            payload = "{\"type\":\"EDIT_TRACKS_INFO\",\"activeTrackIds\":[" + tId + "],\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                            notifyUser("💬 Subtitles Enabled");
                        } catch (Exception ex) {
                            payload = "{\"type\":\"EDIT_TRACKS_INFO\",\"activeTrackIds\":[1],\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
                            notifyUser("💬 Subtitles Enabled");
                        }
                    }
                } else if ("quality".equals(action)) {
                    notifyUser("📺 Quality: " + value);
                    return;
                }
                if (payload != null) {
                    sendCastMsg(o, ctlSender, tid, "urn:x-cast:com.google.cast.media", payload);
                }
            }
            s.close();
        } catch (Exception ignored) {}
    }

    private void performDirectCast(String ip, String devType, String streamUrl, String title, String mimeType, String youtubeId) {
        String targetIp = (ip != null && !ip.isEmpty()) ? ip : "192.168.50.205";
        if (streamUrl != null && streamUrl.startsWith("/")) {
            streamUrl = "https://tvhub.92.5.71.162.sslip.io" + streamUrl;
        }
        // Retain Ad-Shield Proxy for all media (including YouTube and movie platforms) so headers/anti-bot are handled cleanly
        String type = (devType != null) ? devType.toLowerCase() : "";

        // 1. Wake TV from standby via direct local UDP magic packet
        sendWakeOnLanPacket();

        // 2. Google Cast Protocol for TCL Smart TV Pro (192.168.50.205:8009) & Google TVs
        if (type.contains("google_tv") || targetIp.endsWith(".205") || targetIp.endsWith(".3")) {
            if (youtubeId != null && !youtubeId.isEmpty()) {
                notifyUser("Launching YouTube on TCL Smart TV Pro...");
                boolean ytOk = castYouTubeToGoogleTv(targetIp, youtubeId);
                if (ytOk) {
                    notifyUser("🎉 Playing YouTube on TCL Smart TV Pro!");
                    return;
                }
            }
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
        if (youtubeId != null && !youtubeId.isEmpty()) {
            if (castYouTubeToGoogleTv(targetIp, youtubeId)) {
                notifyUser("🎉 Playing YouTube on Smart TV!");
                return;
            }
        }
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

    // --- Active Media App Extractor (Handles both YouTube 233637DE and Media Receiver CC1AD845) ---
    private static String[] extractActiveMediaApp(String text) {
        if (text == null) return null;
        try {
            int brace = text.indexOf('{');
            if (brace == -1) return null;
            JSONObject root = new JSONObject(text.substring(brace));
            if (root.has("status")) {
                JSONObject st = root.getJSONObject("status");
                if (st.has("applications")) {
                    JSONArray apps = st.getJSONArray("applications");
                    for (int i = 0; i < apps.length(); i++) {
                        JSONObject app = apps.getJSONObject(i);
                        String appId = app.optString("appId");
                        String tid = app.optString("transportId", null);
                        if (tid != null && ("CC1AD845".equals(appId) || "233637DE".equals(appId) || "2C6A6E3D".equals(appId))) {
                            return new String[]{appId, tid};
                        }
                    }
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    // --- Dedicated TransportId Extractor: Guarantees Matching Target AppId ---
    private static String extractTransportIdForApp(String text, String targetAppId) {
        if (text == null || targetAppId == null) return null;
        try {
            int brace = text.indexOf('{');
            if (brace == -1) return null;
            JSONObject root = new JSONObject(text.substring(brace));
            if (root.has("status")) {
                JSONObject st = root.getJSONObject("status");
                if (st.has("applications")) {
                    JSONArray apps = st.getJSONArray("applications");
                    for (int i = 0; i < apps.length(); i++) {
                        JSONObject app = apps.getJSONObject(i);
                        if (targetAppId.equals(app.optString("appId"))) {
                            return app.optString("transportId", null);
                        }
                    }
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    // --- Google Cast V2 TLS Engine (Port 8009) with Bi-directional Heartbeat ---
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

            // 1. Send CONNECT to receiver-0 and check active status
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"GET_STATUS\",\"requestId\":1}");

            String transportId = null;
            long startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 2500) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    String tid = extractTransportIdForApp(text, "CC1AD845");
                    if (tid != null && !tid.isEmpty()) {
                        transportId = tid;
                        break;
                    }
                } catch (java.net.SocketTimeoutException ste) {
                    break;
                } catch (Exception ignored) {
                    break;
                }
            }

            // Only send LAUNCH if CC1AD845 was NOT already running!
            // This prevents the blue Google Cast backdrop splash screen from ever reappearing!
            if (transportId == null || transportId.isEmpty()) {
                sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"LAUNCH\",\"appId\":\"CC1AD845\",\"requestId\":2}");
                startWait = System.currentTimeMillis();
                while (System.currentTimeMillis() - startWait < 8500) {
                    try {
                        byte[] raw = readCastMsg(in);
                        if (raw == null) break;
                        String text = new String(raw, "UTF-8");
                        String tid = extractTransportIdForApp(text, "CC1AD845");
                        if (tid != null && !tid.isEmpty()) {
                            transportId = tid;
                            break;
                        }
                    } catch (java.net.SocketTimeoutException ste) {
                        try {
                            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"GET_STATUS\",\"requestId\":3}");
                        } catch (Exception ignored) {}
                    } catch (Exception ignored) {
                        break;
                    }
                }
            }

            if (transportId == null || transportId.isEmpty()) {
                notifyUser("⚠️ Smart TV Cast receiver not ready. Retrying...");
                closeActiveCast();
                return false;
            }

            // 3. Connect to media transport endpoint
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");

            // 4. Send LOAD command with stream URL
            boolean isHls = streamUrl.contains(".m3u8") || streamUrl.contains("/proxy?url=");
            String mime = isHls ? "application/x-mpegurl" : "video/mp4";
            boolean isVod = streamUrl.contains("movie") || streamUrl.contains("videodb") || streamUrl.contains(".mp4") || (streamUrl.contains("googlevideo") && !streamUrl.contains("live"));
            String streamType = isVod ? "BUFFERED" : "LIVE";
            String loadJson = "{\"type\":\"LOAD\",\"requestId\":3,\"autoplay\":true,\"media\":{\"contentId\":\"" + escapeJson(streamUrl) + "\",\"streamType\":\"" + streamType + "\",\"contentType\":\"" + mime + "\",\"metadata\":{\"metadataType\":0,\"title\":\"" + escapeJson(title) + "\"} } }";
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.media", loadJson);
            activeMediaSessionId = 1;

            // Wait up to 3s to capture the real mediaSessionId from MEDIA_STATUS
            long waitSt = System.currentTimeMillis();
            while (System.currentTimeMillis() - waitSt < 3000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    MediaStatusInfo st = parseMediaStatus(text);
                    if (st != null && st.mediaSessionId > 0) {
                        activeMediaSessionId = st.mediaSessionId;
                        liveTvCurrentTime = st.currentTime;
                        if (st.duration > 0) liveTvDuration = st.duration;
                        break;
                    }
                } catch (Exception ignored) { break; }
            }

            // 5. Keep connection alive with FULL BI-DIRECTIONAL PING/PONG READER THREAD
            activeCastSocket = socket;
            activeCastOut = out;
            activeCastIp = ip;
            currentTransportId = transportId;
            lastCastType = "cast";
            lastCastIp = ip;

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
                                    sendCastMsg(activeOut, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PING\"}");
                                    sendCastMsg(activeOut, "sender-0", activeTid, "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PING\"}");
                                }
                                lastPingSent = now;
                            }
                            try {
                                byte[] raw = readCastMsg(activeIn);
                                if (raw != null) {
                                    String text = new String(raw, "UTF-8");
                                    MediaStatusInfo st = parseMediaStatus(text);
                                    if (st != null && st.mediaSessionId > 0) {
                                        activeMediaSessionId = st.mediaSessionId;
                                        liveTvCurrentTime = st.currentTime;
                                        if (st.duration > 0) liveTvDuration = st.duration;
                                        final double cTime = st.currentTime;
                                        final double dTime = st.duration > 0 ? st.duration : liveTvDuration;
                                        final String pState = st.playerState;
                                        mainHandler.post(new Runnable() {
                                            @Override
                                            public void run() {
                                                if (webView != null) {
                                                    webView.evaluateJavascript("if (window.syncNativePlaybackState) window.syncNativePlaybackState(" + cTime + ", " + dTime + ", '" + pState + "');", null);
                                                }
                                            }
                                        });
                                    }
                                    if (text.contains("\"PING\"")) {
                                        synchronized (MainActivity.this) {
                                            if (liveSocket.isClosed()) break;
                                            sendCastMsg(activeOut, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PONG\"}");
                                            sendCastMsg(activeOut, "sender-0", activeTid, "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PONG\"}");
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

    // --- Native Google TV YouTube App Engine (App 233637DE + MDX Lounge Pairing) ---
    private synchronized boolean castYouTubeToGoogleTv(String ip, String videoId) {
        try {
            // ALWAYS close any active socket/heartbeat thread first so port 8009 is clean!
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
            socket.setSoTimeout(2500);
            socket.startHandshake();

            OutputStream out = socket.getOutputStream();
            InputStream in = socket.getInputStream();

            // 1. Connect and Launch YouTube App 233637DE explicitly
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"LAUNCH\",\"appId\":\"233637DE\",\"requestId\":1}");

            String transportId = null;
            long startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 8000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    String tid = extractTransportIdForApp(text, "233637DE");
                    if (tid != null && !tid.isEmpty()) {
                        transportId = tid;
                        break;
                    }
                } catch (java.net.SocketTimeoutException ste) {
                    try {
                        sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"GET_STATUS\",\"requestId\":2}");
                    } catch (Exception ignored) {}
                }
            }

            if (transportId == null || transportId.isEmpty()) {
                socket.close();
                return false;
            }

            // 2. Connect to transport and request screenId
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.youtube.mdx", "{\"type\":\"getMdxSessionStatus\"}");

            String screenId = null;
            startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 6000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    int idx = text.indexOf("\"screenId\":\"");
                    if (idx != -1) {
                        int endIdx = text.indexOf("\"", idx + 12);
                        if (endIdx != -1) {
                            screenId = text.substring(idx + 12, endIdx);
                            break;
                        }
                    }
                } catch (java.net.SocketTimeoutException ignored) {}
            }

            socket.close();

            if (screenId == null || screenId.isEmpty()) {
                return false;
            }

            // 3. Lounge Token
            URL tokenUrl = new URL("https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch");
            HttpURLConnection conn1 = (HttpURLConnection) tokenUrl.openConnection();
            conn1.setRequestMethod("POST");
            conn1.setDoOutput(true);
            conn1.setConnectTimeout(5000);
            conn1.setReadTimeout(5000);
            conn1.setRequestProperty("Origin", "https://www.youtube.com");
            conn1.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            byte[] postData1 = ("screen_ids=" + URLEncoder.encode(screenId, "UTF-8")).getBytes("UTF-8");
            conn1.getOutputStream().write(postData1);

            BufferedReader br1 = new BufferedReader(new InputStreamReader(conn1.getInputStream(), "UTF-8"));
            StringBuilder sb1 = new StringBuilder();
            String line;
            while ((line = br1.readLine()) != null) sb1.append(line);
            br1.close();

            String tokenResp = sb1.toString();
            int tIdx = tokenResp.indexOf("\"loungeToken\":\"");
            if (tIdx == -1) return false;
            int tEnd = tokenResp.indexOf("\"", tIdx + 15);
            String loungeToken = tokenResp.substring(tIdx + 15, tEnd);

            // 4. Bind Session
            URL bindUrl = new URL("https://www.youtube.com/api/lounge/bc/bind?RID=0&VER=8&CVER=1");
            HttpURLConnection conn2 = (HttpURLConnection) bindUrl.openConnection();
            conn2.setRequestMethod("POST");
            conn2.setDoOutput(true);
            conn2.setConnectTimeout(5000);
            conn2.setReadTimeout(5000);
            conn2.setRequestProperty("Origin", "https://www.youtube.com");
            conn2.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            conn2.setRequestProperty("X-YouTube-LoungeId-Token", loungeToken);
            String bindBody = "device=REMOTE_CONTROL&id=tvhubandroid123456789&name=Android&mdx-version=3&pairing_type=cast&app=android-phone-13.14.55";
            conn2.getOutputStream().write(bindBody.getBytes("UTF-8"));

            BufferedReader br2 = new BufferedReader(new InputStreamReader(conn2.getInputStream(), "UTF-8"));
            StringBuilder sb2 = new StringBuilder();
            while ((line = br2.readLine()) != null) sb2.append(line);
            br2.close();

            String bindResp = sb2.toString();
            int sidIdx = bindResp.indexOf("\"c\",\"");
            if (sidIdx == -1) return false;
            int sidEnd = bindResp.indexOf("\"", sidIdx + 5);
            String sid = bindResp.substring(sidIdx + 5, sidEnd);

            int gIdx = bindResp.indexOf("\"S\",\"");
            if (gIdx == -1) return false;
            int gEnd = bindResp.indexOf("\"", gIdx + 5);
            String gsessionid = bindResp.substring(gIdx + 5, gEnd);

            // 5. Play Video Command
            URL playUrl = new URL("https://www.youtube.com/api/lounge/bc/bind?SID=" + URLEncoder.encode(sid, "UTF-8") + "&gsessionid=" + URLEncoder.encode(gsessionid, "UTF-8") + "&RID=1&VER=8&CVER=1");
            HttpURLConnection conn3 = (HttpURLConnection) playUrl.openConnection();
            conn3.setRequestMethod("POST");
            conn3.setDoOutput(true);
            conn3.setConnectTimeout(5000);
            conn3.setReadTimeout(5000);
            conn3.setRequestProperty("Origin", "https://www.youtube.com");
            conn3.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            conn3.setRequestProperty("X-YouTube-LoungeId-Token", loungeToken);

            String playBody = "req0_videoId=" + URLEncoder.encode(videoId, "UTF-8") +
                              "&req0_currentTime=0&req0_currentIndex=-1&req0_audioOnly=false&req0_listId=&count=1&req0__sc=setPlaylist";
            conn3.getOutputStream().write(playBody.getBytes("UTF-8"));

            int playCode = conn3.getResponseCode();
            if (playCode == 200) {
                lastLoungeToken = loungeToken;
                lastSid = sid;
                lastGsessionId = gsessionid;
                loungeRid = 2;
                lastCastType = "youtube";
                lastCastIp = ip;
                liveTvCurrentTime = 0.0;
                activeCastSocket = socket;
                activeCastOut = out;
                activeCastIp = ip;
                currentTransportId = transportId;

                final SSLSocket liveSocket = socket;
                final String activeTid = transportId;
                final InputStream activeIn = in;
                final OutputStream activeOut = out;
                Thread pingThread = new Thread(new Runnable() {
                    @Override
                    public void run() {
                        long lastPingSent = System.currentTimeMillis();
                        try {
                            while (!Thread.currentThread().isInterrupted() && liveSocket != null && !liveSocket.isClosed()) {
                                long now = System.currentTimeMillis();
                                if (now - lastPingSent >= 4000) {
                                    synchronized (MainActivity.this) {
                                        if (liveSocket.isClosed()) break;
                                        sendCastMsg(activeOut, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PING\"}");
                                        sendCastMsg(activeOut, "sender-0", activeTid, "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PING\"}");
                                    }
                                    lastPingSent = now;
                                }
                                try {
                                    byte[] raw = readCastMsg(activeIn);
                                    if (raw != null) {
                                        String text = new String(raw, "UTF-8");
                                        if (text.contains("\"PING\"")) {
                                            synchronized (MainActivity.this) {
                                                if (liveSocket.isClosed()) break;
                                                sendCastMsg(activeOut, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PONG\"}");
                                                sendCastMsg(activeOut, "sender-0", activeTid, "urn:x-cast:com.google.cast.tp.heartbeat", "{\"type\":\"PONG\"}");
                                            }
                                        }
                                    }
                                } catch (java.net.SocketTimeoutException ste) {
                                } catch (Exception ignored) { break; }
                            }
                        } catch (Exception ignored) {}
                    }
                });
                pingThread.setDaemon(true);
                pingThread.start();
                activeCastHeartbeat = pingThread;
                return true;
            }
            return false;
        } catch (Exception e) {
            return false;
        }
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
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\\') sb.append("\\\\");
            else if (c == '"') sb.append("\\\"");
            else if (c == '\n') sb.append("\\n");
            else if (c == '\r') sb.append("\\r");
            else if (c == '\t') sb.append("\\t");
            else if (c < 32 || c > 126) {
                sb.append(String.format("\\u%04x", (int) c));
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
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
