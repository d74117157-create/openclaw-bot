"""
Telegram Gateway — OpenClaw Master Brain
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from shared.config import Config

logger = logging.getLogger("telegram_gateway")

class TelegramGateway:
    """Telegram bot interface for the OpenClaw swarm."""

    def __init__(self, swarm):
        self.swarm = swarm
        self.app = None
        
        if not Config.TELEGRAM_BOT1_TOKEN:
            logger.error("TELEGRAM_BOT1_TOKEN not set")
            return

        self.app = Application.builder().token(Config.TELEGRAM_BOT1_TOKEN).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_message))

    async def start(self):
        """Start the Telegram bot."""
        if not self.app:
            return
            
        logger.info("Telegram gateway starting polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        # Keep running
        while True:
            await asyncio.sleep(3600)

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Telegram chat."""
        try:
            prefix = f"✅ *Task `{task_id}` complete:*\n\n" if task_id else ""
            # Telegram has 4096 char limit
            full_text = prefix + content
            if len(full_text) > 4000:
                full_text = full_text[:3900] + "\n\n... (truncated)"

            await self.app.bot.send_message(
                chat_id=int(channel_id),
                text=full_text,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🧠 *OpenClaw Master Brain* is ONLINE.\n\n"
            "Commands:\n"
            "/status - System health\n"
            "Just send a message to ask the AI swarm.",
            parse_mode="Markdown"
        )

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.swarm.get_stats()
        await update.message.reply_text(
            f"📊 *OpenClaw Status*\n"
            f"Uptime: {int(stats['uptime_seconds'])}s\n"
            f"Tasks: {stats['tasks_total']}",
            parse_mode="Markdown"
        )

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        task_id = await self.swarm.route_message(
            platform="telegram",
            user_id=str(update.effective_user.id),
            username=update.effective_user.username or "user",
            message=update.message.text,
            channel_id=str(update.effective_chat.id),
        )

        await update.message.reply_text(f"🧠 Task queued: `{task_id}`. Processing...")
