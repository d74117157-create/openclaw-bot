"""OpenClaw Superswarm — Async entry point.
Starts: FastAPI health server, Discord bot, Slack bot, 3x Telegram bots.
"""
import asyncio
import logging
import signal
import sys
import threading
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("openclaw.main")

from config import Config
from health import HealthServer, update_state
from memory import init_db, register_bot

config = Config()
config.log_status()

init_db()
register_bot("openclaw-discord", "MAIN BRAIN Discord gateway", "discord", "DISCORD_TOKEN")
register_bot("openclaw-slack", "Slack coordination gateway", "slack", "SLACK_BOT_TOKEN")
register_bot("openclaw-telegram-1", "Telegram bot 1", "telegram", "TELEGRAM_BOT1_TOKEN")
register_bot("openclaw-telegram-2", "Telegram bot 2", "telegram", "TELEGRAM_BOT2_TOKEN")
register_bot("openclaw-telegram-3", "Telegram Super bot", "telegram", "TELEGRAM_BOT3_TOKEN")


async def main():
    health = HealthServer(port=config.HEALTH_PORT)
    await health.start()

    threads = []
    tasks = []

    if config.DISCORD_TOKEN:
        try:
            from gateway.discord_bot import run_discord
            t = threading.Thread(target=run_discord, daemon=True)
            t.start()
            threads.append(t)
            logger.info("Discord thread started")
        except Exception as e:
            logger.error(f"Discord failed to start: {e}")
            update_state("discord", f"error: {e}")
    else:
        update_state("discord", "disabled")

    if config.SLACK_BOT_TOKEN and config.SLACK_APP_TOKEN:
        try:
            from gateway.slack_bot import run_slack
            slack_task = asyncio.create_task(run_slack())
            tasks.append(slack_task)
            logger.info("Slack task started")
        except Exception as e:
            logger.error(f"Slack failed to start: {e}")
            update_state("slack", f"error: {e}")
    else:
        update_state("slack", "disabled")

    if any([config.TELEGRAM_BOT1_TOKEN, config.TELEGRAM_BOT2_TOKEN, config.TELEGRAM_BOT3_TOKEN]):
        try:
            from gateway.telegram_bot import run_telegram
            telegram_task = asyncio.create_task(run_telegram())
            tasks.append(telegram_task)
            logger.info("Telegram task started")
        except Exception as e:
            logger.error(f"Telegram failed to start: {e}")
            update_state("telegram", f"error: {e}")
    else:
        update_state("telegram", "disabled")

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    logger.info("OpenClaw Superswarm running. Press Ctrl+C to stop.")
    await stop_event.wait()

    for t in tasks:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

    await health.stop()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
