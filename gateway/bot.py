import os
import asyncio
import logging
import discord
from discord.ext import commands
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("openclaw")

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

SYSTEM_PROMPT = (
    "You are OpenClaw, a powerful AI assistant living inside Discord. "
    "You were built by Devin. You are confident, helpful, and capable. "
    "You can answer questions, write code, brainstorm ideas, tell jokes, "
    "and help with virtually anything. Keep replies concise but thorough. "
    "Use Discord-friendly formatting (markdown, code blocks, etc)."
)

def _chat(messages):
    if not openai_client:
        return "OpenAI API key not configured."
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, max_tokens=800
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f"Error talking to OpenAI: {e}"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"{bot.user} is online and ready!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    logger.info(f"MSG from {message.author}: {message.content}")
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return
    try:
        async with message.channel.typing():
            msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
            history = []
            async for m in message.channel.history(limit=10):
                role = "assistant" if m.author.bot else "user"
                history.append({"role": role, "content": m.content})
            history.reverse()
            msgs.extend(history)
            reply = await asyncio.to_thread(_chat, msgs)
            await message.reply(reply)
    except Exception as e:
        logger.error(f"on_message error: {e}")
        try:
            await message.reply(f"Error: {e}")
        except Exception:
            pass

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def status(ctx):
    await ctx.send("OpenClaw is online and operational.")

@bot.command()
async def task(ctx, *, task_text: str = None):
    if not task_text:
        await ctx.send("Usage: !task <describe what you need>")
        return
    try:
        async with ctx.typing():
            msgs = [
                {"role": "system", "content": SYSTEM_PROMPT + " The user gave you a task. Complete it thoroughly."},
                {"role": "user", "content": task_text},
            ]
            result = await asyncio.to_thread(_chat, msgs)
            await ctx.send(result)
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
async def auto(ctx, *, prompt: str = None):
    if not prompt:
        await ctx.send("Usage: !auto <what should I do?>")
        return
    try:
        async with ctx.typing():
            msgs = [
                {"role": "system", "content": SYSTEM_PROMPT + " The user gave you a task. Complete it thoroughly."},
                {"role": "user", "content": prompt},
            ]
            result = await asyncio.to_thread(_chat, msgs)
            await ctx.send(result)
    except Exception as e:
        await ctx.send(f"Error: {e}")

token = os.environ.get("DISCORD_TOKEN")
if not token:
    logger.critical("DISCORD_TOKEN not set!")
    exit(1)
logger.info("Starting OpenClaw bot...")
bot.run(token)
