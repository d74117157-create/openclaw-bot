#!/bin/bash
# OCI VM One-Time Setup Script
# Run this once on your Oracle Cloud VM

set -e

echo "[EMPIRE] Setting up OpenClaw on Oracle Cloud..."

sudo apt update && sudo apt install -y python3-pip git nginx

sudo mkdir -p /opt/openclaw
sudo chown ubuntu:ubuntu /opt/openclaw

cd /opt/openclaw
git clone https://github.com/d74117157-create/openclaw-bot.git .
pip3 install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/openclaw.service << 'EOF'
[Unit]
Description=OpenClaw Empire Node
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/openclaw
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/opt/openclaw/.env

[Install]
WantedBy=multi-user.target
EOF

# Create .env template
sudo tee /opt/openclaw/.env << 'EOF'
ANTHROPIC_API_KEY=your_anthropic_key
DISCORD_TOKEN=your_discord_token
TELEGRAM_BOT1_TOKEN=your_tg_bot1
TELEGRAM_BOT2_TOKEN=your_tg_bot2
TELEGRAM_BOT3_TOKEN=your_tg_bot3
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token
RENDER_URL=https://openclaw-bot.onrender.com
EOF

sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw

# Nginx reverse proxy
sudo tee /etc/nginx/sites-available/openclaw << 'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "[EMPIRE] OCI setup complete!"
echo "Edit /opt/openclaw/.env with your real API keys, then:"
echo "  sudo systemctl restart openclaw"
