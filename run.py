import sys
import uvicorn
import socket

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.config import PORT, SERVER_IP

def main():
    print("=" * 65)
    print("  [TV HUB] - SMART TV CAST & REMOTE CONTROLLER")
    print("=" * 65)
    print(f"  * Local IP:                 http://{SERVER_IP}:{PORT}")
    print(f"  * TV Browser Receiver:      http://{SERVER_IP}:{PORT}/tv")
    print(f"  * Default Target TV:        Hisense VIDAA TV (192.168.50.249)")
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
