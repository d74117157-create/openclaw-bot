# 🦅 OpenClaw Empire v3.1

Unified AI Command Center — Multi-agent swarm for digital empire automation.

## Architecture

```
openclaw-empire/
├── app/
│   ├── core/          # Config, logging
│   ├── brain/         # AI client with fallback
│   ├── agents/        # 10 specialist agents
│   ├── database/      # SQLAlchemy models
│   ├── integrations/  # Platform gateways
│   ├── workers/       # Background tasks
│   ├── dashboard/     # Web UI
│   └── main.py        # FastAPI entry point
├── tests/             # Test suite
├── Dockerfile
├── render.yaml
└── requirements.txt
```

## Agents

| Agent | Role |
|-------|------|
| Viktor | Strategic Reasoning |
| Bob | Task Orchestration |
| Dave | DevOps & Deployments |
| Carla | Content & YouTube |
| Alice | Business & Revenue |
| GBaby | Growth & Marketing |
| Security | Audits & Scanning |
| Researcher | Trends & Analysis |
| Coder | Code & Automation |
| QA | Testing & Validation |

## Setup

1. Copy `.env.example` to `.env` and fill in values
2. `pip install -r requirements.txt`
3. `python app/main.py`

## API Endpoints

- `GET /health` — Health check
- `GET /ready` — Readiness with dependency status
- `GET /status` — Full system status
- `GET /agents` — List all agents
- `POST /goal` — Submit a goal

## Deployment

Render: `render.yaml` configured for auto-deploy.
