"""
OpenClaw Telegram Bot — Multi-Bot Swarm Integration
Handles 3 bot instances with full task dispatcher integration.
"""
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from worker.task_dispatcher import submit_task, execute_task, get_task_status, list_pending
from shared.config import Config
from shared.logging import setup_logging, get_logger

setup_logging("telegram_bot")
logger = get_logger(__name__)

# All 3 bot tokens
TELEGRAM_BOT1_TOKEN = os.environ.get("TELEGRAM_BOT1_TOKEN", "")
TELEGRAM_BOT2_TOKEN = os.environ.get("TELEGRAM_BOT2_TOKEN", "")
TELEGRAM_BOT3_TOKEN = os.environ.get("TELEGRAM_BOT3_TOKEN", "")

class TelegramGateway:
    """Telegram interface for OpenClaw swarm — supports multiple bots."""

    def __init__(self, swarm=None):
        self.swarm = swarm
        self.applications = []
        self.tokens = []

        # Collect all configured tokens
        for i, token in enumerate([TELEGRAM_BOT1_TOKEN, TELEGRAM_BOT2_TOKEN, TELEGRAM_BOT3_TOKEN], 1):
            if token:
                self.tokens.append((i, token))
                logger.info(f"Telegram Bot {i} token configured")

        if not self.tokens:
            logger.warning("No Telegram tokens configured")

    async def start(self):
        """Start all Telegram bots."""
        if not self.tokens:
            logger.error("No Telegram tokens configured — skipping Telegram")
            return

        logger.info(f"Starting {len(self.tokens)} Telegram bot(s)...")

        for bot_num, token in self.tokens:
            try:
                app = Application.builder().token(token).build()

                # Add handlers
                app.add_handler(CommandHandler("start", self.make_cmd_start(bot_num)))
                app.add_handler(CommandHandler("help", self.make_cmd_help(bot_num)))
                app.add_handler(CommandHandler("task", self.make_cmd_task(bot_num)))
                app.add_handler(CommandHandler("status", self.make_cmd_status(bot_num)))
                app.add_handler(CommandHandler("pending", self.make_cmd_pending(bot_num)))
                app.add_handler(CommandHandler("agents", self.make_cmd_agents(bot_num)))
                app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.make_handle_message(bot_num)))

                await app.initialize()
                await app.start()
                self.applications.append(app)
                logger.info(f"Telegram Bot {bot_num} started")

            except Exception as e:
                logger.error(f"Failed to start Telegram Bot {bot_num}: {e}")

        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            for app in self.applications:
                await app.stop()

    def make_cmd_start(self, bot_num):
        async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            welcome_text = (
                f"🧠 **OpenClaw Elite Bot #{bot_num}**\n\n"
                "I am an autonomous AI workforce. Send me any task and I will route it to the right agent.\n\n"
                "Commands:\n"
                "/task <description> — Submit a task\n"
                "/status <task_id> — Check task status\n"
                "/pending — List pending tasks\n"
                "/agents — List available agents\n"
                "/help — Show this help"
            )
            await update.message.reply_text(welcome_text, parse_mode="Markdown")
        return cmd_start

    def make_cmd_help(self, bot_num):
        return self.make_cmd_start(bot_num)

    def make_cmd_task(self, bot_num):
        async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text("Usage: /task <description>\nExample: /task research AI automation tools")
                return

            task_desc = " ".join(context.args)
            agent = self._detect_agent(task_desc)

            await update.message.reply_text(f"🚀 Bot #{bot_num} submitting to **{agent}** agent...")

            try:
                task_id = await submit_task(
                    task_desc,
                    agent=agent,
                    requester=f"telegram_bot{bot_num}:{update.effective_user.username or update.effective_user.id}",
                    channel_id=str(update.effective_chat.id)
                )

                result = await execute_task(task_id)

                result_text = (
                    f"✅ **Task Complete**\n\n"
                    f"**ID:** `{task_id}`\n"
                    f"**Agent:** {agent}\n"
                    f"**Result:**\n{result[:1000]}"
                )
                await update.message.reply_text(result_text, parse_mode="Markdown")

            except Exception as e:
                logger.error(f"Task error Bot #{bot_num}: {e}", exc_info=True)
                await update.message.reply_text(f"❌ Error: {str(e)[:500]}")
        return cmd_task

    def make_cmd_status(self, bot_num):
        async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text("Usage: /status <task_id>")
                return

            task_id = context.args[0]
            try:
                status = await get_task_status(task_id)

                if "error" in status:
                    await update.message.reply_text(f"❌ Task not found: {task_id}")
                else:
                    status_text = (
                        f"📋 **Task Status**\n\n"
                        f"**ID:** `{task_id}`\n"
                        f"**Status:** {status.get('status', 'unknown')}\n"
                        f"**Result:** {status.get('result', 'N/A')[:500]}"
                    )
                    await update.message.reply_text(status_text, parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)[:500]}")
        return cmd_status

    def make_cmd_pending(self, bot_num):
        async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                tasks = await list_pending()

                if not tasks:
                    await update.message.reply_text("📋 No pending tasks")
                else:
                    task_list = "\n".join([
                        f"• `{t.get('id', 'N/A')}`: {t.get('desc', 'N/A')[:50]}..."
                        for t in tasks[:10]
                    ])
                    pending_text = f"📋 **Pending Tasks** ({len(tasks)})\n\n{task_list}"
                    await update.message.reply_text(pending_text, parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)[:500]}")
        return cmd_pending

    def make_cmd_agents(self, bot_num):
        async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
            from worker.agents import AGENT_DISPATCH

            agents = "\n".join([f"• **{k}**" for k in AGENT_DISPATCH.keys()])
            agents_text = (
                f"🤖 **Available Agents**\n\n{agents}\n\n"
                f"Use `/task <description>` to submit a task. The right agent will be selected automatically."
            )
            await update.message.reply_text(agents_text, parse_mode="Markdown")
        return cmd_agents

    def make_handle_message(self, bot_num):
        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not update.message or not update.message.text:
                return

            message = update.message.text.strip()
            user = update.effective_user.username or str(update.effective_user.id)

            logger.info(f"[Telegram Bot #{bot_num}] {user}: {message[:80]}")

            try:
                task_id = await submit_task(
                    message,
                    agent="orchestrator",
                    requester=f"telegram_bot{bot_num}:{user}",
                    channel_id=str(update.effective_chat.id)
                )

                result = await execute_task(task_id)

                await update.message.reply_text(f"✅ **Done**\n\n{result[:1500]}", parse_mode="Markdown")

            except Exception as e:
                logger.error(f"Message handling error Bot #{bot_num}: {e}", exc_info=True)
                await update.message.reply_text(
                    f"❌ I encountered an error processing your request.\n\nError: `{str(e)[:500]}`",
                    parse_mode="Markdown"
                )
        return handle_message

    def _detect_agent(self, task_desc: str) -> str:
        """Detect the best agent for a task."""
        task_lower = task_desc.lower()
        if any(w in task_lower for w in ["code", "debug", "fix", "script", "function", "program"]):
            return "coder"
        elif any(w in task_lower for w in ["research", "find", "search", "analyze", "investigate"]):
            return "research"
        elif any(w in task_lower for w in ["business", "opportunity", "niche", "revenue", "money", "profit", "market"]):
            return "business"
        elif any(w in task_lower for w in ["content", "video", "post", "blog", "write", "create", "generate"]):
            return "growth"
        elif any(w in task_lower for w in ["review", "check", "test", "validate", "verify"]):
            return "reviewer"
        elif any(w in task_lower for w in ["ops", "deploy", "server", "infra", "config", "setup"]):
            return "ops"
        elif any(w in task_lower for w in ["qa", "quality", "bug", "issue", "error"]):
            return "qa"
        elif any(w in task_lower for w in ["memory", "remember", "store", "save", "recall"]):
            return "memory_agent"
        return "orchestrator"

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Telegram channel via first available bot."""
        if not self.applications:
            return
        try:
            prefix = f"✅ **Task `{task_id}` complete**\n\n" if task_id else ""
            await self.applications[0].bot.send_message(
                chat_id=int(channel_id),
                text=f"{prefix}{content[:4000]}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

# Standalone runner
if __name__ == "__main__":
    gateway = TelegramGateway()
    asyncio.run(gateway.start())
