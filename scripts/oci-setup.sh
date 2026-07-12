#!/bin/bash
# OpenClaw OCI Worker Setup — Run this on the Oracle Linux VM after creation
set -e

echo "[OCI] ╔═══════════════════════════════════════════╗"
echo "[OCI] ║  OpenClaw OCI Worker Bootstrap          ║"
echo "[OCI] ╚═══════════════════════════════════════════╝"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[OCI] Installing Docker..."
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "[OCI] ✅ Docker installed — log out and back in for group changes"
fi

# Setup app directory
APP_DIR="/opt/openclaw/app"
sudo mkdir -p "$APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
    echo "[OCI] Cloning OpenClaw repo..."
    sudo git clone https://github.com/d74117157-create/openclaw-bot.git "$APP_DIR"
else
    echo "[OCI] Repo exists — updating..."
    cd "$APP_DIR"
    sudo git pull origin main
fi

# Build
echo "[OCI] Building Docker image..."
cd "$APP_DIR"
sudo docker build -t openclaw:latest .

# Create env file template
cat << 'ENVFILE' | sudo tee /opt/openclaw/.env
# Copy your Render env vars here
DISCORD_TOKEN=
TELEGRAM_BOT1_TOKEN=
TELEGRAM_BOT2_TOKEN=
TELEGRAM_BOT3_TOKEN=
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
ANTHROPIC_API_KEY=
TRADING_MODE=paper
BINANCE_API_KEY=
BINANCE_API_SECRET=
ENVFILE

echo "[OCI] ✅ Setup complete. Edit /opt/openclaw/.env and run:"
echo "[OCI]    sudo docker run -d --name openclaw --restart unless-stopped -p 8000:8000 --env-file /opt/openclaw/.env openclaw:latest"
