#!/usr/bin/env bash
set -euo pipefail

echo "[OpenClaw] ============================================"
echo "[OpenClaw] Starting OpenClaw Discord Bot"
echo "[OpenClaw] ============================================"

# Only require DISCORD_TOKEN
if [ -z "${DISCORD_TOKEN:-}" ]; then
  echo "[OpenClaw] ERROR: DISCORD_TOKEN not set" >&2
  echo "[OpenClaw] Please set DISCORD_TOKEN in Render dashboard Environment Variables"
  exit 1
fi

# Log env vars (without exposing secrets)
echo "[OpenClaw] Environment check:"
echo "[OpenClaw]   DISCORD_TOKEN: ${DISCORD_TOKEN:+SET}"
echo "[OpenClaw]   DISCORD_GUILD_ID: ${DISCORD_GUILD_ID:-NOT SET}"
echo "[OpenClaw]   GROQ_API_KEY: ${GROQ_API_KEY:+SET}"
echo "[OpenClaw]   SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:+SET}"
echo "[OpenClaw]   SLACK_CHANNEL: ${SLACK_CHANNEL:-NOT SET}"

# Test imports first
echo "[OpenClaw] Testing imports..."
python3 test_imports.py

# Start Discord bot with background heartbeat for Render
echo "[OpenClaw] Starting bot..."
exec python3 gateway/bot.py
