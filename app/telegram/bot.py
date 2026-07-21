"""OpenClaw Empire — Telegram Command Center"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("openclaw.telegram")

class TelegramCommandCenter:
    """Telegram bot with empire management commands."""

    COMMANDS = {
        "/status": "Show system status",
        "/tasks": "List active tasks",
        "/build": "Trigger a build/deploy",
        "/logs": "Show recent logs",
        "/restart": "Restart the empire",
        "/revenue": "Show revenue stats",
        "/chess": "Play a chess move",
        "/help": "Show all commands"
    }

    def __init__(self):
        self.tokens = [
            os.environ.get("TELEGRAM_BOT1_TOKEN"),
            os.environ.get("TELEGRAM_BOT2_TOKEN"),
            os.environ.get("TELEGRAM_BOT3_TOKEN"),
        ]
        self.enabled = any(self.tokens)
        self._polling = False
        self._apps = []

        if self.enabled:
            logger.info(f"[Telegram] {sum(1 for t in self.tokens if t)} bot(s) configured")
        else:
            logger.warning("[Telegram] No tokens set — Telegram disabled")

    def is_enabled(self) -> bool:
        return self.enabled

    def is_polling(self) -> bool:
        return self._polling

    async def start(self):
        """Start Telegram bots with duplicate polling protection."""
        if self._polling:
            logger.warning("[Telegram] Already polling — skipping duplicate start")
            return

        if not self.enabled:
            logger.info("[Telegram] Disabled — not starting")
            return

        try:
            from telegram.ext import ApplicationBuilder

            apps = []
            for i, token in enumerate(self.tokens):
                if not token:
                    continue
                app = ApplicationBuilder().token(token).build()
                app.add_handler(self._get_handlers())
                apps.append(app)

            if not apps:
                return

            self._apps = apps
            self._polling = True
            logger.info(f"[Telegram] {len(apps)} bot(s) starting polling")

            # Run all bots
            await asyncio.gather(*[a.initialize() for a in apps])
            await asyncio.gather(*[a.start() for a in apps])

            # Keep alive
            while self._polling:
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("[Telegram] Polling cancelled")
            raise
        except Exception as e:
            logger.error(f"[Telegram] Start failed: {e}")
            self._polling = False

    async def stop(self):
        """Stop all Telegram bots gracefully."""
        self._polling = False
        for app in self._apps:
            try:
                await app.stop()
            except Exception as e:
                logger.warning(f"[Telegram] Stop error: {e}")
        self._apps = []
        logger.info("[Telegram] All bots stopped")

    def _get_handlers(self):
        """Get command handlers."""
        from telegram.ext import CommandHandler
        return CommandHandler("start", self._cmd_help)

    async def _cmd_help(self, update, context):
        """Handle /help command."""
        lines = ["🦅 *OpenClaw Empire Commands*"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} — {desc}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def send_message(self, bot_index: int, chat_id: str, text: str) -> bool:
        """Send message via Telegram bot."""
        if not self.enabled or bot_index >= len(self.tokens) or not self.tokens[bot_index]:
            return False
        logger.info(f"[Telegram] Would send to {chat_id}: {text[:50]}...")
        return True
