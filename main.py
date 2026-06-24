#!/usr/bin/env python3
"""OpenClaw Bot — Discord Gateway Bot + Background AI Worker

Architecture:
  - Gateway Bot: Receives Discord events (messages, slash commands) via WebSocket
  - Redis Queue: Tasks queued by gateway, picked up by AI worker
  - AI Worker: Processes tasks (Groq API), posts results back to Discord
  - Slack Reporter: Optional webhook notifications on task completion

Render Deployment: Background Worker (no HTTP port)
"""

import os
import sys
import asyncio
import signal
import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from memory import get_redis, push_task, get_task_status, get_recent_tasks
from worker.slack_reporter import SlackReporter

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("openclaw")

# --- Config ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
OWNER_ID = os.getenv("OWNER_ID")

if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN not set — exiting")
    sys.exit(1)

guild_id = int(GUILD_ID) if GUILD_ID else None
owner_id = int(OWNER_ID) if OWNER_ID else None

# --- Intents & Bot ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
slack = SlackReporter()

# --- Lifecycle ---
@bot.event
async def on_ready():
    logger.info("Bot logged in as %s (ID: %s)", bot.user, bot.user.id)
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=guild_id) if guild_id else None)
        logger.info("Synced %d slash command(s)", len(synced))
    except Exception as e:
        logger.warning("Command sync failed: %s", e)

    # Health check: verify Redis connectivity
    try:
        redis = get_redis()
        redis.ping()
        logger.info("Redis connection OK")
    except Exception as e:
        logger.error("Redis connection failed: %s", e)

@bot.event
async def on_error(event, *args, **kwargs):
    logger.exception("Unhandled error in event %s", event)

# --- Slash Commands ---

@bot.tree.command(name="ask", description="Ask the AI a question")
@app_commands.describe(question="What do you want to ask?")
async def cmd_ask(interaction: discord.Interaction, question: str):
    """Queue an AI task and respond immediately with a task ID."""
    await interaction.response.defer(thinking=True)

    try:
        task_id = push_task({
            "type": "ask",
            "user_id": str(interaction.user.id),
            "username": interaction.user.name,
            "guild_id": str(interaction.guild_id) if interaction.guild_id else None,
            "channel_id": str(interaction.channel_id),
            "question": question,
            "timestamp": datetime.utcnow().isoformat(),
        })

        msg = "Task queued: `%s`\nI\'ll reply here when it\'s done." % task_id
        await interaction.followup.send(msg)
        logger.info("Task %s queued by %s", task_id, interaction.user)

    except Exception as e:
        logger.exception("Failed to queue task")
        await interaction.followup.send("Failed to queue task: %s" % e)


@bot.tree.command(name="agents", description="List active AI agents")
async def cmd_agents(interaction: discord.Interaction):
    """BUG FIX: Use followup.send() after defer()."""
    await interaction.response.defer(thinking=True)

    try:
        redis = get_redis()
        agents = redis.smembers("openclaw:agents") or set()

        if not agents:
            await interaction.followup.send("No active agents right now.")
            return

        embed = discord.Embed(title="Active Agents", color=0x00ff88)
        for agent in sorted(agents):
            info = redis.hgetall("openclaw:agent:%s" % agent) or {}
            status = info.get("status", "unknown")
            last_seen = info.get("last_seen", "never")
            value_text = "Status: `%s`\nLast seen: `%s`" % (status, last_seen)
            embed.add_field(name=agent, value=value_text, inline=False)
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.exception("Failed to list agents")
        await interaction.followup.send("Error: %s" % e)


@bot.tree.command(name="status", description="Check bot and queue status")
async def cmd_status(interaction: discord.Interaction):
    """BUG FIX: Use followup.send() after defer()."""
    await interaction.response.defer(thinking=True)

    try:
        redis = get_redis()
        queue_len = redis.llen("openclaw:queue")
        processing = redis.llen("openclaw:processing")
        completed = redis.get("openclaw:stats:completed") or 0
        failed = redis.get("openclaw:stats:failed") or 0

        embed = discord.Embed(title="OpenClaw Status", color=0x0099ff)
        embed.add_field(name="Queue Length", value=str(queue_len), inline=True)
        embed.add_field(name="Processing", value=str(processing), inline=True)
        embed.add_field(name="Completed", value=str(completed), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)
        embed.add_field(name="Bot User", value=str(bot.user), inline=False)
        embed.set_footer(text="Guild: %s" % (interaction.guild_id or "DM"))

        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.exception("Failed to get status")
        await interaction.followup.send("Error: %s" % e)


@bot.tree.command(name="tasks", description="View recent tasks")
@app_commands.describe(limit="Number of tasks to show (max 20)")
async def cmd_tasks(interaction: discord.Interaction, limit: int = 5):
    """View recent task history."""
    await interaction.response.defer(thinking=True)

    try:
        limit = max(1, min(limit, 20))
        tasks = get_recent_tasks(limit)

        if not tasks:
            await interaction.followup.send("No tasks found.")
            return

        embed = discord.Embed(title="Recent Tasks (last %d)" % len(tasks), color=0xffaa00)
        for t in tasks:
            status_emoji = {"completed": "✅", "failed": "❌", "processing": "⏳", "queued": "🕐"}
            emoji = status_emoji.get(t.get("status", "unknown"), "❓")
            q = t.get("question", "N/A")[:50]
            st = t.get("status", "unknown")
            name_text = "%s %s..." % (emoji, t.get("id", "unknown")[:8])
            value_text = "Q: %s...\nStatus: `%s`" % (q, st)
            embed.add_field(name=name_text, value=value_text, inline=False)
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.exception("Failed to get tasks")
        await interaction.followup.send("Error: %s" % e)


# --- Message Handler ---
@bot.event
async def on_message(message: discord.Message):
    """Process DMs and mentions."""
    if message.author == bot.user:
        return

    # DM handling
    if message.guild is None and owner_id and message.author.id == owner_id:
        # Owner DM commands
        if message.content.startswith("!eval "):
            # Restricted eval for debugging
            code = message.content[6:]
            try:
                result = eval(code)
                await message.reply("```python\n%s\n```" % result)
            except Exception as e:
                await message.reply("Error: %s" % e)
        elif message.content == "!ping":
            await message.reply("Pong!")

    await bot.process_commands(message)


# --- Graceful Shutdown ---
shutdown_event = asyncio.Event()

def handle_signal(sig):
    logger.info("Received signal %s, shutting down gracefully...", sig)
    shutdown_event.set()

async def main():
    """Main entry point with proper signal handling for Render."""
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    try:
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid DISCORD_TOKEN")
        sys.exit(1)
    except Exception as e:
        logger.exception("Bot crashed")
        raise

if __name__ == "__main__":
    asyncio.run(main())
