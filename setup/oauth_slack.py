#!/usr/bin/env python3
"""
Slack OAuth for Workspace Installation
"""
import os

CLIENT_ID = os.getenv("SLACK_CLIENT_ID", "")
REDIRECT_URI = "https://openclaw-bot.onrender.com/oauth/slack/callback"

SCOPES = [
    "chat:write",
    "chat:write.public",
    "commands",
    "users:read",
    "channels:read",
    "groups:read",
    "im:read",
    "mpim:read",
]

auth_url = f"https://slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&scope={','.join(SCOPES)}&redirect_uri={REDIRECT_URI}"

print("=== Slack OAuth Setup ===")
print(f"Install URL:
{auth_url}")
print("""
1. Go to https://api.slack.com/apps → Your App → OAuth & Permissions
2. Add SLACK_CLIENT_ID and SLACK_CLIENT_SECRET to Render
3. Add the redirect URI above to Slack app settings
4. Use the install URL to add the bot to your workspace
5. SLACK_BOT_TOKEN and SLACK_APP_TOKEN are separate — from Slack app settings
""")
