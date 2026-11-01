import sys
import uvicorn
import socket

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        import ctypes
        # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001) | ES_AWAYMODE_REQUIRED (0x00000040)
        # Prevents Windows from going into standby/sleep while TV Hub is running as a home media appliance
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 | 0x00000040)
    except Exception:
        pass

from backend.config import PORT, SERVER_IP

def main():
    print("=" * 65)
    print("  [TV HUB] - SMART TV CAST & REMOTE CONTROLLER")
    print("=" * 65)
    print(f"  * Local IP:                 http://{SERVER_IP}:{PORT}")
    print(f"  * TV Browser Receiver:      http://{SERVER_IP}:{PORT}/tv")
    print(f"  * Dynamic Discovery:        Auto-detects TVs & devices on current Wi-Fi")
    print("  * Starting Public Tunnel for phone remote control...")
    print("=" * 65)
    print("  TIP: You can open either the local IP or the generated")
    print("       public link on your smartphone to control the TV.")
    print("=" * 65)

    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
