"""OpenClaw Empire - Multi-platform bot swarm + AI builder + 24/7 Trading Engine."""
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

from empire.mesh import EmpireMesh
from empire.trading import (
    EmpireTradingOrchestrator, RiskConfig, TradingMode,
    TradeSignal, Position
)
from agents.builder import EmpireBuilder

# ── Config ─────────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
TELEGRAM_BOT1 = os.environ.get("TELEGRAM_BOT1_TOKEN", "")
TELEGRAM_BOT2 = os.environ.get("TELEGRAM_BOT2_TOKEN", "")
TELEGRAM_BOT3 = os.environ.get("TELEGRAM_BOT3_TOKEN", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Trading config from env
TRADING_MODE = os.environ.get("TRADING_MODE", "paper")
MAX_DAILY_LOSS = float(os.environ.get("MAX_DAILY_LOSS_PCT", "5.0"))
MAX_POSITION = float(os.environ.get("MAX_POSITION_PCT", "20.0"))
STOP_LOSS = float(os.environ.get("STOP_LOSS_PCT", "3.0"))
TAKE_PROFIT = float(os.environ.get("TAKE_PROFIT_PCT", "6.0"))

# ── Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[EMPIRE] OpenClaw Empire initializing...")
    app.state.mesh = EmpireMesh()
    app.state.builder = EmpireBuilder(api_key=ANTHROPIC_KEY)

    # Initialize trading engine
    app.state.trading = EmpireTradingOrchestrator()
    app.state.trading.risk.config.max_daily_loss_pct = MAX_DAILY_LOSS
    app.state.trading.risk.config.max_position_pct = MAX_POSITION
    app.state.trading.risk.config.stop_loss_pct = STOP_LOSS
    app.state.trading.risk.config.take_profit_pct = TAKE_PROFIT

    try:
        await app.state.trading.initialize()
        asyncio.create_task(app.state.trading.scan_and_trade())
        print(f"[EMPIRE] Trading engine started in {TRADING_MODE} mode")
    except Exception as e:
        print(f"[EMPIRE] Trading init failed: {e}")

    # Start background tasks
    asyncio.create_task(health_loop(app))

    yield

    print("[EMPIRE] Shutting down...")
    await app.state.trading.shutdown()

async def health_loop(app: FastAPI):
    """Background health check every 30 seconds."""
    while True:
        try:
            await app.state.mesh.health_check()
            print(app.state.mesh.get_summary())
        except Exception as e:
            print(f"[EMPIRE] Health check error: {e}")
        await asyncio.sleep(30)

# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(title="OpenClaw Empire - Trading God Edition", lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "OpenClaw Empire Online",
        "version": "3.0.0-Trading",
        "mode": TRADING_MODE,
        "features": ["bots", "builder", "trading", "mesh"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "node": "render-primary", "trading": TRADING_MODE}

# ── Empire Mesh ────────────────────────────────────────────────────

@app.get("/empire/status")
async def empire_status():
    """Full empire mesh status."""
    return {
        "nodes": app.state.mesh.node_status,
        "last_check": app.state.mesh.last_check
    }

# ── Builder ──────────────────────────────────────────────────────────

@app.post("/empire/build")
async def empire_build(repo_url: str, prompt: str):
    """Clone a repo and build something new with Claude."""
    if not ANTHROPIC_KEY:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not set"}, status_code=500)

    try:
        result = app.state.builder.clone_and_analyze(repo_url, prompt)
        saved = app.state.builder.save_build(result)
        return {
            "status": "built",
            "repo": repo_url,
            "generated_files": saved,
            "claude_output_preview": result[:500] + "..." if len(result) > 500 else result
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ── Trading Engine ─────────────────────────────────────────────────

@app.get("/trading/status")
async def trading_status():
    """Live trading engine status."""
    return app.state.trading.get_status()

@app.get("/trading/positions")
async def trading_positions():
    """All positions (open and closed)."""
    positions = []
    for p in app.state.trading.positions.values():
        positions.append({
            "id": p.id,
            "pair": p.pair,
            "direction": p.direction,
            "entry": p.entry_price,
            "size": p.size,
            "stop_loss": p.stop_loss,
            "take_profit": p.take_profit,
            "pnl_pct": p.pnl_pct,
            "status": p.status,
            "opened_at": p.opened_at
        })
    return {"positions": positions, "count": len(positions)}

@app.post("/trading/signal")
async def trading_signal(pair: str, direction: str = "long", confidence: float = 0.7):
    """Manually submit a trade signal (for testing)."""
    signal = TradeSignal(
        pair=pair,
        direction=direction,
        entry_price=0.0,
        stop_loss=0.0,
        take_profit=0.0,
        confidence=confidence,
        strategy="manual",
        timestamp="",
        reason="Manual signal via API"
    )
    return {"signal": signal.__dict__, "status": "submitted"}

@app.post("/trading/stop")
async def trading_stop():
    """Emergency stop all trading."""
    app.state.trading.running = False
    return {"status": "STOPPED", "message": "All trading halted. Positions remain open — close manually."}

@app.post("/trading/start")
async def trading_start():
    """Resume trading."""
    app.state.trading.running = True
    asyncio.create_task(app.state.trading.scan_and_trade())
    return {"status": "STARTED", "mode": TRADING_MODE}

@app.get("/trading/risk")
async def trading_risk():
    """Current risk boundaries and status."""
    risk = app.state.trading.risk
    return {
        "daily_pnl": risk.daily_pnl,
        "daily_limit": risk.config.max_daily_loss_pct,
        "positions_open": sum(1 for p in risk.positions.values() if p.status == "open"),
        "max_positions": risk.config.max_open_positions,
        "hourly_trades": risk.trade_count_hour,
        "max_hourly": risk.config.max_trades_per_hour,
        "blacklist": risk.config.blacklist
    }

@app.post("/trading/claude-analyze")
async def trading_claude_analyze():
    """Ask Claude to analyze current portfolio."""
    try:
        balance = await app.state.trading.exchange.get_balance()
        open_positions = [p for p in app.state.trading.positions.values() if p.status == "open"]
        analysis = await app.state.trading.claude.analyze_portfolio(open_positions, balance)
        return {"analysis": analysis}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ── Bot Starters ────────────────────────────────────────────────────

async def start_discord():
    """Start Discord bot if token is available."""
    if not DISCORD_TOKEN:
        print("[DISCORD] No token, skipping.")
        return
    try:
        import discord
        from discord.ext import commands

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(f"[DISCORD] Logged in as {bot.user}")

        @bot.command()
        async def empire(ctx):
            await ctx.send("🦅 **OpenClaw Empire** is online. Trading mode: `{TRADING_MODE}`")

        @bot.command()
        async def build(ctx, repo_url: str, *, prompt: str):
            await ctx.send(f"🔨 Cloning `{repo_url}` and building...")
            try:
                result = app.state.builder.clone_and_analyze(repo_url, prompt)
                saved = app.state.builder.save_build(result)
                await ctx.send(f"✅ Built! Files: {', '.join(saved)}")
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

        @bot.command()
        async def trade(ctx):
            """Trading status command."""
            status = app.state.trading.get_status()
            msg = f"""📈 **Trading Status**
Mode: `{status['mode']}`
Running: `{status['running']}`
Open Positions: `{status['open_positions']}`
Daily P&L: `{status['daily_pnl']:.2f}%`
Total P&L: `{status['total_pnl']:.2f}%`
Watchlist: `{', '.join(status['watchlist'])}`"""
            await ctx.send(msg)

        @bot.command()
        async def positions(ctx):
            """Show open positions."""
            pos_list = [p for p in app.state.trading.positions.values() if p.status == "open"]
            if not pos_list:
                await ctx.send("📭 No open positions.")
                return
            msg = "📊 **Open Positions:**\n"
            for p in pos_list[:10]:
                emoji = "🟢" if p.pnl_pct > 0 else "🔴"
                msg += f"{emoji} `{p.pair}` {p.direction.upper()} | P&L: `{p.pnl_pct:.2f}%`\n"
            await ctx.send(msg)

        @bot.command()
        async def stop(ctx):
            """Emergency stop trading."""
            app.state.trading.running = False
            await ctx.send("🛑 **TRADING HALTED** — All new signals blocked. Monitor existing positions.")

        @bot.command()
        async def start(ctx):
            """Resume trading."""
            app.state.trading.running = True
            asyncio.create_task(app.state.trading.scan_and_trade())
            await ctx.send("▶️ **TRADING RESUMED** — Scanning markets...")

        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"[DISCORD] Error: {e}")

async def start_telegram():
    """Start Telegram bots if tokens are available."""
    tokens = [t for t in [TELEGRAM_BOT1, TELEGRAM_BOT2, TELEGRAM_BOT3] if t]
    if not tokens:
        print("[TELEGRAM] No tokens, skipping.")
        return

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes

        async def empire_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🦅 OpenClaw Empire Online\nTrading: " + TRADING_MODE)

        async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            status = app.state.trading.get_status()
            msg = f"📈 Mode: {status['mode']}\nRunning: {status['running']}\nPositions: {status['open_positions']}\nDaily P&L: {status['daily_pnl']:.2f}%"
            await update.message.reply_text(msg)

        async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            app.state.trading.running = False
            await update.message.reply_text("🛑 TRADING HALTED")

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            app.state.trading.running = True
            asyncio.create_task(app.state.trading.scan_and_trade())
            await update.message.reply_text("▶️ TRADING RESUMED")

        for i, token in enumerate(tokens):
            app_tg = Application.builder().token(token).build()
            app_tg.add_handler(CommandHandler("empire", empire_cmd))
            app_tg.add_handler(CommandHandler("trade", trade_cmd))
            app_tg.add_handler(CommandHandler("stop", stop_cmd))
            app_tg.add_handler(CommandHandler("start", start_cmd))
            asyncio.create_task(app_tg.run_polling())
            print(f"[TELEGRAM] Bot {i+1} started")

    except Exception as e:
        print(f"[TELEGRAM] Error: {e}")

async def start_slack():
    """Start Slack bot if tokens are available."""
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("[SLACK] Missing tokens, skipping.")
        return

    try:
        from slack_bolt.async_app import AsyncApp
        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

        slack_app = AsyncApp(token=SLACK_BOT_TOKEN)

        @slack_app.message("empire")
        async def empire_msg(message, say):
            await say("🦅 OpenClaw Empire is online!\nTrading mode: " + TRADING_MODE)

        @slack_app.message("trade status")
        async def trade_status_msg(message, say):
            status = app.state.trading.get_status()
            await say(f"📈 Trading: {status['mode']} | Positions: {status['open_positions']} | Daily P&L: {status['daily_pnl']:.2f}%")

        @slack_app.message("stop trading")
        async def stop_trade_msg(message, say):
            app.state.trading.running = False
            await say("🛑 Trading halted. Existing positions remain open.")

        handler = AsyncSocketModeHandler(slack_app, SLACK_APP_TOKEN)
        asyncio.create_task(handler.start_async())
        print("[SLACK] Bot started")

    except Exception as e:
        print(f"[SLACK] Error: {e}")

# ── Entry Point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    # Start all bots in background
    asyncio.create_task(start_discord())
    asyncio.create_task(start_telegram())
    asyncio.create_task(start_slack())

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
