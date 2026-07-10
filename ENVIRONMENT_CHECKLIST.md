# OpenClaw Environment Checklist

## Discord
DISCORD_TOKEN:
  Required: Yes (for Discord bot)
  Purpose: Discord bot authentication token
  Used By: gateway/bot.py, gateway/brain_bot.py

BRAIN_CHANNEL:
  Required: No (default: brain)
  Purpose: Discord channel name for brain relay
  Used By: gateway/brain_bot.py

## Slack
SLACK_BOT_TOKEN:
  Required: Yes (for Slack bot)
  Purpose: Slack Bot User OAuth Token
  Used By: gateway/slack_bot.py

SLACK_APP_TOKEN:
  Required: Yes (for Slack Socket Mode)
  Purpose: Slack App-Level Token (xapp-...)
  Used By: gateway/slack_bot.py

SLACK_CHANNEL:
  Required: No (default: ops)
  Purpose: Default Slack channel for notifications
  Used By: gateway/slack_bot.py, worker/slack_reporter.py

SLACK_WEBHOOK_URL:
  Required: No
  Purpose: Slack incoming webhook URL for notifications
  Used By: worker/slack_reporter.py

## AI (Groq)
GROQ_API_KEY:
  Required: Yes
  Purpose: Groq API authentication
  Used By: worker/ai_worker.py

GROQ_MODEL:
  Required: No (default: llama3-70b-8192)
  Purpose: Groq model selection
  Used By: worker/ai_worker.py

## GitHub
GITHUB_TOKEN:
  Required: Yes (for GitHub automation)
  Purpose: GitHub Personal Access Token
  Used By: kernel.py, worker/github_agent.py

GITHUB_REPO:
  Required: No
  Purpose: Target GitHub repository (owner/repo)
  Used By: worker/github_agent.py

## Database
MEMORY_DB:
  Required: No (default: openclaw_memory.db)
  Purpose: SQLite database file path
  Used By: memory/__init__.py

## Browser
BROWSER_HEADLESS:
  Required: No (default: true)
  Purpose: Run Playwright in headless mode
  Used By: worker/browser_worker.py

SCREENSHOT_DIR:
  Required: No (default: /tmp/openclaw_screenshots)
  Purpose: Directory for browser screenshots
  Used By: worker/browser_worker.py

## Server
HEALTH_PORT:
  Required: No (default: 8080)
  Purpose: Health server port
  Used By: openclaw/health.py

PORT:
  Required: No (default: 3000)
  Purpose: Main application port
  Used By: Render service

## Redis
REDIS_URL:
  Required: No
  Purpose: Redis connection URL for caching
  Used By: worker/executor.py

## Deployment
RAILWAY_TOKEN:
  Required: No
  Purpose: Railway CLI authentication
  Used By: .github/workflows/deploy.yml

RENDER_API_KEY:
  Required: No
  Purpose: Render API key for deployment
  Used By: render.yaml (if used)

## Other
OPENCLAW_API_KEY:
  Required: No
  Purpose: API key for OpenClaw services
  Used By: kernel.py

OWNER_ID:
  Required: No
  Purpose: Discord owner ID for admin commands
  Used By: gateway/bot.py

WEB_PORT:
  Required: No (default: 8080)
  Purpose: Web server port
  Used By: main.py
