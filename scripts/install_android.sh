#!/bin/bash
# TV Hub 24/7 Autonomous Android Host Node Installer
# Runs TV Hub locally on any Android device via Termux
# Enables 24/7 direct local Wi-Fi casting to Smart TVs even with laptop off!

set -e

echo "=============================================="
echo "📺 TV Hub 24/7 Android Host Node Setup"
echo "=============================================="

# 1. Update Termux repositories and install python & git
echo "📦 Updating Termux environment..."
pkg update -y
pkg install -y python git curl clang make libjpeg-turbo

# 2. Clone or update repository
if [ -d "$HOME/Home-TV" ]; then
    echo "🔄 Updating existing TV Hub repository..."
    cd "$HOME/Home-TV"
    git pull origin main
else
    echo "📥 Cloning TV Hub repository..."
    git clone https://github.com/anania39/Home-TV.git "$HOME/Home-TV"
    cd "$HOME/Home-TV"
fi

# 3. Setup virtual environment & requirements
echo "⚙️ Setting up Python environment..."
python -m venv venv || python -m venv --without-pip venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install fastapi uvicorn httpx yt-dlp pydantic

# 4. Create start script
cat << 'EOF' > "$HOME/start_tvhub.sh"
#!/bin/bash
cd "$HOME/Home-TV"
source venv/bin/activate
export PORT=8000
export NO_DEVICES=0
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
EOF
chmod +x "$HOME/start_tvhub.sh"

# 5. Get Android Wi-Fi IP
ANDROID_IP=$(ip addr show wlan0 2>/dev/null | grep "inet\b" | awk '{print $2}' | cut -d/ -f1 || echo "127.0.0.1")

echo ""
echo "=============================================="
echo "🎉 TV Hub installed successfully on Android!"
echo "=============================================="
echo "📱 Run TV Hub anytime with: ~/start_tvhub.sh"
echo "🌐 Local Phone/TV Controller: http://$ANDROID_IP:8000"
echo "📺 TV Web Receiver:          http://$ANDROID_IP:8000/tv"
echo ""
echo "Starting TV Hub daemon now..."
"$HOME/start_tvhub.sh"
