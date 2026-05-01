import os
import asyncio
import logging
import discord
from discord.ext import commands
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openclaw")

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

ai = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

SYSTEM_PROMPT = (
    "You are OpenClaw, an AI assistant built by Devin. "
    "You live inside a Discord server and help with any task. "
    "Be concise, useful, and friendly."
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

_state = {"model": "llama3-8b-8192", "auto": True}


async def chat_reply(prompt: str) -> str:
    if not ai:
        return "No GROQ_API_KEY configured."
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ai.chat.completions.create(
                model=_state["model"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
            ),
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("Groq error: %s", e)
        return f"AI error: {e}"


@bot.event
async def on_ready():
    log.info("%s is online and ready!", bot.user)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def status(ctx):
    await ctx.send(
        f"Model: {_state['model']}
"
        f"Auto-reply: {_state['auto']}
"
        f"Groq connected: {ai is not None}"
    )


@bot.command()
async def task(ctx, *, prompt: str = ""):
    if not prompt:
        await ctx.send("Usage: !task <your request>")
        return
    async with ctx.typing():
        reply = await chat_reply(prompt)
    await ctx.send(reply)


@bot.command()
async def auto(ctx):
    _state["auto"] = not _state["auto"]
    await ctx.send(f"Auto-reply {'ON' if _state['auto'] else 'OFF'}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.content.startswith("!"):
        return
    if _state["auto"]:
        async with message.channel.typing():
            reply = await chat_reply(message.content)
        await message.channel.send(reply)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("DISCORD_TOKEN not set")
    else:
        bot.run(DISCORD_TOKEN)
