# OpenClaw Swarm

> **Better than Viktor.** Multi-platform AI agent system. Self-hosted. Open source. Yours.

## Why OpenClaw > Viktor

| Feature | Viktor ($75M VC) | OpenClaw (You) |
|---------|------------------|----------------|
| **Platforms** | Slack only | Discord + Telegram + Slack + Web API |
| **Agents** | Single monolithic | 6 specialized swarm agents |
| **Code** | Closed source | 100% open source |
| **Data** | Their cloud | Your infrastructure |
| **Cost** | $30-50/user/mo | Free (hosting only) |
| **Deploy** | They control it | You control everything |
| **Telegram** | No | Yes |
| **Web API** | No | Full REST API |
| **GitHub Integration** | Limited | Full CI/CD |

## Architecture

```
┌─────────────────────────────────────────┐
│         OpenClaw Swarm Kernel           │
├─────────────────────────────────────────┤
│  Discord  │  Telegram  │  Slack │ Web │
│  (Gateway)│  (Gateway) │(Gateway)│ API│
├─────────────────────────────────────────┤
│      Redis Message Bus + Memory         │
├─────────────────────────────────────────┤
│  Coder │ Researcher │ Ops │ Growth │ QA │
│  Agent │   Agent    │Agent│ Agent  │Agent│
├─────────────────────────────────────────┤
│        Groq LLM (Llama 3/Mixtral)       │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/d74117157-create/openclaw-bot.git
cd openclaw-bot
cp .env.example .env
# Edit .env with your tokens
```

### 2. Local Development
```bash
pip install -r requirements.txt
python main.py
```

### 3. Deploy to Render
```bash
# Push to GitHub, then:
# Render Dashboard → Manual Deploy → Deploy latest commit
```

## Commands

### Discord
- `/ask <question>` — Ask the swarm anything
- `/agents` — List active agents
- `/status` — System status
- `/deploy <repo> <branch>` — Deploy code

### Telegram
- `/ask <question>` — Ask the swarm
- `/agents` — List agents
- `/status` — System status
- `/deploy <repo> [branch]` — Deploy

### Slack
- `/openclaw <question>` — Ask the swarm

### Web API
- `POST /api/v1/ask` — Submit task
- `GET /api/v1/status` — System status
- `GET /api/v1/agents` — List agents
- `POST /webhook/github` — GitHub webhooks

## Agents

| Agent | Specialty | What It Does |
|-------|-----------|--------------|
| **Orchestrator** | Routing | Classifies intent, assigns tasks |
| **Coder** | Software | Writes, reviews, deploys code |
| **Researcher** | Analysis | Web search, data analysis, reports |
| **Ops** | Infrastructure | CI/CD, Docker, monitoring |
| **Growth** | Marketing | SEO, social media, content |
| **QA** | Quality | Testing, bug hunting, audits |

## Environment Variables

See `.env.example` for all required and optional variables.

## License

MIT — Do whatever you want. It's yours.
