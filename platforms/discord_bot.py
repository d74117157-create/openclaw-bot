"""Discord bot with auto-reconnect."""
import asyncio, logging
import discord
from discord.ext import commands
from core.config import settings
logger = logging.getLogger("openclaw.discord")

class DiscordBot:
    def __init__(self, agent_pool):
        self.agent_pool = agent_pool
        self.status = {"connected": False, "guilds": 0, "users": 0}
        self._client = None
        self._running = False

    async def start(self):
        self._running = True
        while self._running and settings.SWARM_MODE == "auto-reconnect":
            try: await self._connect()
            except Exception as e:
                logger.error(f"Discord error: {e}. Reconnecting in 10s...")
                self.status["connected"] = False
                await asyncio.sleep(10)

    async def _connect(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        bot = commands.Bot(command_prefix="!", intents=intents)
        self._client = bot
        @bot.event
        async def on_ready():
            self.status["connected"] = True
            self.status["guilds"] = len(bot.guilds)
            self.status["users"] = sum(g.member_count for g in bot.guilds)
            logger.info(f"Discord: {bot.user} | Guilds: {self.status['guilds']}")
        @bot.event
        async def on_message(message):
            if message.author.bot: return
            response = await self.agent_pool.handle_message("discord", str(message.author.id), message.author.name, message.content, str(message.channel.id))
            if response: await message.channel.send(response)
            await bot.process_commands(message)
        @bot.command(name="swarm")
        async def swarm_cmd(ctx): await ctx.send(f"🐝 Swarm: {await self.agent_pool.status}")
        @bot.command(name="agent")
        async def agent_cmd(ctx, *, query):
            response = await self.agent_pool.direct_query(query, "discord")
            await ctx.send(response)
        await bot.start(settings.DISCORD_TOKEN)

    async def stop(self):
        self._running = False
        if self._client: await self._client.close()
        self.status["connected"] = False
