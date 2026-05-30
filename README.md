# OpenClaw - Multi-deployment orchestration

This branch implements a Notion-backed deployment manager and bot integrations for Slack and Discord.

Overview
- Notion DB: "OpenClaw Deployments" (see schema below)
- DeploymentManager: loads DB, health-checks every 60s, selects ACTIVE_DEPLOYMENT
- Discord bot: commands /status, /switch, /sync-notion
- Slack agent: Socket Mode app with example commands
- Integrations: skeletons for Render, Pipedream, Crevio

Notion DB schema (properties):
- Name (Title)
- provider (Select)
- status (Select: online, degraded, offline)
- base_url (URL)
- last_checked (Date)
- priority (Number)

Setup
1. Create a Notion integration and share the database with it. Add the DB ID and token to repo secrets.
2. Add secrets to GitHub: NOTION_API_KEY, NOTION_DB_ID, DISCORD_TOKEN, DISCORD_APPLICATION_ID, SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_SIGNING_SECRET
3. (Optional) Add deploy provider secrets: RENDER_API_KEY, RAILWAY_API_KEY, etc.
4. To run locally, copy .env.example -> .env and fill values. Install requirements: pip install -r requirements.txt

Run
- Start Discord bot: python -c "from src.openclaw.discord_bot import start_discord_bot; import asyncio; asyncio.run(start_discord_bot(<NOTION_API_KEY>, <NOTION_DB_ID>))"
- Start Slack Socket Mode: python -c "from src.openclaw.slack_agent import start_slack; import asyncio; asyncio.run(start_slack(<NOTION_API_KEY>, <NOTION_DB_ID>))"

Security
- Do NOT commit secrets. Rotate any tokens that were exposed previously.

