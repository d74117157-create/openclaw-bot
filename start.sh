#!/usr/bin/env bash
set -uo pipefail

echo "[OpenClaw Elite] ============================================"
echo "[OpenClaw Elite] Starting OpenClaw Elite Multi-Agent System"
echo "[OpenClaw Elite] Discord + 3x Telegram + Slack + All Agents"
echo "[OpenClaw Elite] ============================================"

# Check if ANY gateway is configured
if [ -z "${DISCORD_TOKEN:-}" ] && [ -z "${TELEGRAM_BOT1_TOKEN:-}" ] && [ -z "${TELEGRAM_BOT2_TOKEN:-}" ] && [ -z "${TELEGRAM_BOT3_TOKEN:-}" ] && [ -z "${SLACK_BOT_TOKEN:-}" ]; then
    echo "[OpenClaw Elite] ERROR: No gateway token configured!"
    echo "[OpenClaw Elite] Please set at least one of:"
    echo "[OpenClaw Elite] - DISCORD_TOKEN (for Discord)"
    echo "[OpenClaw Elite] - TELEGRAM_BOT1_TOKEN (for Telegram Bot 1)"
    echo "[OpenClaw Elite] - TELEGRAM_BOT2_TOKEN (for Telegram Bot 2)"
    echo "[OpenClaw Elite] - TELEGRAM_BOT3_TOKEN (for Telegram Bot 3)"
    echo "[OpenClaw Elite] - SLACK_BOT_TOKEN (for Slack)"
    echo "[OpenClaw Elite] In your Render dashboard Environment Variables"
    exit 1
fi

# Log env vars (without exposing secrets)
echo "[OpenClaw Elite] Environment check:"
echo "[OpenClaw Elite] DISCORD_TOKEN: ${DISCORD_TOKEN:+SET}"
echo "[OpenClaw Elite] DISCORD_GUILD_ID: ${DISCORD_GUILD_ID:-NOT SET (slash commands will sync globally, may take 1h)}"
echo "[OpenClaw Elite] TELEGRAM_BOT1_TOKEN: ${TELEGRAM_BOT1_TOKEN:+SET}"
echo "[OpenClaw Elite] TELEGRAM_BOT2_TOKEN: ${TELEGRAM_BOT2_TOKEN:+SET}"
echo "[OpenClaw Elite] TELEGRAM_BOT3_TOKEN: ${TELEGRAM_BOT3_TOKEN:+SET}"
echo "[OpenClaw Elite] SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN:+SET}"
echo "[OpenClaw Elite] SLACK_APP_TOKEN: ${SLACK_APP_TOKEN:+SET}"
echo "[OpenClaw Elite] SLACK_CHANNEL: ${SLACK_CHANNEL:-NOT SET}"
echo "[OpenClaw Elite] GROQ_API_KEY: ${GROQ_API_KEY:+SET}"
echo "[OpenClaw Elite] OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo "[OpenClaw Elite] GITHUB_TOKEN: ${GITHUB_TOKEN:+SET}"
echo "[OpenClaw Elite] REDIS_URL: ${REDIS_URL:-NOT SET (SQLite will be used as fallback)}"
echo "[OpenClaw Elite] MEMORY_DB: ${MEMORY_DB:-/app/data/openclaw_memory.db}"

# Optional Redis check
if [ -n "${REDIS_URL:-}" ]; then
    echo "[OpenClaw Elite] Checking Redis connectivity..."
    python3 -c "
import redis, sys
try:
    r = redis.from_url('${REDIS_URL}')
    r.ping()
    print('[OpenClaw Elite] Redis: OK')
except Exception as e:
    print(f'[OpenClaw Elite] Redis: UNAVAILABLE ({e})')
    print('[OpenClaw Elite] Falling back to SQLite for memory')
" || true
fi

# Test imports first
echo "[OpenClaw Elite] Testing imports..."
python3 test_imports.py
IMPORT_STATUS=$?

if [ $IMPORT_STATUS -ne 0 ]; then
    echo "[OpenClaw Elite] WARNING: Import test returned exit code $IMPORT_STATUS"
    echo "[OpenClaw Elite] Continuing startup anyway - non-critical modules may be unavailable"
fi

# Start the Elite system
echo "[OpenClaw Elite] Starting Elite Orchestrator..."
echo "[OpenClaw Elite] Active gateways: Discord, 3x Telegram, Slack"
echo "[OpenClaw Elite] Active agents: Bob, Carla, Dave, Alice, Coder, Reviewer, QA, Ops, Research, Growth, Memory, Business"
exec python3 main.py
