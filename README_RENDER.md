Render deployment and environment instructions for OpenClaw

This file documents what to set when creating a Render service for OpenClaw.

1) Recommended service type
- Create a "Web Service" in Render (connect your GitHub repo).
- Branch: main
- Build Command: (leave blank) or `pip install -r requirements_v2.txt`
- Start Command: `./start.sh` or let Render detect Procfile (it will run the `web` process)
- Environment: Python 3.10

2) Required environment variables (set these in Render dashboard -> Environment)
- SLACK_BOT_TOKEN: xoxb-... (Bot token)
- SLACK_APP_TOKEN: xapp-... (App token for Socket Mode)
- SLACK_CHANNEL: the channel name or ID the bot will post to
- DISCORD_TOKEN: (if you also run Discord in same service)
- OLLAMA_BASE_URL or ANTHROPIC_API_KEY / GROQ_API_KEY: LLM backend settings
- MEMORY_DB (optional): path to sqlite DB (e.g., /tmp/openclaw.db)

3) GitHub Secrets (if using the deploy workflow)
- RENDER_API_KEY
- RENDER_SERVICE_ID

4) Health check
- Render will use the exposed port; the health endpoint is available at `/health` (e.g., https://your-service.onrender.com/health)

5) Notes & troubleshooting
- Start command (`./start.sh`) launches Slack and Discord bots in the background and then starts a FastAPI health server. Logs are written to `logs/discord.log` and `logs/slack.log`.
- If you prefer separate Render services for Slack and Discord, create two services and set the Start Command for each to run the appropriate gateway script.
- Ensure you do NOT paste your tokens anywhere public. Rotate tokens if they have been exposed.
