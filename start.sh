#!/bin/bash
# Render startup script
set -e

echo "[EMPIRE] Starting OpenClaw Empire..."

# Install Claude Code CLI for in-service building
curl -fsSL https://claude.ai/install.sh | bash || echo "Claude Code install skipped (non-critical)"

# Run the app
exec python main.py
