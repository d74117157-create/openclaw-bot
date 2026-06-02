#!/usr/bin/env bash
set -euo pipefail

# Ensure logs dir exists
mkdir -p logs

# Activate venv automatically if present
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Run env checks to fail fast with clear messages
if [ -f scripts/env_check.py ]; then
  echo "Running environment checks..."
  python3 scripts/env_check.py || {
    echo "Environment validation failed. Check Render/GitHub secrets and logs for details." >&2
    exit 1
  }
fi

# Start Slack bot in background
if [ -f gateway/slack_bot.py ]; then
  echo "Starting Slack bot..."
  python gateway/slack_bot.py >> logs/slack.log 2>&1 &
  SLACK_PID=$!
  echo "Slack bot PID: $SLACK_PID"
else
  echo "No Slack bot entrypoint found at gateway/slack_bot.py"
fi

# Start Discord bot in background
if [ -f gateway/bot.py ]; then
  echo "Starting Discord bot..."
  python gateway/bot.py >> logs/discord.log 2>&1 &
  DISCORD_PID=$!
  echo "Discord bot PID: $DISCORD_PID"
else
  echo "No Discord bot entrypoint found at gateway/bot.py"
fi

# Run health web server in foreground (Render expects a web process)
exec uvicorn web.health:app --host 0.0.0.0 --port ${PORT:-10000}
