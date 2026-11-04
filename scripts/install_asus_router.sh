#!/bin/sh
# TV Hub 24/7 ASUS Router Node Setup (Asuswrt / Asuswrt-Merlin)
# For ASUS RT-AX1800U and other ASUS routers with USB port + Entware
#
# Requirements:
# 1. A USB Flash Drive plugged into the ASUS Router's USB port
# 2. Entware enabled (via Asuswrt-Merlin or stock Asuswrt USB Applications / Download Master)
# 3. SSH enabled in Router Administration -> System -> Enable SSH

set -e

echo "=============================================="
echo "📺 TV Hub 24/7 ASUS Router Node Setup"
echo "=============================================="

# Check if opkg is available
if ! command -v opkg >/dev/null 2>&1; then
    echo "⚠️ Entware (opkg) not detected."
    echo "To enable Entware on ASUS RT-AX1800U:"
    echo "1. Insert a USB flash drive (formatted EXT4 or NTFS) into the router."
    echo "2. Open Router Web UI -> USB Application -> Install Download Master."
    echo "3. Or run the Asuswrt Entware installer: entware-setup.sh"
    exit 1
fi

echo "📦 Installing Python3 and tools via Entware opkg..."
opkg update
opkg install python3 python3-pip git-http curl ca-certificates

# Clone or update Home-TV
INSTALL_DIR="/opt/Home-TV"
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Updating existing TV Hub in $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📥 Cloning TV Hub into $INSTALL_DIR..."
    git clone https://github.com/anania39/Home-TV.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "⚙️ Installing Python dependencies..."
pip3 install fastapi uvicorn httpx pydantic

# Create startup init service
INIT_SCRIPT="/opt/etc/init.d/S99tvhub"
cat << 'EOF' > "$INIT_SCRIPT"
#!/bin/sh
ENABLED=yes
PROCS=python3
ARGS="-m uvicorn backend.app:app --host 0.0.0.0 --port 8000"
PREARGS=""
DESC="TV Hub 24/7 Network Daemon"
PATH=/opt/sbin:/opt/bin:/opt/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

case "$1" in
    start)
        echo "Starting $DESC..."
        cd /opt/Home-TV
        PORT=8000 NO_DEVICES=0 nohup python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 > /opt/var/log/tvhub.log 2>&1 &
        ;;
    stop)
        echo "Stopping $DESC..."
        killall python3 2>/dev/null || true
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
EOF
chmod +x "$INIT_SCRIPT"

echo ""
echo "=============================================="
echo "🎉 TV Hub installed successfully on Router!"
echo "=============================================="
echo "🌐 Accessible on your local Wi-Fi network at: http://192.168.50.1:8000"
echo "📺 TV Web Receiver at:                        http://192.168.50.1:8000/tv"
echo ""
"$INIT_SCRIPT" start
