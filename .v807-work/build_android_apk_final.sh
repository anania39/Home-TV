#!/bin/bash
set -e
echo '=== Building Fully Autonomous TV Hub Android Host App (v8.0.7) ==='

BUILD_DIR=/home/ubuntu/tvhub_apk_build_v807
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
cp /home/ubuntu/tvhub-v8.0.7-stage/static/index.html $BUILD_DIR/assets/index.html
cp /home/ubuntu/tvhub-v8.0.7-stage/static/tv.html $BUILD_DIR/assets/tv.html
mkdir -p $BUILD_DIR/assets/static
mkdir -p $BUILD_DIR/assets/playlists
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/app.js $BUILD_DIR/assets/static/app.js
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/style.css $BUILD_DIR/assets/static/style.css
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/manifest.json $BUILD_DIR/assets/static/manifest.json
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/sw.js $BUILD_DIR/assets/static/sw.js
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/tv.html $BUILD_DIR/assets/static/tv.html
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/endpoint.json $BUILD_DIR/assets/static/endpoint.json
cp -r /home/ubuntu/tvhub-v8.0.7-stage/static/*.png $BUILD_DIR/assets/static/ 2>/dev/null || true
cp -r /home/ubuntu/tvhub-v8.0.7-stage/playlists/* $BUILD_DIR/assets/playlists/ || true

# 2. Generate App Icons (Vibrant Cyan TV Hub Icon)
python3 - << PYEOF
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

with open('/home/ubuntu/tvhub_apk_build_v806/res/mipmap-hdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(72, 72, 14, 165, 233))
with open('/home/ubuntu/tvhub_apk_build_v806/res/mipmap-xhdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(96, 96, 14, 165, 233))
with open('/home/ubuntu/tvhub_apk_build_v806/res/mipmap-xxhdpi/ic_launcher.png', 'wb') as f:
    f.write(make_png(144, 144, 14, 165, 233))
with open('/home/ubuntu/tvhub_apk_build_v806/res/mipmap-xxxhdpi/ic_launcher.png', 'wb') as f:
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
<manifest xmlns:android="http://schemas.android.com/apk/res/android"        package="com.tvhub.app"
    android:versionCode="807"
    android:versionName="8.0.7">

    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    <uses-permission android:name="com.termux.permission.RUN_COMMAND" />

    <queries>
        <package android:name="com.termux" />
    </queries>

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
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
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
import android.net.Uri;
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
    private volatile int activeMediaSessionId = 1;
    private volatile double liveTvCurrentTime = 0.0;
    private volatile double liveTvDuration = 0.0;
    private int castRequestId = 10;
    private volatile String lastCastType = "";
    private volatile String lastCastIp = "192.168.50.205";
    private volatile String lastScreenId = "";
    private volatile String lastStreamUrl = "";
    private volatile String lastStreamTitle = "";
    private volatile String lastStreamType = "LIVE";
    private String lastLoungeToken = null;
    private String lastSid = null;
    private String lastGsessionId = null;
    private int loungeRid = 2;
    private PhoneMediaServer mediaServer = null;
    private static final int REQUEST_PICK_PHONE_VIDEO = 9104;

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

        // Local Wi-Fi host for videos stored on this phone. Casting still uses the native TV bridge.
        mediaServer = new PhoneMediaServer(this);
        mediaServer.start();

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
        settings.setUserAgentString("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 TVHubHostApp/8.0.7");

        // Expose Native TV Hub Android Host Bridge
        webView.addJavascriptInterface(new TVHubBridge(), "TVHubAndroid");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                try {
                    String requestUrl = request.getUrl().toString();
                    if (requestUrl.contains("/static/app.js") || requestUrl.contains("/app.js")) {
                        return new WebResourceResponse("application/javascript", "UTF-8", getAssets().open("app.js"));
                    }
                } catch (Exception ignored) {}
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                view.loadUrl(url);
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                injectPhoneVideoButton();
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                view.postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        view.loadUrl("https://tvhub.92.5.71.162.sslip.io?v=8.0.7");
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

        startPhoneServerOnColdLaunch();
    }

    private String localBackendBase() {
        String ip = PhoneMediaServer.getLanIp();
        if (ip == null || ip.length() == 0 || ip.startsWith("127.")) ip = "127.0.0.1";
        return "http://" + ip + ":8000";
    }

    private boolean isLocalBackendUp(String base) {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(base + "/api/auth/status").openConnection();
            connection.setConnectTimeout(1200);
            connection.setReadTimeout(1500);
            connection.setRequestMethod("GET");
            connection.setUseCaches(false);
            return connection.getResponseCode() == 200;
        } catch (Exception e) {
            return false;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }    private void loadBestHost(final boolean ignored) {
        final String local = localBackendBase();
        new Thread(new Runnable() {
            @Override
            public void run() {
                boolean up = isLocalBackendUp(local);
                if (!up) {
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() { startPhoneServer(); }
                    });
                    long deadline = System.currentTimeMillis() + 26000;
                    while (System.currentTimeMillis() < deadline) {
                        try { Thread.sleep(1200); } catch (Exception ignored) {}
                        if (isLocalBackendUp(local)) {
                            up = true;
                            break;
                        }
                    }
                }
                final boolean ready = up;
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        if (webView == null) return;
                        if (ready) {
                            webView.loadUrl(local + "/?v=8.0.7");
                        } else {
                            Toast.makeText(MainActivity.this, "Phone server did not answer; using the fallback hub.", Toast.LENGTH_LONG).show();
                            webView.loadUrl("https://tvhub.92.5.71.162.sslip.io?v=8.0.7");
                        }
                    }
                });
            }
        }).start();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        loadBestHost(false);
    }

    private void startPhoneServerOnColdLaunch() {
        final String local = localBackendBase();
        new Thread(new Runnable() {
            @Override
            public void run() {
                // If the phone backend is already serving, nothing to do.
            }
        }).start();
    }

    private void showStartupScreen(final String message) {
        mainHandler.post(new Runnable() {
            @Override
            public void run() {
                if (webView == null) return;
                String html = "<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>" +
                    "<style>html,body{margin:0;height:100%;background:#08111d;color:#e2f3ff;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;}" +
                    "body{display:flex;align-items:center;justify-content:center;text-align:center;}" +
                    ".w{max-width:280px}.r{width:42px;height:42px;margin:0 auto 18px;border:4px solid rgba(56,189,248,.2);border-top-color:#38bdf8;border-radius:50%;animation:s 1s linear infinite;}" +
                    "h1{font-size:22px;margin:0 0 8px;letter-spacing:.5px}p{font-size:13px;line-height:1.5;color:#9fc4dc;margin:0}" +
                    "@keyframes s{to{transform:rotate(360deg)}}</style></head><body><div class='w'><div class='r'></div>" +
                    "<h1>TV Hub</h1><p>" + message + "</p></div></body></html>";
                webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null);
            }
        });
    }

    private void startPhoneServer() {
        try {
            Intent intent = new Intent("com.termux.RUN_COMMAND");
            intent.setClassName("com.termux", "com.termux.app.RunCommandService");
            intent.putExtra("com.termux.RUN_COMMAND_PATH", "/data/data/com.termux/files/usr/bin/bash");
            intent.putExtra("com.termux.RUN_COMMAND_ARGUMENTS", new String[]{"/data/data/com.termux/files/home/start_tvhub.sh"});
            intent.putExtra("com.termux.RUN_COMMAND_WORKDIR", "/data/data/com.termux/files/home");
            intent.putExtra("com.termux.RUN_COMMAND_BACKGROUND", true);
            startService(intent);
            Toast.makeText(this, "Starting phone server...", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Phone server could not start automatically.", Toast.LENGTH_LONG).show();
        }
    }

    private void openTermux() {
        try {
            Intent termux = getPackageManager().getLaunchIntentForPackage("com.termux");
            if (termux != null) {
                startActivity(termux);
            } else {
                startActivity(new Intent(Intent.ACTION_VIEW, android.net.Uri.parse("https://f-droid.org/packages/com.termux/")));
            }
        } catch (Exception ignored) {}
    }

    private void showPhoneServerSetup() {
        mainHandler.post(new Runnable() {
            @Override
            public void run() {
                new android.app.AlertDialog.Builder(MainActivity.this)
                    .setTitle("Phone Server")
                    .setMessage("Run the full TV Hub backend on this phone, with no laptop or VPS.\n\nOne-time setup:\n1. Install Termux (F-Droid) and allow external commands in its settings.\n2. Run scripts/install_android.sh once.\n3. Tap Start Phone Server.\n\nThe app loads http://<phone-ip>:8000 and the phone serves channels, YouTube, media uploads and casting.")
                    .setPositiveButton("Start Server", new android.content.DialogInterface.OnClickListener() {
                        public void onClick(android.content.DialogInterface d, int w) { startPhoneServer(); }
                    })
                    .setNeutralButton("Open Termux", new android.content.DialogInterface.OnClickListener() {
                        public void onClick(android.content.DialogInterface d, int w) { openTermux(); }
                    })                    .setNegativeButton("Check Again", new android.content.DialogInterface.OnClickListener() {
                        public void onClick(android.content.DialogInterface d, int w) { loadBestHost(true); }
                    })
                    .show();
            }
        });
    }

    // --- Native Android Host Bridge Exposed to JavaScript ---
    public class TVHubBridge {
        @JavascriptInterface
        public boolean isNativeApp() {
            return true;
        }

        @JavascriptInterface
        public void pickPhoneVideo() {
            mainHandler.post(new Runnable() {
                @Override
                public void run() {
                    try {
                        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                        intent.addCategory(Intent.CATEGORY_OPENABLE);
                        intent.setType("video/*");
                        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                        startActivityForResult(intent, REQUEST_PICK_PHONE_VIDEO);
                    } catch (Exception e) {
                        Toast.makeText(MainActivity.this, "No file picker available", Toast.LENGTH_SHORT).show();
                    }
                }
            });
        }

        @JavascriptInterface
        public String getMediaServerUrl() {
            return mediaServer != null ? mediaServer.getBaseUrl() : "";
        }

        @JavascriptInterface
        public void showMediaServerInfo() {
            final String url = mediaServer != null ? mediaServer.getBaseUrl() : "";
            mainHandler.post(new Runnable() {
                @Override
                public void run() {
                    String message = url.isEmpty() ? "Phone media server is not running" : "Phone video server: " + url;
                    Toast.makeText(MainActivity.this, message, Toast.LENGTH_LONG).show();
                }
            });
        }

        @JavascriptInterface
        public void showPhoneServerSetup() {
            MainActivity.this.showPhoneServerSetup();
        }

        @JavascriptInterface
        public void reloadFromPhoneServer() {                           loadBestHost(true);
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
        }        @JavascriptInterface
        public void castToTv(final String ip, final String devType, final String streamUrl, final String title, final String mimeType, final String youtubeId) {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    if (streamUrl != null && streamUrl.startsWith("/")) {
                        streamUrl = "https://tvhub.92.5.71.162.sslip.io" + streamUrl;
                    }
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
            int lastBrace = text.lastIndexOf('}');
            if (lastBrace == -1 || lastBrace <= brace) return null;
            JSONObject root = new JSONObject(text.substring(brace, lastBrace + 1));
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

        // Quality is sent as {"label":"720p","url":"..."} from the deck.
        // Keep the plain label accepted for older web bundles.
        String qualityLabel = (value != null && !value.isEmpty()) ? value : "Auto";
        String qualityUrl = "";
        if (value != null && value.trim().startsWith("{")) {
            try {
                JSONObject qObj = new JSONObject(value);
                qualityLabel = qObj.optString("label", "Auto");
                qualityUrl = qObj.optString("url", "");
            } catch (Exception ignored) {}
        }

        // Only the native YouTube app uses Lounge. lastScreenId is a cache,
        // never a cast-type flag: it used to route every normal cast to Lounge.
        boolean isYouTube = "youtube".equals(lastCastType);

        // If the last cast was a YouTube session through the Lounge, all controls route
        // through MDX. Normal Google Cast sessions (CC1AD845 receiver for channels,
        // movies, uploads and explicit direct Cast) use the Cast V2 media protocol below.
        if (isYouTube) {
            ensureLoungeSession();
            int reqId = ++castRequestId;
            int sessId = activeMediaSessionId > 0 ? activeMediaSessionId : 1;
            try {

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
                Map<String, String> p1 = new HashMap<>();
                p1.put("playbackRate", value);
                sendLoungeCommand("setPlaybackRate", p1);

                Map<String, String> p2 = new HashMap<>();
                p2.put("playbackSpeed", value);
                sendLoungeCommand("setPlaybackSpeed", p2);

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
                    notifyUser("📍 Jumped to " + timeStr + " on TV");
                }
                liveTvCurrentTime = sec;
                String sVal = String.valueOf(Math.max(0, sec));

                Map<String, String> p = new HashMap<>();
                p.put("newTime", sVal);
                sendLoungeCommand("seekTo", p);
            } else if ("subtitles".equals(action)) {
                if ("off".equalsIgnoreCase(value) || "0".equals(value)) {
                    Map<String, String> p = new HashMap<>();
                    p.put("req0_hasSubtitles", "false");
                    sendLoungeCommand("setSubtitleTrack", p);
                    notifyUser("💬 Subtitles: Off");
                } else {
                    Map<String, String> p = new HashMap<>();
                    p.put("req0_trackName", value);
                    p.put("req0_hasSubtitles", "true");
                    sendLoungeCommand("setSubtitleTrack", p);
                    notifyUser("💬 Subtitles: " + value);
                }
            } else if ("quality".equals(action)) {
                String qParam = "auto";
                if ("1080p".equalsIgnoreCase(qualityLabel)) qParam = "hd1080";
                else if ("720p".equalsIgnoreCase(qualityLabel)) qParam = "hd720";
                else if ("480p".equalsIgnoreCase(qualityLabel)) qParam = "large";
                else if ("360p".equalsIgnoreCase(qualityLabel)) qParam = "medium";
                else if ("240p".equalsIgnoreCase(qualityLabel)) qParam = "small";
                Map<String, String> p = new HashMap<>();
                p.put("req0_playbackQuality", qParam);
                sendLoungeCommand("setPlaybackQuality", p);
                notifyUser("📺 Quality: " + qualityLabel);
            }
            } catch (Exception ignored) {}
            return;
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
                        int mins = (int) (targetSec / 60);
                        int remSecs = (int) (targetSec % 60);
                        notifyUser("⏩ Jumped to " + String.format("%02d:%02d", mins, remSecs) + " on TV");
                    }
                    liveTvCurrentTime = targetSec;
                    msgJson = "{\"type\":\"SEEK\",\"currentTime\":" + targetSec + ",\"resumeState\":\"PLAYBACK_START\",\"mediaSessionId\":" + sessId + ",\"requestId\":" + reqId + "}";
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
                    reloadActiveCastQuality(qualityLabel, qualityUrl);
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
        if (!"dlna".equals(lastCastType)) {
            sendCastDirectControl(action, value);
        }
        // 3. DLNA Control for Hisense TV
        if ("dlna".equals(lastCastType) || (lastCastIp != null && (lastCastIp.endsWith(".249") || lastCastIp.contains("hisense")))) {
            String controlUrl = "http://" + lastCastIp + ":38400/upnp/control/mingusavtr";
            if ("play".equals(action)) {
                String playSpeed = (value != null && !value.isEmpty()) ? value : "1";
                sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Play", "<InstanceID>0</InstanceID><Speed>" + playSpeed + "</Speed>");
            } else if ("pause".equals(action)) {
                sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Pause", "<InstanceID>0</InstanceID>");
            } else if ("stop".equals(action)) {
                sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Stop", "<InstanceID>0</InstanceID>");
            } else if ("seek".equals(action) || "seek_relative".equals(action)) {
                double targetSec = 0.0;
                try {
                    if ("seek_relative".equals(action) || (value != null && (value.startsWith("+") || value.startsWith("-")))) {
                        targetSec = Math.max(0.0, liveTvCurrentTime + Double.parseDouble(value));
                    } else {
                        targetSec = Math.max(0.0, Double.parseDouble(value));
                    }
                    liveTvCurrentTime = targetSec;
                    sendDlnaSeek(controlUrl, targetSec);
                } catch (Exception ignored) {}
            } else if ("speed".equals(action) || "rate".equals(action)) {
                if (value != null && !value.isEmpty()) {
                    sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Play", "<InstanceID>0</InstanceID><Speed>" + value + "</Speed>");
                }
            } else if ("quality".equals(action)) {
                String newUrl = (qualityUrl != null && !qualityUrl.isEmpty()) ? qualityUrl : buildQualityUrl(lastStreamUrl, qualityLabel);
                if (newUrl != null && !newUrl.isEmpty() && !newUrl.equals(lastStreamUrl)) {
                    double resumeAt = liveTvCurrentTime;
                    if (sendDlnaCast(lastCastIp, controlUrl, newUrl, lastStreamTitle)) {
                        if (resumeAt > 1.0) sendDlnaSeek(controlUrl, resumeAt);
                        notifyUser("📺 Quality: " + qualityLabel);
                    }
                }
            }
        }
    }

    private synchronized void reloadActiveCastQuality(String label, String url) {
        if (activeCastOut == null || currentTransportId == null) {
            notifyUser("⚠️ Quality change needs an active Cast session");
            return;
        }
        String newUrl = (url != null && !url.isEmpty()) ? url : buildQualityUrl(lastStreamUrl, label);
        if (newUrl == null || newUrl.isEmpty()) {
            notifyUser("⚠️ No quality URL for this stream");
            return;
        }
        if (newUrl.equals(lastStreamUrl)) {
            notifyUser("⚠️ This stream has no separate quality variants");
            return;
        }
        double resumeAt = liveTvCurrentTime;
        int oldSession = activeMediaSessionId;
        try {
            boolean isHls = newUrl.contains(".m3u8") || newUrl.contains("/proxy?url=");
            String mime = isHls ? "application/x-mpegurl" : "video/mp4";
            String streamType = "BUFFERED".equals(lastStreamType) ? "BUFFERED" : "LIVE";
            String loadJson = "{\"type\":\"LOAD\",\"requestId\":" + (++castRequestId) +
                    ",\"autoplay\":true,\"media\":{\"contentId\":\"" + escapeJson(newUrl) +
                    "\",\"streamType\":\"" + streamType + "\",\"contentType\":\"" + mime +
                    "\",\"metadata\":{\"metadataType\":0,\"title\":\"" + escapeJson(lastStreamTitle) + "\"} } }";
            synchronized (MainActivity.this) {
                sendCastMsg(activeCastOut, "sender-0", currentTransportId, "urn:x-cast:com.google.cast.media", loadJson);
            }
            long waitStart = System.currentTimeMillis();
            while (System.currentTimeMillis() - waitStart < 2500) {
                if (activeMediaSessionId != oldSession) break;
                try { Thread.sleep(100); } catch (Exception ignored) {}
            }
            if ("BUFFERED".equals(lastStreamType) && resumeAt > 1.0) {
                int sessId = activeMediaSessionId > 0 ? activeMediaSessionId : 1;
                String seekJson = "{\"type\":\"SEEK\",\"currentTime\":" + resumeAt +
                        ",\"resumeState\":\"PLAYBACK_START\",\"mediaSessionId\":" + sessId +
                        ",\"requestId\":" + (++castRequestId) + "}";
                synchronized (MainActivity.this) {
                    sendCastMsg(activeCastOut, "sender-0", currentTransportId, "urn:x-cast:com.google.cast.media", seekJson);
                }
            }
            lastStreamUrl = newUrl;
            notifyUser("📺 Quality: " + label);
        } catch (Exception e) {
            notifyUser("⚠️ Quality change failed");
        }
    }

    private String buildQualityUrl(String base, String label) {
        if (base == null || base.isEmpty()) return null;
        String clean = base.replaceAll("([?&])(q|quality)=[^&]*&?", "$1");
        clean = clean.replaceAll("[?&]$", "");
        if (!clean.contains("/proxy?url=") && !clean.contains("/api/stream/proxy?url=")) {
            return clean;
        }
        String sep = clean.contains("?") ? "&" : "?";
        try {
            return clean + sep + "q=" + URLEncoder.encode(label, "UTF-8");
        } catch (Exception e) {
            return clean + sep + "q=" + label;
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
                        String key = entry.getKey();
                        if (!key.startsWith("req0_")) {
                            key = "req0_" + key;
                        }
                        sb.append("&").append(URLEncoder.encode(key, "UTF-8")).append("=").append(URLEncoder.encode(entry.getValue(), "UTF-8"));
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
            String screenId = lastScreenId;
            if (screenId == null || screenId.isEmpty()) {
                screenId = "15e75b8ac2df0509ef8b499fc78eef3d76ae913654fb8c32a282ec6793ab2c33";
                lastScreenId = screenId;
            }

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
            loungeRid = 1;
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
                    String tidFound = extractTransportIdForApp(text, "CC1AD845");
                    if (tidFound != null && !tidFound.isEmpty()) {
                        tid = tidFound;
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
                    notifyUser("⚠️ Quality change requires an active Cast session");
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
        lastStreamUrl = (streamUrl != null) ? streamUrl : "";
        lastStreamTitle = (title != null) ? title : "Video";
        String type = (devType != null) ? devType.toLowerCase() : "";

        // Normalize loopback URLs to the chosen host so cast/controls never carry the wrong authority.
        if (streamUrl != null) {
            String low = streamUrl.toLowerCase();
            if (low.contains("https://tvhub.92.5.71.162.sslip.io") || low.contains("https://home.tvhub.one")) {
                String u = streamUrl;
                u = u.replace("https://tvhub.92.5.71.162.sslip.io", "http://" + targetIp);
                u = u.replace("https://home.tvhub.one", "http://" + targetIp);
                streamUrl = u;
            }
        }
        // YouTube: let the TV fetch googlevideo from Google, but do it through our own Cast path so
        // playback controls, speed and subtitles actually work (the TV YouTube app would ignore them).        if (youtubeId == null || youtubeId.isEmpty()) {
            if (streamUrl != null) {
                String low = streamUrl.toLowerCase();
                if (low.contains("youtube.com") || low.contains("youtu.be") || low.contains("googlevideo.com")) {
                    java.util.regex.Pattern pt = java.util.regex.Pattern.compile("(?:youtu\\\\.be\\\\/|youtube\\\\.com\\\\/(?:embed\\\\/|v\\\\/|watch\\\\?v=|shorts\\\\/|live\\\\/)|docid=|video_id=)([a-zA-Z0-9_-]{11})");
                    java.util.regex.Matcher mt = pt.matcher(streamUrl);
                    if (mt.find()) {
                        youtubeId = mt.group(1);
                    }
                }
            }
        }

        // 1. Wake TV from standby via direct local UDP magic packet
        sendWakeOnLanPacket();

        // 2. YouTube on TCL/Google TV: do NOT launch the TV YouTube app — use our own Cast media
        // receiver path so playback controls, playback rate and subtitles actually work.
        if ((youtubeId != null && !youtubeId.isEmpty()) && (type.contains("google_tv") || targetIp.endsWith(".205") || targetIp.endsWith(".3") || targetIp.endsWith(".249") || targetIp.endsWith(".139") || targetIp.endsWith(".249"))) {
            if (streamUrl != null && (streamUrl.contains("/proxy?url=") || streamUrl.contains("/api/stream/proxy?url="))) {
                notifyUser("Playing YouTube on TV via Cast media receiver...");
                boolean ok = castToGoogleTv(targetIp, streamUrl, title);
                if (ok) {
                    notifyUser("Now Playing " + title + " on TV (via Cast media receiver)");
                } else {
                    notifyUser("TV did not acknowledge the Cast stream. Retrying...");
                    try { Thread.sleep(600); } catch (Exception ignored) {}
                    ok = castToGoogleTv(targetIp, streamUrl, title);
                }
                if (ok) {
                    notifyUser("Now Playing " + title + " on TV (via Cast media receiver)");
                } else {
                    notifyUser("Could not start YouTube casting on the TV. Launch the native app instead.");
                }
                return;
            }
        }

        // 2. Google Cast Protocol for TCL Smart TV Pro (192.168.50.205:8009) & Google TVs
        if (type.contains("google_tv") || targetIp.endsWith(".205") || targetIp.endsWith(".3")) {
            if (youtubeId != null && !youtubeId.isEmpty() && (streamUrl == null || (!streamUrl.contains("/proxy?url=") && !streamUrl.contains("/api/stream/proxy?url=")))) {
                notifyUser("Launching YouTube on TCL Smart TV Pro...");
                boolean ytOk = castYouTubeToGoogleTv(targetIp, youtubeId);
                if (!ytOk) {
                    try { Thread.sleep(600); } catch (Exception ignored) {}
                    ytOk = castYouTubeToGoogleTv(targetIp, youtubeId);
                }
                if (ytOk) {
                    notifyUser("🎉 Now Playing YouTube on TCL Smart TV Pro!");
                } else {
                    notifyUser("⚠️ Launching YouTube on TV, please wait a moment...");
                }
                return; // Strictly NEVER fall through to castToGoogleTv for YouTube!
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
            boolean dlnaOk = sendDlnaCast(targetIp, controlUrl, streamUrl, title);
            if (dlnaOk) {
                notifyUser("🎉 Now Playing " + title + " on Hisense TV!");
                return;
            }
        }

        // 5. Universal Fallback: Try Cast V2 on 8009 then DLNA on 38400
        if (youtubeId != null && !youtubeId.isEmpty()) {
            if (castYouTubeToGoogleTv(targetIp, youtubeId)) {
                notifyUser("Playing YouTube on Smart TV!");
            } else {
                notifyUser("Launching YouTube on TV, please wait a moment...");
            }
        } else {
            boolean castFallback = castToGoogleTv(targetIp, streamUrl, title);
            if (castFallback) {
                notifyUser("Playing " + title + " on Smart TV!");
            } else {
                boolean dlnaFallback = sendDlnaCast(targetIp, "http://" + targetIp + ":38400/upnp/control/mingusavtr", streamUrl, title);
                if (dlnaFallback) {
                    notifyUser("Playing " + title + " on TV!");
                } else {
                    notifyUser("Power signal sent to TV. If TV is off, please turn it on.");
                }
            }
        }
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
    private boolean isHlsStreamUrl(String url) {
        if (url == null) return false;
        if (url.contains(".m3u8")) return true;
        if (url.contains("/proxy?url=") || url.contains("/api/stream/proxy?url=")) {
            int idx = url.indexOf("url=");
            if (idx >= 0) {
                int end = url.indexOf('&', idx);
                if (end < 0) end = url.length();
                String raw = url.substring(idx + 4, end);
                try { raw = java.net.URLDecoder.decode(raw, "UTF-8"); } catch (Exception ignored) {}
                if (raw != null) {
                    String low = raw.toLowerCase();
                    if (low.contains(".m3u8") || "mpegurl".equals(low)) return true;
                    String ext = raw.endsWith(".ts") || raw.endsWith(".ts?") || raw.startsWith("http") ? "ts" : null;
                    if (ext == null) {
                        int dot = raw.lastIndexOf('.');
                        if (dot > raw.lastIndexOf('/') && dot >= 0) ext = raw.substring(dot + 1).toLowerCase();
                    } else { ext = "ts"; }
                    if ("mp4" .equals(ext) || "webm".equals(ext) || "mov".equals(ext) || "mpeg4".equals(ext)) return false;
                    if (low.contains("file.m3u8") && !raw.contains("?")) return false;
                }
            }
            return false;
        }
        return false;
    }

    private String itemIdleReason(String text) {
        if (text == null) return null;
        int brace = text.indexOf('{');
        if (brace < 0) return null;
        try {
            JSONObject root = new JSONObject(text.substring(brace));
            JSONArray arr = root.optJSONArray("status");
            if (arr != null && arr.length() > 0) {
                JSONObject item = arr.getJSONObject(0);
                String idle = item.optString("idleReason");
                if (idle != null && idle.length() > 0) return idle;
            }
        } catch (Exception ignored) {}
        return null;
    }

    private synchronized boolean castToGoogleTv(String ip, String streamUrl, String title) {
        try {
            closeActiveCast();
            lastLoungeToken = null;
            lastSid = null;
            lastGsessionId = null;
            lastScreenId = "";

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
            boolean isHls = isHlsStreamUrl(streamUrl);
            String mime = isHls ? "application/x-mpegurl" : "video/mp4";
            boolean isVod = streamUrl.contains("movie") || streamUrl.contains("videodb") || streamUrl.contains(".mp4") || (streamUrl.contains("googlevideo") && !streamUrl.contains("live"));
            String streamType = isVod ? "BUFFERED" : "LIVE";
            String loadJson = "{\"type\":\"LOAD\",\"requestId\":3,\"autoplay\":true,\"media\":{\"contentId\":\"" + escapeJson(streamUrl) + "\",\"streamType\":\"" + streamType + "\",\"contentType\":\"" + mime + "\",\"metadata\":{\"metadataType\":0,\"title\":\"" + escapeJson(title) + "\"} } }";
            sendCastMsg(out, "sender-0", transportId, "urn:x-cast:com.google.cast.media", loadJson);
            activeMediaSessionId = 1;
            lastStreamUrl = streamUrl;
            lastStreamTitle = title;
            lastStreamType = streamType;

            // Wait up to 6s to capture the real mediaStatus from the TV (idle -> playing).
            long waitSt = System.currentTimeMillis();
            int lastSession = 0;
            boolean sawStatus = false;
            while (System.currentTimeMillis() - waitSt < 6000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) break;
                    String text = new String(raw, "UTF-8");
                    MediaStatusInfo st = parseMediaStatus(text);
                    if (st != null) {
                        sawStatus = true;
                        lastSession = st.mediaSessionId;
                        liveTvCurrentTime = st.currentTime;
                        if (st.duration > 0) liveTvDuration = st.duration;
                        if (st.mediaSessionId > 0) {
                            activeMediaSessionId = st.mediaSessionId;
                        }
                        if ("PLAYING".equals(st.playerState) || "BUFFERING".equals(st.playerState)) {
                            break;
                        }
                        if ("IDLE".equals(st.playerState)) {
                            String idle = itemIdleReason(text);
                            if (idle != null && ("ERROR".equals(idle) || "INTERRUPTED".equals(idle) || "CANCELLED".equals(idle))) {
                                notifyUser("⚠️ TV ignored the stream (" + idle + ")");
                                closeActiveCast();
                                return false;
                            }
                        }
                    }
                } catch (Exception ignored) { break; }
            }
            if (activeMediaSessionId <= 0 && !sawStatus) {
                notifyUser("⚠️ TV did not reply with a media session; retrying...");
                closeActiveCast();
                return false;
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
            socket.setSoTimeout(5000);
            socket.startHandshake();

            OutputStream out = socket.getOutputStream();
            InputStream in = socket.getInputStream();

            // 1. Connect and Launch YouTube App 233637DE explicitly
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.tp.connection", "{\"type\":\"CONNECT\"}");
            sendCastMsg(out, "sender-0", "receiver-0", "urn:x-cast:com.google.cast.receiver", "{\"type\":\"LAUNCH\",\"appId\":\"233637DE\",\"requestId\":1}");

            String transportId = null;
            long startWait = System.currentTimeMillis();
            while (System.currentTimeMillis() - startWait < 9000) {
                try {
                    byte[] raw = readCastMsg(in);
                    if (raw == null) {
                        try { Thread.sleep(200); } catch (Exception ignored) {}
                        continue;
                    }
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
                            lastScreenId = screenId;
                            break;
                        }
                    }
                } catch (java.net.SocketTimeoutException ignored) {}
            }

            if (screenId == null || screenId.isEmpty()) {
                screenId = (lastScreenId != null && !lastScreenId.isEmpty()) ? lastScreenId : "15e75b8ac2df0509ef8b499fc78eef3d76ae913654fb8c32a282ec6793ab2c33";
                lastScreenId = screenId;
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

            String playBody = "count=1&req0__sc=setPlaylist&req0_videoId=" + URLEncoder.encode(videoId, "UTF-8") +
                              "&req0_currentTime=0&req0_currentIndex=-1&req0_audioOnly=false&req0_listId=";
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
                        long lastStatusSent = 0;
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
                                        MediaStatusInfo info = parseMediaStatus(text);
                                        if (info != null) {
                                            if (info.mediaSessionId > 0) activeMediaSessionId = info.mediaSessionId;
                                            if (info.currentTime >= 0) liveTvCurrentTime = info.currentTime;
                                            if (info.duration > 0) liveTvDuration = info.duration;
                                            final double cTime = liveTvCurrentTime;
                                            final double dTime = liveTvDuration;
                                            final String pState = info.playerState;
                                            runOnUiThread(new Runnable() {
                                                @Override
                                                public void run() {
                                                    if (webView != null) {
                                                        webView.evaluateJavascript("if (window.syncNativePlaybackState) window.syncNativePlaybackState(" + cTime + ", " + dTime + ", '" + pState + "');", null);
                                                    }
                                                }
                                            });
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
    private void sendDlnaSeek(String controlUrl, double seconds) {
        int total = (int) Math.max(0, seconds);
        String time = String.format("%02d:%02d:%02d", total / 3600, (total % 3600) / 60, total % 60);
        sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Seek",
                "<InstanceID>0</InstanceID><Unit>REL_TIME</Unit><Target>" + time + "</Target>");
    }

    private boolean sendDlnaCast(String ip, String controlUrl, String mediaUrl, String title) {
        try {
            boolean isHls = mediaUrl.contains(".m3u8") || mediaUrl.contains("/proxy?url=");
            boolean isVod = mediaUrl.contains("movie") || mediaUrl.contains("videodb") || mediaUrl.contains(".mp4") || mediaUrl.contains("googlevideo");
            String proto = isHls ? "http-get:*:application/x-mpegurl:DLNA.ORG_OP=00;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000" : "http-get:*:video/mp4:*";
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
            boolean played = sendSoap(controlUrl, "urn:schemas-upnp-org:service:AVTransport:1", "Play", playBody);
            if (played) {
                lastCastType = "dlna";
                lastCastIp = ip;
                lastStreamUrl = mediaUrl;
                lastStreamTitle = title;
                lastStreamType = isVod ? "BUFFERED" : "LIVE";
                liveTvCurrentTime = 0.0;
            }
            return played;
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

    private void injectPhoneVideoButton() {
        if (webView == null) return;
        String js =
            "(function(){" +
            "if(window.__tvhubPhoneButton)return;" +
            "window.onTVHubPhoneVideoPicked=function(url,name,mime){" +
            "try{" +
            "var target=(typeof resolveSelectedTarget==='function'&&typeof state!=='undefined')?resolveSelectedTarget(state.currentTvId):{ip:'192.168.50.205',dev_type:'google_tv',name:'Smart TV'};" +
            "window.TVHubAndroid.castToTv(target.ip,target.dev_type,url,name,mime||'video/mp4','');" +
            "if(typeof state!=='undefined'){state.currentTitle=name;state.playbackState='PLAYING';state.playbackType='video';}" +
            "var t=document.getElementById('bar-title');if(t)t.textContent=name;" +
            "if(typeof showToast==='function')showToast('Casting phone video: '+name+' to '+target.name);" +
            "}catch(e){if(window.TVHubAndroid)TVHubAndroid.toast('Could not cast: '+e);}" +
            "};" +
            "var b=document.createElement('button');" +
            "b.id='tvhub-phone-video-btn';" +
            "b.textContent='\ud83d\udcf1 Phone Video';" +
            "b.title='Cast a video stored on this phone to the selected TV';" +
            "b.style.cssText='position:fixed;right:14px;bottom:86px;z-index:2147483647;border:1px solid rgba(56,189,248,.65);background:rgba(8,20,35,.94);color:#e0f2fe;border-radius:999px;padding:10px 14px;font:600 12px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.45);';" +
            "b.onclick=function(){if(window.TVHubAndroid)TVHubAndroid.pickPhoneVideo();};" +
            "b.oncontextmenu=function(e){e.preventDefault();if(window.TVHubAndroid)TVHubAndroid.showMediaServerInfo();return false;};" +
            "document.body.appendChild(b);window.__tvhubPhoneButton=b;" +
            "var s=document.createElement('div');" +
            "s.id='tvhub-phone-server-status';" +
            "s.style.cssText='position:fixed;right:14px;top:8px;z-index:2147483647;background:rgba(8,20,35,.6);border:1px solid rgba(74,222,128,.5);border-radius:999px;padding:2px 10px;font:500 11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;color:#dcfce7;backdrop-filter:blur(8px);';" +
            "s.innerHTML='&#9679; Phone Server';" +
            "document.body.appendChild(s);" +
            "var t=document.getElementById('bar-title');if(t){" +
            "var up=t.textContent.indexOf('Setanta')!==-1||t.textContent.indexOf('playing')!==-1;" +
            "s.style.display=up?'none':'block';" +
            "movie.addEventListener ? d.addEventListener('play',function(){s.style.display='none'}) : null;" +
            "}" +
            "})();";
        webView.evaluateJavascript(js, null);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_PICK_PHONE_VIDEO || resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        Uri uri = data.getData();
        try {
            getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (Exception ignored) {}
        final PhoneMediaServer.MediaEntry entry = mediaServer != null ? mediaServer.add(uri) : null;
        if (entry == null) {
            Toast.makeText(this, "Could not open that video", Toast.LENGTH_SHORT).show();
            return;
        }
        final String mediaUrl = mediaServer.getUrl(entry.id);
        webView.post(new Runnable() {
            @Override
            public void run() {
                String js = "if(typeof window.onTVHubPhoneVideoPicked==='function'){window.onTVHubPhoneVideoPicked(\"" + escapeJson(mediaUrl) + "\",\"" + escapeJson(entry.name) + "\",\"" + escapeJson(entry.mime) + "\");}else{TVHubAndroid.toast('Picked a video');}";
                webView.evaluateJavascript(js, null);
            }
        });
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
        if (mediaServer != null) {
            mediaServer.stop();
        }
        closeActiveCast();
        if (multicastLock != null && multicastLock.isHeld()) {
            multicastLock.release();
        }
    }
}
JAVA

# 5b. Local phone-media HTTP host. Serves user-picked videos to TVs on the same Wi-Fi.
cat << 'MEDIA_SERVER_JAVA' > $BUILD_DIR/src/com/tvhub/app/PhoneMediaServer.java
package com.tvhub.app;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import android.util.Log;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.channels.FileChannel;
import java.util.Enumeration;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Tiny HTTP host for videos stored on the phone. It intentionally does not proxy IPTV or
 * run the Python backend: the native Cast/DLNA bridge handles playback, while this server
 * gives the TV a LAN URL with byte-range support for local files.
 */
