"""Telegram Bot Manager — 3 bot instances."""
import asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from core.config import settings
logger = logging.getLogger("openclaw.telegram")

class TelegramBotManager:
    def __init__(self, agent_pool):
        self.agent_pool = agent_pool
        self.status = {"bots": {}, "total_chats": 0}
        self._apps = []
        self._running = False

    async def start(self):
        self._running = True
        tokens = [("bot1", settings.TELEGRAM_BOT1_TOKEN), ("bot2", settings.TELEGRAM_BOT2_TOKEN), ("bot3", settings.TELEGRAM_BOT3_TOKEN)]
        for name, token in tokens:
            if not token: continue
            app = ApplicationBuilder().token(token).build()
            self._apps.append((name, app))
            self.status["bots"][name] = {"connected": True, "chats": set()}
            app.add_handler(CommandHandler("start", self._start_cmd))
            app.add_handler(CommandHandler("swarm", self._swarm_cmd))
            app.add_handler(CommandHandler("agent", self._agent_cmd))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            logger.info(f"[Telegram {name}] Starting...")
            await app.initialize(); await app.start(); await app.updater.start_polling()
        while self._running: await asyncio.sleep(1)

    async def _start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🐝 Welcome to OpenClaw! Use /agent <query>.")
    async def _swarm_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Swarm: {await self.agent_pool.status}")
    async def _agent_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query: await update.message.reply_text("Usage: /agent <question>"); return
        response = await self.agent_pool.direct_query(query, "telegram")
        await update.message.reply_text(response)
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        chat_id = update.message.chat_id
        for name, _ in self._apps:
            if chat_id not in self.status["bots"][name]["chats"]: self.status["bots"][name]["chats"].add(chat_id)
        response = await self.agent_pool.handle_message("telegram", str(update.message.from_user.id), update.message.from_user.username or "unknown", update.message.text, str(chat_id))
        if response: await update.message.reply_text(response)

    async def stop(self):
        self._running = False
        for name, app in self._apps:
            logger.info(f"[Telegram {name}] Stopping...")
            await app.updater.stop(); await app.stop(); await app.shutdown()
