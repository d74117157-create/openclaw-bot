"""OpenClaw unified launcher - starts whichever bots have tokens configured."""

import os
import sys
import logging
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("openclaw")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def run_discord():
    """Start the Discord bot (blocking)."""
    from gateway.bot import bot
    import kernel
    kernel.init_kernel()
    logger.info("Starting Discord bot...")
    bot.run(DISCORD_TOKEN)


def run_telegram():
    """Start the Telegram bot (blocking)."""
    from gateway.telegram_bot import run_telegram as _run_tg
    _run_tg()


def main():
    has_discord = bool(DISCORD_TOKEN)
    has_telegram = bool(TELEGRAM_TOKEN)

    if not has_discord and not has_telegram:
        logger.critical("No bot tokens configured. Set DISCORD_TOKEN and/or TELEGRAM_TOKEN.")
        sys.exit(1)

    if has_discord and has_telegram:
        logger.info("Both Discord and Telegram tokens found - starting both bots.")
        tg_thread = threading.Thread(target=run_telegram, daemon=True)
        tg_thread.start()
        run_discord()

    elif has_telegram:
        logger.info("Telegram token found - starting Telegram bot.")
        run_telegram()

    elif has_discord:
        logger.info("Discord token found - starting Discord bot.")
        run_discord()


if __name__ == "__main__":
    main()
