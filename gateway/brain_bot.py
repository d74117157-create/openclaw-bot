"""
OpenClaw - gateway/brain_bot.py
Cross-platform brain gateway relaying messages between Discord and Slack.
"""
import os, asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from memory import init_db, save_task, update_task
from worker.ai_worker import process_task

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
BRAIN_CHANNEL = os.environ.get("BRAIN_CHANNEL", "brain")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"[BrainBot] Online as {bot.user}")
    init_db()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.name != BRAIN_CHANNEL:
        return

    content = message.content.strip()
    if not content.startswith("!"):
        return

    cmd = content[1:].split()[0].lower()
    tid = save_task(content, "brain")

    try:
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, process_task, content, "orchestrator")
        update_task(tid, result, "done")
        await message.channel.send(f"**[Brain]** {result[:1900]}")
    except Exception as exc:
        update_task(tid, str(exc), "failed")
        raise


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
