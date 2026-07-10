# 🐝 OpenClaw Superswarm

Multi-agent bot swarm with Discord + 3× Telegram + Slack + AI orchestration.
**Dual-deployment:** Oracle VM (primary) + Render (fallback).

## Quick Start

```bash
docker compose up -d
curl http://localhost:8000/health
```

## Architecture

- **FastAPI** health server + swarm API
- **Discord Bot** — auto-reconnect, `!swarm` / `!agent` commands
- **Telegram Manager** — 3 bots, `/swarm` / `/agent` commands
- **Slack Bot** — Socket Mode, `/swarm` / `/agent` slash commands
- **6 AI Agents** — Coder, Researcher, Ops, Growth, QA, Orchestrator
- **Tool Registry** — `defineTool` pattern for dynamic tool calling

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `deploy.yml` | Push to `main` | Deploy to Oracle VM (primary) |
| `setup-oracle-vm.yml` | Manual | One-click provision Oracle VM |
| `deploy-to-render.yml` | Push to `main` | Deploy to Render (backup) |

## License
MIT
