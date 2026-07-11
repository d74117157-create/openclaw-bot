#!/bin/bash
# OpenClaw Superswarm — Render startup
set -e

echo "[EMPIRE] ╔═══════════════════════════════════════╗"
echo "[EMPIRE] ║  OpenClaw Superswarm v3.0-Trading    ║"
echo "[EMPIRE] ╚═══════════════════════════════════════╝"

# Verify critical env vars
MISSING=0
for var in DISCORD_TOKEN TELEGRAM_BOT1_TOKEN TELEGRAM_BOT2_TOKEN TELEGRAM_BOT3_TOKEN SLACK_BOT_TOKEN SLACK_APP_TOKEN; do
    if [ -z "${!var}" ]; then
        echo "[EMPIRE] ⚠️  $var not set"
        MISSING=$((MISSING+1))
    else
        echo "[EMPIRE] ✅ $var set"
    fi
done

echo "[EMPIRE] $MISSING env vars missing (non-critical if not using that platform)"

# Start the empire
exec python main.py
