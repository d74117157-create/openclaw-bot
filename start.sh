#!/usr/bin/env bash
set -euo pipefail

echo "[OpenClaw] Starting Discord bot..."

# Only require DISCORD_TOKEN
if [ -z "${DISCORD_TOKEN:-}" ]; then
  echo "[OpenClaw] ERROR: DISCORD_TOKEN not set" >&2
  exit 1
fi

# Start Discord bot
exec python3 gateway/bot.py
