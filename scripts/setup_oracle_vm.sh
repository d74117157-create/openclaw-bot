#!/bin/bash
set -e
echo "🐝 Setting up OpenClaw on Oracle VM..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg git fail2ban ufw
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \"$(. /etc/os-release && echo \"$$VERSION_CODENAME\")\" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
sudo ufw allow 22/tcp; sudo ufw allow 80/tcp; sudo ufw allow 443/tcp; sudo ufw allow 8000/tcp
sudo ufw --force enable
mkdir -p ~/openclaw-superswarm/logs ~/openclaw-superswarm/data
echo "✅ Done. Log out and back in for docker group."
