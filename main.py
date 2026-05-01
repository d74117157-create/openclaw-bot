"""OpenClaw unified launcher - starts whichever bots have tokens configured."""

import os
import sys
import logging
import threading
import asyncio

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("openclaw")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")


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


def run_slack():
        """Start the Slack bot in its own asyncio loop."""
        from gateway.slack_bot import start_slack_bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Starting Slack bot...")
        loop.run_until_complete(start_slack_bot())


def main():
        threads = []
        has_discord = bool(DISCORD_TOKEN)
        has_telegram = bool(TELEGRAM_TOKEN)
        has_slack = bool(SLACK_BOT_TOKEN and SLACK_APP_TOKEN)

    if not has_discord and not has_telegram and not has_slack:
                logger.critical("No bot tokens configured. Set DISCORD_TOKEN, TELEGRAM_TOKEN, and/or SLACK_BOT_TOKEN + SLACK_APP_TOKEN.")
                sys.exit(1)

    if has_telegram:
                logger.info("Telegram token found - starting Telegram bot.")
                t = threading.Thread(target=run_telegram, daemon=True)
                t.start()
                threads.append(t)

    if has_slack:
                logger.info("Slack tokens found - starting Slack bot.")
                t = threading.Thread(target=run_slack, daemon=True)
                t.start()
                threads.append(t)

    if has_discord:
                logger.info("Discord token found - starting Discord bot.")
                run_discord()
else:
            for t in threads:
                            t.join()


if __name__ == "__main__":
        main()
