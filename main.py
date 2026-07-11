"""OpenClaw Empire - Multi-platform bot swarm with AI agents."""
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from empire.mesh import EmpireMesh
from agents.builder import EmpireBuilder

# ── Config ─────────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
TELEGRAM_BOT1 = os.environ.get("TELEGRAM_BOT1_TOKEN", "")
TELEGRAM_BOT2 = os.environ.get("TELEGRAM_BOT2_TOKEN", "")
TELEGRAM_BOT3 = os.environ.get("TELEGRAM_BOT3_TOKEN", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[EMPIRE] OpenClaw Empire initializing...")
    app.state.mesh = EmpireMesh()
    app.state.builder = EmpireBuilder(api_key=ANTHROPIC_KEY)

    # Start background tasks
    asyncio.create_task(health_loop(app))

    yield

    print("[EMPIRE] Shutting down...")

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
app = FastAPI(title="OpenClaw Empire", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "OpenClaw Empire Online", "version": "2.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "node": "render-primary"}

@app.get("/empire/status")
async def empire_status():
    """Full empire mesh status."""
    return {
        "nodes": app.state.mesh.node_status,
        "last_check": app.state.mesh.last_check
    }

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

# ── Bot Starters (Import and start when tokens are present) ─────────

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
            await ctx.send("🦅 **OpenClaw Empire** is online. Use `!build <repo> <prompt>` to generate code.")

        @bot.command()
        async def build(ctx, repo_url: str, *, prompt: str):
            await ctx.send(f"🔨 Cloning `{repo_url}` and building...")
            try:
                result = app.state.builder.clone_and_analyze(repo_url, prompt)
                saved = app.state.builder.save_build(result)
                await ctx.send(f"✅ Built! Generated files: {', '.join(saved)}")
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

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
            await update.message.reply_text("🦅 OpenClaw Empire Online")

        for i, token in enumerate(tokens):
            app_tg = Application.builder().token(token).build()
            app_tg.add_handler(CommandHandler("empire", empire_cmd))
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
            await say("🦅 OpenClaw Empire is online!")

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
