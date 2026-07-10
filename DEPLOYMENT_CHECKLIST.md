
PRE-DEPLOYMENT CHECKLIST
========================

□ Environment Variables Set (Render Dashboard)
  □ DISCORD_TOKEN
  □ GROQ_API_KEY
  □ SLACK_BOT_TOKEN (optional)
  □ SLACK_APP_TOKEN (optional)
  □ GITHUB_TOKEN (optional)

□ Render Service Created
  □ Repository: d74117157-create/openclaw-bot
  □ Branch: main
  □ Runtime: Python 3
  □ Build: pip install -r requirements.txt
  □ Start: python openclaw/main_async.py
  □ Health: /health

□ Post-Deployment Verification
  □ /health returns {"status": "healthy"}
  □ /ready returns 200 OK
  □ Discord bot comes online
  □ /status slash command responds
  □ Logs show no startup errors

□ Platform Testing
  □ Discord: /create-task test
  □ Discord: /agents list
  □ Slack: Mention bot in ops channel
  □ GitHub: /github list (if token set)
