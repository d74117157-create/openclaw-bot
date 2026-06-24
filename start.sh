#!/usr/bin/env bash
set -euo pipefail

echo "[OpenClaw] Starting swarm..."

# Run env checks
if [ -f scripts/env_check.py ]; then
  echo "[OpenClaw] Running environment checks..."
  python3 scripts/env_check.py || {
    echo "[OpenClaw] Environment validation failed. Check env vars." >&2
    exit 1
  }
fi

# Start Discord bot (main process)
if [ -f gateway/bot.py ]; then
  echo "[OpenClaw] Starting Discord bot..."
  exec python3 gateway/bot.py
else
  echo "[OpenClaw] ERROR: gateway/bot.py not found"
  exit 1
fi