public class PhoneMediaServer {
    private static final String TAG = "TVHubMediaServer";
    private final Context context;
    private final Map<String, MediaEntry> entries = new ConcurrentHashMap<String, MediaEntry>();
    private ServerSocket serverSocket;
    private Thread acceptThread;
    private volatile boolean running = false;
    private int port = 0;

    public PhoneMediaServer(Context context) {
        this.context = context.getApplicationContext();
    }

    public synchronized void start() {
        if (running) return;
        for (int candidate = 8080; candidate <= 8090; candidate++) {
            ServerSocket candidateSocket = null;
            try {
                candidateSocket = new ServerSocket();
                candidateSocket.setReuseAddress(true);
                candidateSocket.bind(new InetSocketAddress("0.0.0.0", candidate));
                serverSocket = candidateSocket;
                port = candidate;
                running = true;
                acceptThread = new Thread(new Runnable() {
                    @Override
                    public void run() {
                        acceptLoop();
                    }
                }, "TVHubMediaAccept");
                acceptThread.setDaemon(true);
                acceptThread.start();
                Log.i(TAG, "Phone media server listening on " + getBaseUrl());
                return;
            } catch (Exception e) {
                try {
                    if (candidateSocket != null) candidateSocket.close();
                } catch (Exception ignored) {}
                Log.w(TAG, "Port " + candidate + " unavailable: " + e.getMessage());
            }
        }
        Log.e(TAG, "Could not start phone media server");
    }

