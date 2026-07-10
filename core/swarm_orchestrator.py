"""SwarmOrchestrator — manages all platforms and agents."""
import asyncio, logging
from typing import Dict, List, Any, Optional
from core.config import settings
from agents.agent_pool import AgentPool
from platforms.discord_bot import DiscordBot
from platforms.telegram_bots import TelegramBotManager
from platforms.slack_bot import SlackBot
logger = logging.getLogger("openclaw.swarm")

class SwarmOrchestrator:
    def __init__(self):
        self.is_running = False
        self.agent_count = 0
        self._bots: Dict[str, Any] = {}
        self._agent_pool: Optional[AgentPool] = None
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        self.is_running = True
        self._agent_pool = AgentPool()
        await self._agent_pool.start()
        self.agent_count = len(self._agent_pool.agents)
        if settings.DISCORD_TOKEN:
            discord = DiscordBot(self._agent_pool)
            self._bots["discord"] = discord
            self._tasks.append(asyncio.create_task(discord.start()))
        if any([settings.TELEGRAM_BOT1_TOKEN, settings.TELEGRAM_BOT2_TOKEN, settings.TELEGRAM_BOT3_TOKEN]):
            telegram = TelegramBotManager(self._agent_pool)
            self._bots["telegram"] = telegram
            self._tasks.append(asyncio.create_task(telegram.start()))
        if settings.SLACK_BOT_TOKEN and settings.SLACK_APP_TOKEN:
            slack = SlackBot(self._agent_pool)
            self._bots["slack"] = slack
            self._tasks.append(asyncio.create_task(slack.start()))
        logger.info(f"Swarm started: {len(self._bots)} platforms, {self.agent_count} agents.")

    async def stop(self):
        self.is_running = False
        for name, bot in self._bots.items():
            try: await bot.stop()
            except Exception as e: logger.warning(f"Error stopping {name}: {e}")
        if self._agent_pool: await self._agent_pool.stop()
        for task in self._tasks:
            task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        logger.info("Swarm stopped.")

    async def status(self) -> Dict[str, Any]:
        return {"running": self.is_running,
                "platforms": {name: getattr(bot, "status", {}) for name, bot in self._bots.items()},
                "agents": self._agent_pool.status if self._agent_pool else {}, "uptime": "active"}

    async def reload(self):
        if self._agent_pool: await self._agent_pool.reload()
