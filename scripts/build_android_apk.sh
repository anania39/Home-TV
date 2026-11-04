#!/bin/bash
set -e
echo '=== Building TV Hub Android APK ==='

BUILD_DIR=/home/ubuntu/tvhub_apk_build
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR/src/com/tvhub/app
mkdir -p $BUILD_DIR/res/values
mkdir -p $BUILD_DIR/res/mipmap-hdpi
mkdir -p $BUILD_DIR/res/mipmap-xhdpi
mkdir -p $BUILD_DIR/res/mipmap-xxhdpi
mkdir -p $BUILD_DIR/bin

# 1. Generate App Icon (Cyan / Dark Blue TV Hub Launcher)
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
            if dx * dx + dy * dy < (w // 8) * (w // 8) and (x < w // 8 or x > w - w // 8) and (y < h // 8 or y > h - h // 8):
                raw += bytes([11, 15, 25])
            elif x > w // 4 and x < w - w // 4 and y > h // 4 and y < h - h // 4:
                raw += bytes([255, 255, 255])
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
PYEOF

# 2. Strings
cat << 'STRINGS' > $BUILD_DIR/res/values/strings.xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TV Hub</string>
</resources>
STRINGS

# 3. AndroidManifest.xml
cat << 'MANIFEST' > $BUILD_DIR/AndroidManifest.xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.tvhub.app"
    android:versionCode="6"
    android:versionName="6.0">

    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="33" />

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
        android:usesCleartextTraffic="true">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
MANIFEST

# 4. MainActivity.java
cat << 'JAVA' > $BUILD_DIR/src/com/tvhub/app/MainActivity.java
package com.tvhub.app;

import android.app.Activity;
import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

public class MainActivity extends Activity {
    private WebView webView;
    private WifiManager.MulticastLock multicastLock;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        try {
            WifiManager wm = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            if (wm != null) {
                multicastLock = wm.createMulticastLock("TVHubMulticastLock");
                multicastLock.setReferenceCounted(true);
                multicastLock.acquire();
            }
        } catch (Exception e) {}

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF0B0F19);

        webView = new WebView(this);
        root.addView(webView);
        setContentView(root);

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

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                view.loadUrl(url);
                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                request.grant(request.getResources());
            }
        });

        webView.loadUrl("https://tvhub.92.5.71.162.sslip.io");
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (multicastLock != null && multicastLock.isHeld()) {
            multicastLock.release();
        }
    }
}
JAVA

echo '=== Packaging resources with aapt ==='
ANDROID_JAR=/usr/lib/android-sdk/platforms/android-23/android.jar
aapt package -f -m -J $BUILD_DIR/src -M $BUILD_DIR/AndroidManifest.xml -S $BUILD_DIR/res -I $ANDROID_JAR

echo '=== Compiling Java sources ==='
javac -source 8 -target 8 -bootclasspath $ANDROID_JAR -d $BUILD_DIR/bin $BUILD_DIR/src/com/tvhub/app/*.java

echo '=== Converting bytecode to Dalvik DEX ==='
dalvik-exchange --dex --output=$BUILD_DIR/bin/classes.dex $BUILD_DIR/bin

echo '=== Creating unaligned APK ==='
aapt package -f -M $BUILD_DIR/AndroidManifest.xml -S $BUILD_DIR/res -I $ANDROID_JAR -F $BUILD_DIR/bin/unaligned.apk $BUILD_DIR/bin

echo '=== Aligning APK with zipalign ==='
zipalign -f -p 4 $BUILD_DIR/bin/unaligned.apk $BUILD_DIR/bin/aligned.apk

echo '=== Generating Keystore & Signing APK ==='
KEYSTORE=$BUILD_DIR/release.jks
if [ ! -f $KEYSTORE ]; then
    keytool -genkeypair -v -keystore $KEYSTORE -alias tvhub -keyalg RSA -keysize 2048 -validity 10000 -storepass tvhubpass -keypass tvhubpass -dname 'CN=TVHub, OU=Home, O=TVHub, L=Tbilisi, ST=Tbilisi, C=GE'
fi

apksigner sign --ks $KEYSTORE --ks-key-alias tvhub --ks-pass pass:tvhubpass --key-pass pass:tvhubpass --out $BUILD_DIR/TVHub.apk $BUILD_DIR/bin/aligned.apk

echo '=== Verifying APK Signature ==='
apksigner verify $BUILD_DIR/TVHub.apk

cp $BUILD_DIR/TVHub.apk /home/ubuntu/Home-TV/static/TVHub.apk
cp $BUILD_DIR/TVHub.apk /home/ubuntu/Home-TV/TVHub.apk

echo '=== Done! APK successfully created at /home/ubuntu/Home-TV/TVHub.apk ==='
ls -lh /home/ubuntu/Home-TV/TVHub.apk
