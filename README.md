# 🦅 OpenClaw Empire

Multi-platform bot swarm + AI builder + multi-cloud deployment.

## Architecture

```
GitHub → Render (Primary) + Oracle Cloud (Worker)
              ↓
    Discord + 3×Telegram + Slack bots
              ↓
        Empire Builder (Claude API)
```

## Quick Start

### 1. Local Development (Codespaces)
Open this repo in GitHub Codespaces — Claude Code + all deps are pre-installed.

### 2. Deploy to Render
```bash
# Already connected to srv-d978fh6puehc73fkq60g
# Push to main → auto-deploys
```

### 3. Deploy to Oracle Cloud
```bash
# On your OCI VM:
curl -fsSL https://raw.githubusercontent.com/d74117157-create/openclaw-bot/main/scripts/oci-setup.sh | bash
```

Then add these GitHub Secrets:
- `OCI_HOST` — your VM public IP
- `OCI_SSH_KEY` — your private SSH key
- `RENDER_DEPLOY_HOOK` — your Render deploy hook URL

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API access |
| `DISCORD_TOKEN` | Discord bot token |
| `TELEGRAM_BOT1_TOKEN` | Telegram Bot 1 |
| `TELEGRAM_BOT2_TOKEN` | Telegram Bot 2 |
| `TELEGRAM_BOT3_TOKEN` | Telegram Bot 3 (Super) |
| `SLACK_BOT_TOKEN` | Slack Bot Token |
| `SLACK_APP_TOKEN` | Slack App Token |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Status |
| `/health` | GET | Health check |
| `/empire/status` | GET | Full mesh status |
| `/empire/build` | POST | Clone repo + build with Claude |

## Bot Commands

**Discord:**
- `!empire` — Status
- `!build <repo_url> <prompt>` — Clone and generate code

**Telegram:**
- `/empire` — Status

**Slack:**
- Mention "empire" — Status

## Empire Builder

The builder agent clones any GitHub repo, feeds key files to Claude, and generates new Python modules:

```python
from agents.builder import EmpireBuilder

builder = EmpireBuilder()
output = builder.clone_and_analyze(
    "https://github.com/some/repo",
    "Build me a webhook handler like this repo's architecture"
)
builder.save_build(output)
```

## License
MIT
