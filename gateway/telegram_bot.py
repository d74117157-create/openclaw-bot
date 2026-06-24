#!/usr/bin/env python3
"""Telegram Gateway — OpenClaw Swarm interface for Telegram

SUPERIOR TO VIKTOR: Viktor has NO Telegram support. OpenClaw does.

Features:
- Inline commands (/ask, /agents, /status, /deploy)
- Group chat support with @botname mentions
- Reply threading
- File upload/download for code sharing
- Voice message transcription (future)
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
except ImportError:
    logging.warning("python-telegram-bot not installed. Telegram gateway disabled.")
    Application = None

from memory import get_redis, push_task
from worker.slack_reporter import SlackReporter

logger = logging.getLogger("telegram_gateway")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


class TelegramGateway:
    """Telegram bot interface for the OpenClaw swarm."""

    def __init__(self, swarm):
        self.swarm = swarm
        self.swarm.gateways["telegram"] = self
        self.app = None
        self.slack = SlackReporter()

        if not TELEGRAM_TOKEN:
            logger.error("TELEGRAM_TOKEN not set")
            return

        if Application is None:
            logger.error("python-telegram-bot not installed")
            return

        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self._register_handlers()

    def _register_handlers(self):
        """Register Telegram command handlers."""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("ask", self.cmd_ask))
        self.app.add_handler(CommandHandler("agents", self.cmd_agents))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("deploy", self.cmd_deploy))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_message))
        self.app.add_handler(CallbackQueryHandler(self.on_callback))

    async def start(self):
        """Start the Telegram bot."""
        if not self.app:
            logger.warning("Telegram app not initialized")
            return

        logger.info("Telegram gateway starting polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

        # Keep running
        while True:
            await asyncio.sleep(60)

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Telegram chat."""
        try:
            if task_id:
                content = "Task `%s` complete:\n\n%s" % (task_id, content)

            # Telegram has 4096 char limit
            if len(content) > 4000:
                content = content[:4000] + "\n\n... (truncated)"

            await self.app.bot.send_message(
                chat_id=int(channel_id),
                text=content,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("Telegram send failed: %s", e)

    # ─── Command Handlers ──────────────────────────────────────────────────────

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome = (
            "*OpenClaw Swarm* — Your AI Agent Army\n"
            "\n"
            "Better than Viktor because:\n"
            "• Multi-platform (Discord, Telegram, Slack)\n"
            "• Multi-agent swarm (Coder, Researcher, Ops, Growth, QA)\n"
            "• Self-hosted — you own your data\n"
            "• Open source — customize everything\n"
            "\n"
            "Commands:\n"
            "/ask <question> — Ask anything\n"
            "/agents — List active agents\n"
            "/status — System status\n"
            "/deploy <repo> <branch> — Deploy code\n"
            "/help — Show this help"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")

    async def cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command."""
        question = " ".join(context.args)
        if not question:
            await update.message.reply_text("Usage: /ask <your question>")
            return

        task_id = await self.swarm.route_message(
            platform="telegram",
            user_id=str(update.effective_user.id),
            username=update.effective_user.username or "unknown",
            message=question,
            channel_id=str(update.effective_chat.id),
        )

        await update.message.reply_text(
            "Task queued: `%s`\nI'll reply here when done." % task_id,
            parse_mode="Markdown"
        )

    async def cmd_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /agents command."""
        agents_text = "*OpenClaw Swarm Agents*\n\n"
        for name, agent in self.swarm.agents.items():
            status = "online" if agent.is_ready() else "booting"
            agents_text += "• *%s*: `%s` (%s)\n" % (name.upper(), status, agent.agent_type)

        await update.message.reply_text(agents_text, parse_mode="Markdown")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        stats = self.swarm.get_stats()
        status_text = (
            "*OpenClaw Status*\n"
            "\n"
            "Queue: %s\n"
            "Completed: %s\n"
            "Failed: %s\n"
            "Uptime: %ds\n"
            "Platforms: %s"
        ) % (
            stats["queue_length"],
            stats["tasks_completed"],
            stats["tasks_failed"],
            int(stats["uptime_seconds"]),
            ", ".join(stats["gateways"])
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def cmd_deploy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deploy command."""
        if not context.args:
            await update.message.reply_text("Usage: /deploy <repo> [branch]")
            return

        repo = context.args[0]
        branch = context.args[1] if len(context.args) > 1 else "main"

        task_id = await self.swarm.route_message(
            platform="telegram",
            user_id=str(update.effective_user.id),
            username=update.effective_user.username or "unknown",
            message="deploy %s %s" % (repo, branch),
            channel_id=str(update.effective_chat.id),
        )

        await update.message.reply_text("Deploy queued: `%s`" % task_id, parse_mode="Markdown")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.cmd_start(update, context)

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages."""
        if not update.message or not update.message.text:
            return

        # Only respond to mentions in groups, always in DMs
        if update.effective_chat.type in ["group", "supergroup"]:
            if not update.message.text.startswith("@") and f"@{context.bot.username}" not in update.message.text:
                return

        task_id = await self.swarm.route_message(
            platform="telegram",
            user_id=str(update.effective_user.id),
            username=update.effective_user.username or "unknown",
            message=update.message.text,
            channel_id=str(update.effective_chat.id),
        )

        await update.message.reply_text(
            "Processing... Task: `%s`" % task_id,
            parse_mode="Markdown"
        )

    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()

        # Handle agent selection, deployment confirmation, etc.
        await query.edit_message_text(text="Selected: %s" % query.data)
