"""
OpenClaw Telegram Bot — Fully Integrated with Task Dispatcher
Handles commands, messages, and routes everything through the agent system.
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

TELEGRAM_BOT1_TOKEN = os.environ.get("TELEGRAM_BOT1_TOKEN", "")
TELEGRAM_BOT2_TOKEN = os.environ.get("TELEGRAM_BOT2_TOKEN", "")

class TelegramGateway:
    """Telegram interface for OpenClaw swarm."""

    def __init__(self, swarm=None):
        self.swarm = swarm
        self.application = None
        self.token = TELEGRAM_BOT1_TOKEN or TELEGRAM_BOT2_TOKEN

    async def start(self):
        """Start the Telegram bot."""
        if not self.token:
            logger.error("No Telegram token configured")
            return

        logger.info("Starting Telegram gateway...")
        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("task", self.cmd_task))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("pending", self.cmd_pending))
        self.application.add_handler(CommandHandler("agents", self.cmd_agents))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Start polling
        await self.application.initialize()
        await self.application.start()
        logger.info("Telegram gateway started")

        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await self.application.stop()

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "🧠 **OpenClaw Elite Bot**

"
            "I am an autonomous AI workforce. Send me any task and I will route it to the right agent.

"
            "Commands:
"
            "/task <description> — Submit a task
"
            "/status <task_id> — Check task status
"
            "/pending — List pending tasks
"
            "/agents — List available agents
"
            "/help — Show this help",
            parse_mode="Markdown"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.cmd_start(update, context)

    async def cmd_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /task command — submits task to dispatcher."""
        if not context.args:
            await update.message.reply_text("Usage: /task <description>
Example: /task research AI automation tools")
            return

        task_desc = " ".join(context.args)
        agent = "orchestrator"  # Default agent

        # Detect agent from keywords
        task_lower = task_desc.lower()
        if any(w in task_lower for w in ["code", "debug", "fix", "write", "script", "function"]):
            agent = "coder"
        elif any(w in task_lower for w in ["research", "find", "search", "analyze", "investigate"]):
            agent = "research"
        elif any(w in task_lower for w in ["business", "opportunity", "niche", "revenue", "money", "profit"]):
            agent = "business"
        elif any(w in task_lower for w in ["content", "video", "post", "blog", "script", "write"]):
            agent = "growth"

        await update.message.reply_text(f"🚀 Submitting task to **{agent}** agent...")

        try:
            task_id = await submit_task(
                task_desc,
                agent=agent,
                requester=f"telegram:{update.effective_user.username or update.effective_user.id}",
                channel_id=str(update.effective_chat.id)
            )

            # Execute immediately
            result = await execute_task(task_id)

            await update.message.reply_text(
                f"✅ **Task Complete**

"
                f"**ID:** `{task_id}`
"
                f"**Agent:** {agent}
"
                f"**Result:**
{result[:1000]}",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Task error: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)[:500]}")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not context.args:
            await update.message.reply_text("Usage: /status <task_id>")
            return

        task_id = context.args[0]
        try:
            status = await get_task_status(task_id)

            if "error" in status:
                await update.message.reply_text(f"❌ Task not found: {task_id}")
            else:
                await update.message.reply_text(
                    f"📋 **Task Status**

"
                    f"**ID:** `{task_id}`
"
                    f"**Status:** {status.get('status', 'unknown')}
"
                    f"**Result:** {status.get('result', 'N/A')[:500]}",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:500]}")

    async def cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending command."""
        try:
            tasks = await list_pending()

            if not tasks:
                await update.message.reply_text("📋 No pending tasks")
            else:
                task_list = "\n".join([
                    f"• `{t.get('id', 'N/A')}`: {t.get('desc', 'N/A')[:50]}..."
                    for t in tasks[:10]
                ])
                await update.message.reply_text(
                    f"📋 **Pending Tasks** ({len(tasks)})\n\n{task_list}",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:500]}")

    async def cmd_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /agents command."""
        from worker.agents import AGENT_DISPATCH

        agents = "\n".join([f"• **{k}**" for k in AGENT_DISPATCH.keys()])
        await update.message.reply_text(
            f"🤖 **Available Agents**\n\n{agents}\n\n"
            f"Use `/task <description>` to submit a task. The right agent will be selected automatically.",
            parse_mode="Markdown"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        if not update.message or not update.message.text:
            return

        message = update.message.text.strip()
        user = update.effective_user.username or str(update.effective_user.id)

        logger.info(f"[Telegram] {user}: {message[:80]}")

        # Treat as a task
        try:
            task_id = await submit_task(
                message,
                agent="orchestrator",
                requester=f"telegram:{user}",
                channel_id=str(update.effective_chat.id)
            )

            result = await execute_task(task_id)

            await update.message.reply_text(
                f"✅ **Done**\n\n{result[:1500]}",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Message handling error: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ I encountered an error processing your request.\n\n"
                f"Error: `{str(e)[:500]}`",
                parse_mode="Markdown"
            )

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Telegram channel."""
        if not self.application:
            return
        try:
            prefix = f"✅ **Task `{task_id}` complete**\n\n" if task_id else ""
            await self.application.bot.send_message(
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
