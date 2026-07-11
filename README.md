# OpenClaw Superswarm v5.0

Multi-platform AI agent swarm: **Discord + Slack + 3× Telegram** bots, Groq LLM orchestration, GitHub automation, Render deployment.

## Architecture

- **gateway/discord_bot.py** — Discord MAIN BRAIN (slash commands, brain channel)
- **gateway/slack_bot.py** — Slack Socket Mode gateway
- **gateway/telegram_bot.py** — 3 Telegram bots via python-telegram-bot
- **worker/ai_worker.py** — Groq LLM engine (9 agent personas)
- **worker/task_router.py** — Smart task routing (AI + keyword fallback)
- **worker/executor.py** — Parallel execution, Slack/GitHub posting
- **worker/github_agent.py** — GitHub API automation (branches, PRs, issues, Actions)
- **worker/slack_reporter.py** — Real-time Slack updates
- **worker/self_test.py** — QA validation harness
- **worker/browser_worker.py** — Playwright browser automation
- **memory/db.py** — SQLite persistent memory
- **health.py** — FastAPI health/metrics server for Render
- **main.py** — Single async entry point

## Discord Commands

- `/create-task <agent> <task>` — Run single agent
- `/swarm <task>` — Auto-plan + full swarm execution
- `/deploy <target>` — Ops deployment plan
- `/github <action>` — GitHub automation
- `/agents` — List swarm agents
- `/status` — Task stats
- `/route <task>` — Show AI routing plan

## Telegram Commands

- `/start` — Welcome
- `/swarm <task>` — Run orchestrator
- `/agents` — List agents
- `/status` — Task stats
- Any text — Direct AI processing

## Setup

1. `cp .env.example .env` and fill tokens
2. `pip install -r requirements.txt`
3. `python main.py`

## Render Deploy

1. Connect GitHub repo to Render
2. Set `RENDER_DEPLOY_HOOK` in GitHub Secrets → auto-deploy on push
3. Health check: `GET /health` and `GET /ready`

## Environment Variables

| Variable | Platform | Required |
|----------|----------|----------|
| `DISCORD_TOKEN` | Discord | Optional |
| `TELEGRAM_BOT1_TOKEN` | Telegram | Optional |
| `TELEGRAM_BOT2_TOKEN` | Telegram | Optional |
| `TELEGRAM_BOT3_TOKEN` | Telegram | Optional |
| `SLACK_BOT_TOKEN` | Slack | Optional |
| `SLACK_APP_TOKEN` | Slack | Optional |
| `GROQ_API_KEY` | AI | **Yes** |
| `GITHUB_TOKEN` | GitHub | Optional |
| `RENDER_DEPLOY_HOOK` | CI/CD | Optional |

At least one platform token is required.