    public synchronized void stop() {
        running = false;
        try {
            if (serverSocket != null) serverSocket.close();
        } catch (Exception ignored) {}
        serverSocket = null;
        if (acceptThread != null) {
            acceptThread.interrupt();
            acceptThread = null;
        }
        entries.clear();
    }

    public int getPort() {
        return port;
    }

    public String getBaseUrl() {
        if (port <= 0) return "";
        return "http://" + getLanIp() + ":" + port;
    }

    public String getUrl(String id) {
        return getBaseUrl() + "/media/" + id;
    }

    public static String getLanIp() {
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            String fallback = null;
            while (interfaces != null && interfaces.hasMoreElements()) {
                NetworkInterface network = interfaces.nextElement();
                if (!network.isUp() || network.isLoopback()) continue;
                String name = network.getName() == null ? "" : network.getName().toLowerCase(Locale.US);
                Enumeration<InetAddress> addresses = network.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    InetAddress address = addresses.nextElement();
                    if (!(address instanceof Inet4Address) || address.isLoopbackAddress()) continue;
                    String ip = address.getHostAddress();
                    if (ip == null || ip.startsWith("169.254.")) continue;
                    if (name.startsWith("wlan") || name.startsWith("ap") || name.startsWith("eth")) {
                        return ip;
                    }
                    if (fallback == null) fallback = ip;
                }
            }
            if (fallback != null) return fallback;
        } catch (Exception ignored) {}
        return "127.0.0.1";
    }

    public MediaEntry add(Uri uri) {
        if (uri == null) return null;
        String name = "Phone video";
        long size = 0;
        String mime = "video/mp4";
        try {
            ContentResolver resolver = context.getContentResolver();
            Cursor cursor = resolver.query(uri,
                    new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE},
                    null, null, null);
            if (cursor != null) {
                try {
                    if (cursor.moveToFirst()) {
                        int nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                        int sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE);
                        if (nameIndex >= 0 && !cursor.isNull(nameIndex)) name = cursor.getString(nameIndex);
                        if (sizeIndex >= 0 && !cursor.isNull(sizeIndex)) size = cursor.getLong(sizeIndex);
                    }
                } finally {
                    cursor.close();
                }
            }
            String type = resolver.getType(uri);
            if (type != null && type.startsWith("video/")) mime = type;
            if (size <= 0) {
                ParcelFileDescriptor descriptor = resolver.openFileDescriptor(uri, "r");
                if (descriptor != null) {
                    try {
                        size = descriptor.getStatSize();
                    } finally {
                        descriptor.close();
                    }
                }
            }
        } catch (Exception e) {
            Log.w(TAG, "Could not read video metadata", e);
        }
        String id = "v" + Long.toHexString(System.currentTimeMillis()) + Integer.toHexString(uri.toString().hashCode());
        MediaEntry entry = new MediaEntry(id, uri, name, size, mime);
        entries.put(id, entry);
        Log.i(TAG, "Shared " + name + " as " + getUrl(id));
        return entry;
    }

    private void acceptLoop() {
        while (running && serverSocket != null && !serverSocket.isClosed()) {
            Socket socket = null;
            try {
                socket = serverSocket.accept();
                socket.setSoTimeout(15000);
                final Socket client = socket;
                Thread worker = new Thread(new Runnable() {
                    @Override
                    public void run() {
                        handle(client);
                    }
                }, "TVHubMediaClient");
                worker.setDaemon(true);
                worker.start();
            } catch (Exception e) {
                if (running) Log.w(TAG, "Accept failed: " + e.getMessage());
                try {
                    if (socket != null) socket.close();
                } catch (Exception ignored) {}
            }
        }
    }

    private void handle(Socket socket) {
        OutputStream out = null;
        try {
            InputStream in = socket.getInputStream();
            String requestLine = readLine(in);
            if (requestLine == null) return;
            String[] parts = requestLine.split(" ");
            if (parts.length < 2) return;
            String method = parts[0].toUpperCase(Locale.US);
            String target = parts[1];
            String rangeHeader = null;
            String line;
            while ((line = readLine(in)) != null && line.length() > 0) {
                int colon = line.indexOf(':');
                if (colon <= 0) continue;
                String key = line.substring(0, colon).trim().toLowerCase(Locale.US);
                if ("range".equals(key)) rangeHeader = line.substring(colon + 1).trim();
            }
            out = socket.getOutputStream();
            if ("OPTIONS".equals(method)) {
                writeSimple(out, 204, "No Content", "text/plain", "", true);
                return;
            }
            if (!"GET".equals(method) && !"HEAD".equals(method)) {
                writeSimple(out, 405, "Method Not Allowed", "text/plain", "Method not allowed", false);
                return;
            }
            String path = target;
            int query = path.indexOf('?');
            if (query >= 0) path = path.substring(0, query);
            if ("/".equals(path) || "/index.html".equals(path)) {
                serveList(out, "HEAD".equals(method));
                return;
            }
            if ("/health".equals(path)) {
                writeSimple(out, 200, "OK", "text/plain", "ok", "HEAD".equals(method));
                return;
            }
            if (path.startsWith("/media/")) {
                serveMedia(out, method, path.substring(7), rangeHeader);
                return;
            }
            writeSimple(out, 404, "Not Found", "text/plain", "Not found", "HEAD".equals(method));
        } catch (Exception e) {
            Log.w(TAG, "Request failed: " + e.getMessage());
        } finally {
            try {
                if (out != null) out.flush();
            } catch (Exception ignored) {}
            try {
                socket.close();
            } catch (Exception ignored) {}
        }
    }

    private void serveList(OutputStream out, boolean head) throws IOException {
        StringBuilder html = new StringBuilder();
        html.append("<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>");
        html.append("<title>TV Hub Phone Media</title></head><body style='font-family:sans-serif;background:#0b0f19;color:#e2e8f0;padding:24px'>");
        html.append("<h1>TV Hub Phone Media</h1><p>Videos shared from this phone. Keep the TV Hub app open.</p><ul>");
        for (MediaEntry entry : entries.values()) {
            html.append("<li style='margin:10px 0'><a style='color:#38bdf8' href='/media/").append(entry.id).append("'>");
            html.append(escapeHtml(entry.name)).append("</a> <small>").append(Math.max(0, entry.size / (1024 * 1024))).append(" MB</small></li>");
        }
        if (entries.isEmpty()) html.append("<li>No videos picked yet.</li>");
        html.append("</ul></body></html>");
        writeSimple(out, 200, "OK", "text/html; charset=utf-8", html.toString(), head);
    }

    private void serveMedia(OutputStream out, String method, String id, String rangeHeader) throws IOException {
        MediaEntry entry = entries.get(id);
        if (entry == null) {
            writeSimple(out, 404, "Not Found", "text/plain", "Unknown video", "HEAD".equals(method));
            return;
        }
        ParcelFileDescriptor descriptor = null;
        FileInputStream stream = null;
        try {
            descriptor = context.getContentResolver().openFileDescriptor(entry.uri, "r");
            if (descriptor == null) {
                writeSimple(out, 404, "Not Found", "text/plain", "Video unavailable", "HEAD".equals(method));
                return;
            }
            stream = new FileInputStream(descriptor.getFileDescriptor());
            FileChannel channel = stream.getChannel();
            long size = channel.size();
            if (size <= 0) size = entry.size;
            if (size <= 0) {
                writeSimple(out, 416, "Range Not Satisfiable", "text/plain", "Video size unavailable", "HEAD".equals(method));
                return;
            }

            long start = 0;
            long end = size - 1;
            boolean partial = false;
            if (rangeHeader != null && rangeHeader.toLowerCase(Locale.US).startsWith("bytes=")) {
                String spec = rangeHeader.substring(6).trim();
                int comma = spec.indexOf(',');
                if (comma >= 0) spec = spec.substring(0, comma);
                int dash = spec.indexOf('-');
                if (dash < 0) {
                    writeRangeError(out, size);
                    return;
                }
                try {
                    String startText = spec.substring(0, dash).trim();
                    String endText = spec.substring(dash + 1).trim();
                    if (startText.length() == 0) {
                        long suffix = Long.parseLong(endText);
                        start = Math.max(0, size - suffix);
                    } else {
                        start = Long.parseLong(startText);
                    }
                    end = endText.length() == 0 ? size - 1 : Long.parseLong(endText);
                    if (start < 0) start = 0;
                    if (end >= size) end = size - 1;
                    if (start >= size || start > end) {
                        writeRangeError(out, size);
                        return;
                    }
                    partial = true;
                } catch (NumberFormatException e) {
                    writeRangeError(out, size);
                    return;
                }
            }

            long length = end - start + 1;
            StringBuilder headers = new StringBuilder();
            headers.append("HTTP/1.1 ").append(partial ? "206 Partial Content" : "200 OK").append("\r\n");
            headers.append("Content-Type: ").append(entry.mime).append("\r\n");
            headers.append("Content-Length: ").append(length).append("\r\n");
            headers.append("Accept-Ranges: bytes\r\n");
            headers.append("Access-Control-Allow-Origin: *\r\n");
            headers.append("Access-Control-Allow-Headers: Range\r\n");
            headers.append("Access-Control-Expose-Headers: Content-Length, Content-Range, Accept-Ranges\r\n");
            headers.append("Cache-Control: no-store\r\n");
            headers.append("Connection: close\r\n");
            if (partial) {
                headers.append("Content-Range: bytes ").append(start).append("-").append(end).append("/").append(size).append("\r\n");
            }
            headers.append("\r\n");
            out.write(headers.toString().getBytes("UTF-8"));
            if ("HEAD".equals(method)) return;

            channel.position(start);
            byte[] buffer = new byte[64 * 1024];
            long remaining = length;
            while (remaining > 0) {
                int want = (int) Math.min(buffer.length, remaining);
                int read = channel.read(java.nio.ByteBuffer.wrap(buffer, 0, want));
                if (read <= 0) break;
                out.write(buffer, 0, read);
                remaining -= read;
            }
            out.flush();
        } finally {
            try {
                if (stream != null) stream.close();
            } catch (Exception ignored) {}
            try {
                if (descriptor != null) descriptor.close();
            } catch (Exception ignored) {}
        }
    }

    private void writeRangeError(OutputStream out, long size) throws IOException {
        String headers = "HTTP/1.1 416 Range Not Satisfiable\r\n"
                + "Content-Range: bytes */" + size + "\r\n"
                + "Content-Length: 0\r\n"
                + "Access-Control-Allow-Origin: *\r\n"
                + "Connection: close\r\n\r\n";
        out.write(headers.getBytes("UTF-8"));
        out.flush();
    }

    private void writeSimple(OutputStream out, int code, String reason, String mime, String text, boolean head) throws IOException {
        byte[] body = text == null ? new byte[0] : text.getBytes("UTF-8");
        String headers = "HTTP/1.1 " + code + " " + reason + "\r\n"
                + "Content-Type: " + mime + "\r\n"
                + "Content-Length: " + body.length + "\r\n"
                + "Accept-Ranges: bytes\r\n"
                + "Access-Control-Allow-Origin: *\r\n"
                + "Access-Control-Allow-Headers: Range\r\n"
                + "Cache-Control: no-store\r\n"
                + "Connection: close\r\n\r\n";
        out.write(headers.getBytes("UTF-8"));
        if (!head && body.length > 0) out.write(body);
        out.flush();
    }

    private static String readLine(InputStream in) throws IOException {
        StringBuilder line = new StringBuilder();
        int value;
        while ((value = in.read()) != -1) {
            if (value == '\n') break;
            if (value != '\r') line.append((char) value);
            if (line.length() > 16384) break;
        }
        if (value == -1 && line.length() == 0) return null;
        return line.toString();
    }

    private static String escapeHtml(String value) {
        if (value == null) return "";
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
    }

    public static class MediaEntry {
        public final String id;
        public final Uri uri;
        public final String name;
        public final long size;
        public final String mime;

        public MediaEntry(String id, Uri uri, String name, long size, String mime) {
            this.id = id;
            this.uri = uri;
            this.name = name;
            this.size = size;
            this.mime = mime;
        }
    }
}
MEDIA_SERVER_JAVA

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
KEYSTORE=/home/ubuntu/tvhub-release.jks
if [ ! -f $KEYSTORE ]; then
    keytool -genkeypair -v -keystore $KEYSTORE -alias tvhub -keyalg RSA -keysize 2048 -validity 10000 -storepass tvhubpass -keypass tvhubpass -dname 'CN=TVHub, OU=Home, O=TVHub, L=Tbilisi, ST=Tbilisi, C=GE'
fi

apksigner sign --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --ks $KEYSTORE --ks-key-alias tvhub --ks-pass pass:tvhubpass --key-pass pass:tvhubpass --out $BUILD_DIR/TVHub.apk $BUILD_DIR/bin/aligned.apk

echo '=== Verifying APK Signature ==='
apksigner verify --verbose $BUILD_DIR/TVHub.apk

cp $BUILD_DIR/TVHub.apk /home/ubuntu/tvhub-v8.0.7-stage/static/TVHub.apk
cp $BUILD_DIR/TVHub.apk /home/ubuntu/tvhub-v8.0.7-stage/TVHub.apk


echo '=== Done! Autonomous Host APK successfully created at /home/ubuntu/tvhub-v8.0.7-stage/TVHub.apk ==='
ls -lh /home/ubuntu/tvhub-v8.0.7-stage/TVHub.apk
