"""OpenClaw Telegram gateway — manages 3 bots via python-telegram-bot."""
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from memory import init_db, save_task, update_task
from worker.ai_worker import process_task, AGENT_PERSONAS
from health import update_state

load_dotenv()
logger = logging.getLogger("openclaw.telegram")

TOKENS = [
    os.environ.get("TELEGRAM_BOT1_TOKEN", ""),
    os.environ.get("TELEGRAM_BOT2_TOKEN", ""),
    os.environ.get("TELEGRAM_BOT3_TOKEN", ""),
]
BOT_NAMES = ["OpenClaw-1", "OpenClaw-2", "OpenClaw-Super"]


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, agent: str = "orchestrator"):
    text = update.message.text if update.message else ""
    user = update.effective_user.username or update.effective_user.id if update.effective_user else "unknown"
    tid = save_task(text, f"telegram-{agent}")
    try:
        result = process_task(text, agent)
        update_task(tid, result, "done")
        await update.message.reply_text(result[:4000])
    except Exception as exc:
        update_task(tid, str(exc), "failed")
        await update.message.reply_text(f"Error: {exc}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 OpenClaw Superswarm online. Send any task or use /swarm <task>.")


async def cmd_swarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = " ".join(context.args) if context.args else "No task provided"
    await _handle_message(update, context, agent="orchestrator")


async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"• {k} — {v[:60]}..." for k, v in AGENT_PERSONAS.items()]
    await update.message.reply_text("🤖 **Agents:**\n" + "\n".join(lines))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from memory import get_stats
    stats = get_stats()
    await update.message.reply_text(f"📊 Tasks: {stats['total']} | Done: {stats['done']} | Failed: {stats['failed']}")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_message(update, context)


def build_app(token: str, name: str):
    if not token:
        return None
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("swarm", cmd_swarm))
    app.add_handler(CommandHandler("agents", cmd_agents))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    logger.info(f"[Telegram] {name} configured")
    return app


async def run_telegram():
    apps = []
    for token, name in zip(TOKENS, BOT_NAMES):
        app = build_app(token, name)
        if app:
            apps.append((app, name))
    if not apps:
        logger.warning("No Telegram tokens set — Telegram bots disabled")
        update_state("telegram", "disabled")
        return
    init_db()
    update_state("telegram", "polling")
    # Run all bots concurrently
    await asyncio.gather(*[a.initialize() for a, _ in apps])
    await asyncio.gather(*[a.start() for a, _ in apps])
    logger.info(f"[Telegram] {len(apps)} bot(s) polling")
    # Keep alive
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        for a, _ in apps:
            await a.stop()
        raise
