"""OpenClaw Superswarm — Async entry point.
Starts: FastAPI health server, Discord bot, Slack bot, 3× Telegram bots.
"""
import asyncio
import logging
import signal
import sys
import threading
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging early
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

# Initialize database
init_db()
register_bot("openclaw-discord", "MAIN BRAIN Discord gateway", "discord", "DISCORD_TOKEN")
register_bot("openclaw-slack", "Slack coordination gateway", "slack", "SLACK_BOT_TOKEN")
register_bot("openclaw-telegram-1", "Telegram bot 1", "telegram", "TELEGRAM_BOT1_TOKEN")
register_bot("openclaw-telegram-2", "Telegram bot 2", "telegram", "TELEGRAM_BOT2_TOKEN")
register_bot("openclaw-telegram-3", "Telegram Super bot", "telegram", "TELEGRAM_BOT3_TOKEN")


async def main():
    health = HealthServer(port=config.HEALTH_PORT)
    await health.start()

    tasks = []

    # Discord
    if config.DISCORD_TOKEN:
        from gateway.discord_bot import run_discord
        t = threading.Thread(target=run_discord, daemon=True)
        t.start()
        tasks.append(t)
        logger.info("Discord thread started")
    else:
        update_state("discord", "disabled")

    # Slack
    if config.SLACK_BOT_TOKEN and config.SLACK_APP_TOKEN:
        from gateway.slack_bot import run_slack
        slack_task = asyncio.create_task(run_slack())
        tasks.append(slack_task)
        logger.info("Slack task started")
    else:
        update_state("slack", "disabled")

    # Telegram
    if any([config.TELEGRAM_BOT1_TOKEN, config.TELEGRAM_BOT2_TOKEN, config.TELEGRAM_BOT3_TOKEN]):
        from gateway.telegram_bot import run_telegram
        telegram_task = asyncio.create_task(run_telegram())
        tasks.append(telegram_task)
        logger.info("Telegram task started")
    else:
        update_state("telegram", "disabled")

    # Wait for shutdown signal
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass  # Windows

    logger.info("OpenClaw Superswarm running. Press Ctrl+C to stop.")
    await stop_event.wait()

    # Cleanup
    await health.stop()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
