# 🔐 OpenClaw Secrets Master Guide
# EVERYTHING you need to configure. Copy-paste ready.
# ⚠️  NEVER commit real tokens to GitHub. Use Render env vars only.

===============================================
SECTION 1: RENDER ENVIRONMENT VARIABLES
===============================================

Go to: https://dashboard.render.com → Your Service → Environment

--- DISCORD ---
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
DISCORD_GUILD_ID=YOUR_GUILD_ID_HERE
DISCORD_CHANNEL_ID=YOUR_CHANNEL_ID_HERE
DISCORD_WEBHOOK_URL=YOUR_DISCORD_WEBHOOK_URL_HERE

--- TELEGRAM ---
TELEGRAM_BOT_TOKEN_1=YOUR_BOT1_TOKEN_HERE
TELEGRAM_BOT_TOKEN_2=YOUR_BOT2_TOKEN_HERE
TELEGRAM_BOT_TOKEN_3=YOUR_BOT3_TOKEN_HERE
TELEGRAM_BOT_TOKEN_SUPER=YOUR_SUPER_BOT_TOKEN_HERE

--- SLACK ---
SLACK_APP_TOKEN=YOUR_SLACK_APP_TOKEN_HERE
SLACK_BOT_TOKEN=YOUR_SLACK_BOT_TOKEN_HERE
SLACK_WEBHOOK_URL=YOUR_SLACK_WEBHOOK_URL_HERE

--- YOUTUBE / GOOGLE ---
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE

--- GITHUB ---
GITHUB_TOKEN=YOUR_GITHUB_PAT_HERE

--- RENDER ---
RENDER_API_KEY=YOUR_RENDER_API_KEY_HERE
RENDER_SERVICE_ID=YOUR_RENDER_SERVICE_ID_HERE

--- ORACLE CLOUD ---
OCI_HOST=YOUR_ORACLE_VM_IP_HERE
OCI_USER=opc
OCI_SSH_KEY=YOUR_SSH_PRIVATE_KEY_HERE

--- OPTIONAL: PAID APIs (for v2) ---
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_KEY_HERE

===============================================
SECTION 2: HOW TO GET EACH SECRET
===============================================

--- DISCORD TOKEN ---
1. Go to https://discord.com/developers/applications
2. Click your app → Bot → Reset Token → Copy
3. Enable: Message Content Intent, Server Members Intent, Presence Intent

--- DISCORD WEBHOOK ---
1. In your Discord server → Server Settings → Integrations → Webhooks
2. New Webhook → Select channel → Copy Webhook URL

--- TELEGRAM TOKENS ---
1. Message @BotFather on Telegram
2. /newbot → name it → copy token
3. For each bot, repeat. You have 4 bots = 4 tokens.
4. Send a message to each bot FIRST (so Victor can find your chat ID)

--- SLACK TOKENS ---
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. OAuth & Permissions → Bot Token Scopes:
   - chat:write
   - channels:read
   - groups:read
   - im:read
   - mpim:read
4. Install to Workspace → Copy Bot Token (xoxb-...)
5. Basic Info → App-Level Tokens → Generate (xapp-...)
6. Incoming Webhooks → Add New → Copy URL

--- GOOGLE API KEY ---
1. Go to https://console.cloud.google.com
2. Create project → APIs & Services → Enable APIs:
   - YouTube Data API v3
   - YouTube Analytics API v2
3. Credentials → Create API Key → Copy

--- GITHUB TOKEN ---
1. https://github.com/settings/tokens
2. Generate new token (classic) → Select scopes:
   - repo (full control)
   - workflow
   - read:org
3. Copy token

--- RENDER API KEY ---
1. https://dashboard.render.com → Account Settings → API Keys
2. Create API Key → Copy

--- ORACLE CLOUD ---
1. Create VM at https://cloud.oracle.com
2. Generate SSH key pair: ssh-keygen -t rsa -b 4096
3. Add public key to VM
4. Copy private key as OCI_SSH_KEY env var
5. Copy VM public IP as OCI_HOST

===============================================
SECTION 3: SECURITY HARDENING
===============================================

