import os
import discord
from discord.ext import commands
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worker import ai_worker

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return
    async with message.channel.typing():
        history = []
        async for msg in message.channel.history(limit=10):
            role = "assistant" if msg.author.bot else "user"
            history.append({"role": role, "content": msg.content})
        history.reverse()
        reply = ai_worker.chat_reply(history)
        await message.reply(reply)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def status(ctx):
    await ctx.send("OpenClaw is online and operational.")

@bot.command()
async def task(ctx, *, task_text: str = None):
    if not task_text:
        await ctx.send("Usage: `!task <describe what you need>`")
        return
    async with ctx.typing():
        result = ai_worker.process_task(task_text)
        await ctx.send(result)

@bot.command()
async def auto(ctx, *, prompt: str = None):
    if not prompt:
        await ctx.send("Usage: `!auto <what should I do?>`")
        return
    async with ctx.typing():
        result = ai_worker.process_task(prompt)
        await ctx.send(result)

token = os.environ.get("DISCORD_TOKEN")
if not token:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)
bot.run(token)
