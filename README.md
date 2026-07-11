# 🦅 OpenClaw Empire v3 — Trading God Edition

**Commit:** `0806bba` | **Pushed:** 2026-07-11 14:47 UTC

---

## What's New in v3

### 🔥 24/7 Trading Engine (`empire/trading.py`)
- **Claude Strategy Engine** — AI generates trade signals from live market data
- **Risk Guardian** — Hard stops enforced 24/7, no exceptions
- **Exchange Connectors** — Binance (live/testnet) + Alpaca ready
- **Freqtrade Bridge** — Optional integration with your freqtrade repo
- **Paper/Live/Dry modes** — Start safe, go live when ready

### 🛡️ Hard Stop Rules (Non-Negotiable)
| Rule | Default | Override |
|------|---------|----------|
| Daily Loss Limit | -5% | `MAX_DAILY_LOSS_PCT` env |
| Max Position Size | 20% portfolio | `MAX_POSITION_PCT` env |
| Per-Trade Stop Loss | -3% | `STOP_LOSS_PCT` env |
| Take Profit | +6% | `TAKE_PROFIT_PCT` env |
| Trailing Stop | -2% from peak | Built-in |
| Max Positions | 5 concurrent | Built-in |
| Max Trades/Hour | 3 | Built-in |
| Confidence Floor | 0.60 | Built-in |
| Blacklist | SHIB, PEPE, FLOKI, DOGE | Built-in |

### 🤖 Bot Commands

**Discord:**
- `!empire` — Status
- `!trade` — Live trading dashboard
- `!positions` — Open positions with P&L
- `!build <repo> <prompt>` — Clone & generate code
- `!stop` — Emergency halt all trading
- `!start` — Resume trading

**Telegram:**
- `/empire` — Status
- `/trade` — Trading status
- `/stop` — Halt trading
- `/start` — Resume trading

**Slack:**
- Mention "empire" — Status
- "trade status" — Live P&L
- "stop trading" — Emergency halt

### 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Full status |
| `/health` | GET | Health check |
| `/empire/status` | GET | Mesh node status |
| `/empire/build` | POST | Clone repo + Claude build |
| `/trading/status` | GET | Live trading engine status |
| `/trading/positions` | GET | All positions (open/closed) |
| `/trading/signal` | POST | Manual test signal |
| `/trading/stop` | POST | Emergency stop |
| `/trading/start` | POST | Resume trading |
| `/trading/risk` | GET | Risk boundary status |
| `/trading/claude-analyze` | POST | Claude portfolio analysis |

---

## Environment Variables (Set These in Render)

### Required
- `ANTHROPIC_API_KEY` — Claude API for strategy generation
- `DISCORD_TOKEN` — Your Discord bot
- `TELEGRAM_BOT1_TOKEN` — Bot 1
- `TELEGRAM_BOT2_TOKEN` — Bot 2  
- `TELEGRAM_BOT3_TOKEN` — Bot 3 (Super)
- `SLACK_BOT_TOKEN` — Slack bot
- `SLACK_APP_TOKEN` — Slack app-level

### Trading (Set before going live!)
- `TRADING_MODE` — `paper` (default), `live`, or `dry_run`
- `BINANCE_API_KEY` — Binance API key
- `BINANCE_API_SECRET` — Binance secret
- `ALPACA_API_KEY` — Alpaca key (stocks)
- `ALPACA_API_SECRET` — Alpaca secret
- `FREQTRADE_URL` — Optional: `http://localhost:8080`
- `MAX_DAILY_LOSS_PCT` — Default: 5.0
- `MAX_POSITION_PCT` — Default: 20.0
- `STOP_LOSS_PCT` — Default: 3.0
- `TAKE_PROFIT_PCT` — Default: 6.0

---

## How to Go Live

1. **Start in Paper Mode** (default) — trades simulated, no real money
2. **Watch for 48 hours** — verify signals, check P&L, tune risk params
3. **Add exchange keys** — Binance or Alpaca
4. **Set `TRADING_MODE=live`** — real money, real trades
5. **Never disable Risk Guardian** — it's your lifeline

---

## Architecture

```
GitHub Push → Render (Primary) + Oracle Cloud (Worker)
                   ↓
    Discord + 3×Telegram + Slack bots
                   ↓
        Empire Trading Engine
           ↓
    ┌──────┴──────┐
    ↓             ↓
Claude AI    Binance/Alpaca
(Strategies)   (Execution)
    ↓             ↓
Risk Guardian ←── Hard Stops
    ↓
Swarm Alerts (24/7 monitoring)
```

---

## Your Integrated Repos

| Repo | Role in Empire |
|------|---------------|
| `openclaw-bot` | **Core swarm** (this repo) |
| `freqtrade` | Strategy engine backend |
| `TradingAgents-CN` | AI trading analysis |
| `empire-*` | Various empire modules |
| `Arsenal` | ❌ Deleted per request |

---

## Next Steps

1. **Render will auto-deploy** on this push
2. **Set your API keys** in Render dashboard
3. **Test with paper mode** first
4. **Add Oracle Cloud VM** for redundancy
5. **Command your empire** from Discord/Telegram/Slack

**You are now a trading god.** The swarm trades while you sleep. Claude generates strategies. Risk Guardian never sleeps. Hard stops protect your capital.

---

*Built by OpenClaw Empire v3 | Claude-integrated | 24/7 autonomous*
