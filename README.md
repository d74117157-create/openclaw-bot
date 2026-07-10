# OpenClaw - Autonomous AI Command Center

Discord-controlled multi-agent swarm OS with GitHub automation, Slack coordination, and Railway deployment.

## Architecture

Discord commands flow into the MAIN BRAIN (gateway/bot.py) which orchestrates agents via Groq LLM.
Results are cross-posted to Slack and GitHub issues are auto-created.

## Files

openclaw-bot/
- gateway/bot.py - Discord MAIN BRAIN (all slash commands)
- gateway/slack_bot.py - Slack gateway (Socket Mode)
- worker/ai_worker.py - Core AI engine (Groq LLM, 9 agent personas)
- worker/task_router.py - Smart task router
- worker/executor.py - Agent execution pipeline
- worker/github_agent.py - GitHub automation agent
- worker/browser_worker.py - Playwright browser agent
- worker/slack_reporter.py - Slack reporting
- worker/self_test.py - QA validation harness
- worker/agents/ - 7 specialist agents (coder, reviewer, qa, ops, research, growth, memory_agent)
- memory/__init__.py - SQLite persistent memory
- tests/test_memory.py - Unit tests
- .github/workflows/deploy.yml - CI/CD pipeline
- bot_factory.py - Bot lifecycle manager
- kernel.py - GitHub API kernel
- main.py - Entry point
- Procfile - Railway process definition
- Dockerfile - Container definition
- railway.toml - Railway service config
- requirements.txt - Python dependencies
- .env.example - Environment variable template

## Discord Slash Commands

- /create-task <task> - MAIN BRAIN auto-plans and executes with full swarm
- /swarm <agents> <task> - Manually pick agents: coder,ops,qa
- /deploy <service> - OPS agent generates Railway deployment plan
- /github <action> - GitHub automation (PRs, branches, issues, Actions)
- /status - Swarm status: tasks, agents, deployments
- /fix <problem> - Diagnose and fix a system via Research+Coder+QA
- /review <code/PR> - REVIEWER agent audit
- /optimize <target> - Research+Coder+OPS optimization pipeline
- /monitor <service> - OPS monitoring plan
- /rebuild <service> - Full 6-agent rebuild pipeline
- /scale <service> <up/down> - OPS scaling plan
- /stop - Emergency stop + Slack alert
- /resume - Resume operations
- /agents - List all swarm agents

## Setup

1. Clone and configure:
   git clone https://github.com/d74117157-create/openclaw-bot
   cd openclaw-bot
   cp .env.example .env

2. Environment Variables:
   - DISCORD_TOKEN - Discord Developer Portal, Bot, Token
   - SLACK_BOT_TOKEN - Slack API, OAuth & Permissions
   - SLACK_APP_TOKEN - Slack API, App-Level Tokens (Socket Mode)
   - SLACK_CHANNEL - Your Slack channel name (e.g. openclaw-ops)
   - GROQ_API_KEY - console.groq.com
   - GITHUB_TOKEN - GitHub Settings, Developer settings, PAT
   - GITHUB_REPO - d74117157-create/openclaw-bot
   - RAILWAY_TOKEN - Railway dashboard, Account, Tokens

3. GitHub Secrets (for CI/CD):
   Add RAILWAY_TOKEN and SLACK_WEBHOOK_URL in GitHub Settings, Secrets and variables, Actions.

4. Railway Deployment:
   npm install -g @railway/cli
   railway login
   railway link
   railway up

5. Local Development:
   pip install -r requirements.txt
   python gateway/bot.py
   python gateway/slack_bot.py

## Agents

- ORCHESTRATOR - Decomposes tasks into parallel agent DAGs
- CODER - Builds bots, APIs, scripts, integrations
- REVIEWER - Code/architecture/PR/security audits
- QA - Test plans, validation, approval gates
- OPS - Railway/Docker/scaling/monitoring
- RESEARCH - APIs, tools, integration patterns
- GROWTH - Funnels, engagement, Discord/Slack automation
- MEMORY - Tracks decisions, failures, optimization history
- GITHUB - Repos, branches, PRs, issues, Actions

## Powered by

- Groq (llama3-70b-8192) - AI inference
- discord.py 2.x - Discord gateway
- slack-bolt - Slack Socket Mode
- Railway - Deployment and hosting
- GitHub Actions - CI/CD
- SQLite - Persistent swarm memory
