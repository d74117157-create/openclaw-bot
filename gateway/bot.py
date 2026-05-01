"""Discord bot gateway - receives commands and routes them to the kernel."""

import os
import sys
import asyncio
import time
import logging

import discord
from discord.ext import commands

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import kernel

logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    logger.critical("DISCORD_TOKEN is not set. Bot cannot start.")
    sys.exit(1)

INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

_last_task_ts = {}
COOLDOWN_SECONDS = 3
MAX_RESPONSE_LEN = 1900


def _truncate(text, limit=MAX_RESPONSE_LEN):
    if len(text) <= limit:
        return text
    return text[:limit - 20] + "\n\n... (truncated)"


@bot.event
async def on_ready():
    kernel.init_kernel()
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    print(f"OpenClaw is online as {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: {error.param.name}. Check !help.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        logger.error("Unhandled command error: %s", error)
        await ctx.send("Something went wrong. Please try again.")


@bot.command(name="task")
async def task_command(ctx, *, message: str):
    """Send a task to the AI worker. Usage: !task <your request>"""
    now = time.time()
    last = _last_task_ts.get(ctx.author.id, 0)
    if now - last < COOLDOWN_SECONDS:
        await ctx.send("Slow down - try again in a moment.")
        return
    _last_task_ts[ctx.author.id] = now
    try:
        async with ctx.typing():
            result = await asyncio.to_thread(kernel.handle_task, message)
        await ctx.send(f"Task complete:\n{_truncate(result)}")
    except Exception as exc:
        logger.error("!task error: %s", exc)
        await ctx.send(f"Task failed: {exc}")


@bot.command(name="auto")
async def auto_command(ctx, mode: str):
    """Toggle autopilot. Usage: !auto on | !auto off"""
    mode = mode.lower().strip()
    if mode == "on":
        if kernel.is_autopilot_on():
            await ctx.send("Autopilot is already running.")
            return
        kernel.enable_autopilot(asyncio.get_event_loop())
        await ctx.send("Autopilot enabled. Pending tasks will be processed automatically.")
    elif mode == "off":
        if not kernel.is_autopilot_on():
            await ctx.send("Autopilot is already off.")
            return
        kernel.disable_autopilot()
        await ctx.send("Autopilot disabled. Background processing stopped.")
    else:
        await ctx.send("Usage: !auto on or !auto off")


@bot.command(name="status")
async def status_command(ctx):
    """Show task statistics and autopilot state."""
    try:
        stats = kernel.get_status()
        total = sum(stats.values())
        done = stats.get("done", 0)
        pending = stats.get("pending", 0)
        failed = stats.get("failed", 0)
        ap = "ON" if kernel.is_autopilot_on() else "OFF"
        msg = (f"OpenClaw Status\n"
               f"Total tasks: {total}\n"
               f"Completed: {done}\n"
               f"Pending: {pending}\n"
               f"Failed: {failed}\n"
               f"Autopilot: {ap}")
        await ctx.send(msg)
    except Exception as exc:
        logger.error("!status error: %s", exc)
        await ctx.send(f"Could not fetch status: {exc}")


@bot.command(name="ping")
async def ping_command(ctx):
    """Health check - confirms the bot is alive."""
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency: {latency_ms} ms")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
