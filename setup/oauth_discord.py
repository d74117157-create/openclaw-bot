#!/usr/bin/env python3
"""
Discord OAuth 2.0 for Bot Invite & Slash Command Permissions
"""
import os

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
REDIRECT_URI = "https://openclaw-bot.onrender.com/oauth/discord/callback"

SCOPES = [
    "bot",
    "applications.commands",
]

PERMISSIONS = "8"  # Administrator (for full bot control)

auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions={PERMISSIONS}&scope={'%20'.join(SCOPES)}&redirect_uri={REDIRECT_URI}&response_type=code"

print("=== Discord OAuth Setup ===")
print(f"Bot Invite URL:
{auth_url}")
print("""
1. Add DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET to Render
2. Use the invite URL above to add the bot to your server
3. The bot needs Administrator permissions for full swarm control
4. DISCORD_TOKEN is separate — that's the bot token from Discord Developer Portal
""")
