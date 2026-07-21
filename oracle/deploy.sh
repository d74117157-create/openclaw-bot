#!/bin/bash
set -euo pipefail

echo "🦅 OpenClaw Oracle Cloud Deployment"

# Configuration
OCI_USER="opc"
OCI_HOST="${OCI_HOST:-}"
OCI_KEY="${OCI_KEY:-~/.ssh/id_rsa}"

if [ -z "$OCI_HOST" ]; then
    echo "❌ OCI_HOST not set. Export it first:"
    echo "   export OCI_HOST=your.oracle.vm.ip"
    exit 1
fi

echo "📦 Building application..."
docker build -t openclaw:latest ..

echo "💾 Saving image..."
docker save openclaw:latest | gzip > openclaw.tar.gz

echo "🚀 Deploying to Oracle VM..."
scp -i "$OCI_KEY" oracle/docker-compose.yml oracle/nginx.conf "$OCI_USER@$OCI_HOST:/home/$OCI_USER/openclaw/"
scp -i "$OCI_KEY" openclaw.tar.gz "$OCI_USER@$OCI_HOST:/home/$OCI_USER/openclaw/"

ssh -i "$OCI_KEY" "$OCI_USER@$OCI_HOST" << 'REMOTE'
    cd /home/opc/openclaw
    docker load < openclaw.tar.gz
    docker-compose down || true
    docker-compose up -d
    docker system prune -f
REMOTE

echo "✅ Deployment complete!"
echo "   Health check: curl https://$OCI_HOST/health"
