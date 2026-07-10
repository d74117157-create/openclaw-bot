#!/bin/bash
# OpenClaw Oracle Cloud Infrastructure Setup Script
# Run this on your OCI VM after creation

set -e

echo "=========================================="
echo "  OpenClaw OCI VM Setup"
echo "=========================================="

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11 and dependencies
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt-get install -y git curl wget

# Install Node.js (for any frontend/build tools)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker (optional but recommended)
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER

# Create app directory
mkdir -p ~/openclaw-bot
cd ~/openclaw-bot

# Setup Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

echo ""
echo "=========================================="
echo "  OCI VM Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Clone your repo: git clone https://github.com/d74117157-create/openclaw-bot.git ~/openclaw-bot"
echo "2. Create .env file with your tokens"
echo "3. Install deps: pip install -r requirements.txt"
echo "4. Start bot: python openclaw/main_async.py"
echo ""
echo "For systemd service:"
echo "  sudo systemctl enable --now openclaw"
echo "  sudo systemctl status openclaw"
echo ""
