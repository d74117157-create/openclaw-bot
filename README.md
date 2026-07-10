# 🐝 OpenClaw Superswarm v2.0

Multi-agent bot swarm with Discord + 3× Telegram + Slack + AI orchestration.
**Dual-deployment:** Oracle VM (primary) + Render (fallback).

## Architecture

```
                    ┌─────────────────┐
                    │   GitHub Push   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────────┐ ┌──────────┐ ┌──────────────┐
      │  Oracle VM   │ │  Render  │ │  Health      │
      │  (Primary)   │ │ (Backup) │ │  Monitor     │
      │  Docker      │ │  Web     │ │  /health     │
      │  Compose     │ │  Service │ │  /swarm      │
      └──────────────┘ └──────────┘ └──────────────┘
```

## Quick Start

```bash
docker compose up -d
curl http://localhost:8000/health
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Swarm status |
| `/health` | GET | Health check |
| `/health/ready` | GET | Readiness probe |
| `/health/live` | GET | Liveness probe |
| `/swarm/status` | GET | Full swarm status |
| `/swarm/reload` | POST | Hot-reload agents |

## Bot Commands

### Discord: `!swarm`, `!agent <query>`
### Telegram: `/swarm`, `/agent <query>`
### Slack: `/swarm`, `/agent <query>`

## License
MIT
