#!/bin/bash
set -e

echo "=========================================="
echo "  OpenClaw ELITE"
echo "  Multi-Agent Bot Swarm Platform"
echo "=========================================="

# Validate critical environment variables
if [ -z "$DISCORD_TOKEN" ] && [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "WARNING: No bot token configured. Set DISCORD_TOKEN or SLACK_BOT_TOKEN."
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "WARNING: GROQ_API_KEY not set. AI features will be disabled."
fi

# Render requires binding to $PORT for web services
# If PORT is set, we need a web server. Start it in background.
if [ -n "$PORT" ]; then
    echo "Starting health server on port $PORT..."
    python -c "
import os, sys
sys.path.insert(0, '/app')
from openclaw.health import create_health_app
import uvicorn
app = create_health_app()
uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), log_level='warning')
" &
    HEALTH_PID=$!
    echo "Health server started (PID: $HEALTH_PID)"
fi

echo "Starting OpenClaw Elite bots..."
exec python main.py
