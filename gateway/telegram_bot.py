"""Telegram bot gateway - receives commands and routes them to the kernel."""

import os
import sys
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import kernel

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# -- Command handlers --

async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      await update.message.reply_text(
                "\U0001f916 *OpenClaw is online!*\n\n"
                "Commands:\n"
                "/task >message> - Send a task to the AI\n"
                "/auto on|off - Toggle autopilot\n"
                "/status - Show task stats\n"
                "/ping - Health check",
                parse_mode="Markdown",
      )


async def task_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      if not ctx.args:
                await update.message.reply_text("Usage: /task >your request>")
                return

      message = " ".join(ctx.args)
      await update.message.reply_text("Processing...")

    try:
              result = await asyncio.to_thread(kernel.handle_task, message)
              if len(result) > 4000:
                            result = result[:3980] + "\n\n... (truncated)"
                        await update.message.reply_text(f"Task complete:\n{result}")
except Exception as exc:
        logger.error("Telegram /task error: %s", exc)
        await update.message.reply_text(f"Task failed: {exc}")


async def auto_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      if not ctx.args:
                await update.message.reply_text("Usage: /auto on or /auto off")
                return

    mode = ctx.args[0].lower().strip()

    if mode == "on":
              if kernel.is_autopilot_on():
                            await update.message.reply_text("Autopilot is already running.")
                            return
                        loop = asyncio.get_event_loop()
        kernel.enable_autopilot(loop)
        await update.message.reply_text("Autopilot enabled. Pending tasks will be processed automatically.")

elif mode == "off":
        if not kernel.is_autopilot_on():
                      await update.message.reply_text("Autopilot is already off.")
                      return
                  kernel.disable_autopilot()
        await update.message.reply_text("Autopilot disabled. Background processing stopped.")

else:
        await update.message.reply_text("Usage: /auto on or /auto off")


async def status_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      try:
                stats = kernel.get_status()
                total = sum(stats.values())
                done = stats.get("done", 0)
                pending = stats.get("pending", 0)
                failed = stats.get("failed", 0)
                ap_state = "ON" if kernel.is_autopilot_on() else "OFF"

        msg = (
                      "OpenClaw Status\n\n"
                      f"Total tasks: {total}\n"
                      f"Completed: {done}\n"
                      f"Pending: {pending}\n"
                      f"Failed: {failed}\n"
                      f"Autopilot: {ap_state}"
        )
        await update.message.reply_text(msg)
except Exception as exc:
        logger.error("Telegram /status error: %s", exc)
        await update.message.reply_text(f"Could not fetch status: {exc}")


async def ping_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      await update.message.reply_text("Pong! OpenClaw Telegram bot is alive.")


async def fallback_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      """Treat any plain text as a task automatically."""
    message = update.message.text
    if not message:
              return

    try:
              result = await asyncio.to_thread(kernel.handle_task, message)
        if len(result) > 4000:
                      result = result[:3980] + "\n\n... (truncated)"
                  await update.message.reply_text(f"{result}")
except Exception as exc:
        logger.error("Telegram fallback error: %s", exc)
        await update.message.reply_text(f"Error: {exc}")


# -- Application builder --

def build_telegram_app():
      """Build and return the Telegram Application (does not start it)."""
    if not TELEGRAM_TOKEN:
              raise RuntimeError("TELEGRAM_TOKEN is not set.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("task", task_command))
    app.add_handler(CommandHandler("auto", auto_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_message))

    return app


def run_telegram():
      """Start the Telegram bot (blocking)."""
    kernel.init_kernel()
    app = build_telegram_app()
    logger.info("Telegram bot starting...")
    print("OpenClaw Telegram bot is online!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
      run_telegram()