NEVER commit these to GitHub:
- All tokens above
- SSH keys
- Database passwords

ALWAYS:
1. Set them as Render Environment Variables (encrypted at rest)
2. Use .env files ONLY for local dev (add to .gitignore)
3. Rotate tokens monthly
4. Never share screenshots with tokens visible
5. Use separate tokens for dev vs production

WHAT TO ADD TO .gitignore:
```
.env
*.pem
*.key
secrets/
config/local*
logs/*.log
data/trading/*.json
```

===============================================
SECTION 4: THE MONEY HACKS (Growth Secrets)
===============================================

HACK 1: Content Arbitrage
- Scrape trending topics from YouTube/Twitter/Reddit
- Rewrite with AI → post to ALL platforms
- Link back to your monetized channel/blog
- Revenue: AdSense, affiliate links, sponsors

HACK 2: Signal Selling
- Run trading signals 24/7
- Post free signals publicly (build trust)
- DM premium signals to paid subscribers
- Revenue: Patreon, Telegram paid channels, Discord subscriptions
- Price: $10-50/month per subscriber

HACK 3: Bot-as-a-Service
- Your swarm manages communities
- Offer to Discord/Telegram server owners
- "I'll run your community bot for $100/month"
- Revenue: Monthly retainer

HACK 4: Lead Generation
- Scrape Twitter/Reddit for people asking questions
- Auto-reply with helpful info + your link
- Funnel to email list or product
- Revenue: Affiliate, SaaS, info products

HACK 5: SaaS Wrapper
- Package your swarm as a product
- "AutoContent AI" - generates videos for creators
- "SignalBot Pro" - trading signals for traders
- Revenue: $20-100/month subscriptions

===============================================
SECTION 5: RENDER DEPLOY CHECKLIST
===============================================

Before hitting deploy, verify:

[ ] All env vars set in Render dashboard
[ ] requirements.txt has: requests, python-telegram-bot, discord.py, slack-bolt
[ ] main.py starts victor.py or FastAPI server
[ ] GitHub repo has latest code pushed
[ ] Render service linked to correct repo branch
[ ] Health check URL returns 200
[ ] Telegram bots have received at least one message
[ ] Discord bot invited to server with correct permissions
[ ] Slack app installed to workspace

===============================================
SECTION 6: QUICK TEST COMMANDS
===============================================

# Test YouTube pipeline
python3 automation/youtube_pipeline.py tech US

# Test trading signals
python3 automation/trading_signals.py --top

# Test Victor orchestrator
python3 victor.py "health check"
python3 victor.py "broadcast test message"
python3 victor.py "make a youtube video about crypto"

# Test platform posting
python3 -c "from victor import broadcast; broadcast('🚀 OpenClaw is LIVE')"

===============================================
SECTION 7: TROUBLESHOOTING SECRETS
===============================================

Problem: "Module not found"
Fix: pip install -r requirements.txt

Problem: "Telegram bot not responding"
Fix: Send /start to the bot first. Victor needs a chat ID.

Problem: "Discord webhook 401"
Fix: Regenerate webhook URL. Old one expired.

Problem: "YouTube API quota exceeded"
Fix: You get 10,000 units/day. Each search = 100 units. 
     Cache results. Use trending endpoint (cheap).

Problem: "Binance API 429 (rate limit)"
Fix: Add time.sleep(1) between requests. Or use WebSocket.

Problem: "Render service sleeping"
Fix: Ping it every 10 min with UptimeRobot (free)
     Or upgrade to paid plan ($7/month)

===============================================
SECTION 8: YOUR ACTUAL TOKENS (DO NOT SHARE)
===============================================

Your real tokens are stored in this conversation memory.
When you need them, ask Victor or Claude to recall them.
Never paste them in public channels or GitHub.

Key tokens you have configured:
- Discord token (starts with MTUx...)
- 3 Telegram bot tokens (from BotFather)
- Slack app + bot tokens (xapp-... / xoxb-...)
- Google API key (YouTube Data API)
- GitHub PAT (ghp_...)
- Render API key (rnd_...)

===============================================
