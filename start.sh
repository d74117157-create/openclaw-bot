#!/usr/bin/env bash
set -uo pipefail

echo "[OpenClaw Elite] ============================================"
echo "[OpenClaw Elite] Starting OpenClaw Elite Multi-Agent System"
echo "[OpenClaw Elite] ============================================"

# Only require DISCORD_TOKEN
if [ -z "${DISCORD_TOKEN:-}" ]; then
    echo "[OpenClaw Elite] ERROR: DISCORD_TOKEN not set" >&2
    echo "[OpenClaw Elite] Please set DISCORD_TOKEN in Render dashboard Environment Variables"
    exit 1
fi

# Log env vars (without exposing secrets)
echo "[OpenClaw Elite] Environment check:"
echo "[OpenClaw Elite] DISCORD_TOKEN: ${DISCORD_TOKEN:+SET}"
echo "[OpenClaw Elite] DISCORD_GUILD_ID: ${DISCORD_GUILD_ID:-NOT SET}"
echo "[OpenClaw Elite] GROQ_API_KEY: ${GROQ_API_KEY:+SET}"
echo "[OpenClaw Elite] OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo "[OpenClaw Elite] SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN:+SET}"
echo "[OpenClaw Elite] SLACK_CHANNEL: ${SLACK_CHANNEL:-NOT SET}"
echo "[OpenClaw Elite] GITHUB_TOKEN: ${GITHUB_TOKEN:+SET}"

# Test imports first - with full error visibility
echo "[OpenClaw Elite] Testing imports..."
python3 test_imports.py
IMPORT_STATUS=$?

if [ $IMPORT_STATUS -ne 0 ]; then
    echo "[OpenClaw Elite] WARNING: Import test had issues (exit code $IMPORT_STATUS)"
    echo "[OpenClaw Elite] Attempting to start anyway..."
fi

# Start the Elite system
echo "[OpenClaw Elite] Starting Elite Orchestrator..."
exec python3 main.py
