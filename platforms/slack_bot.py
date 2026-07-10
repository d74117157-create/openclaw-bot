"""Slack Bolt integration with Socket Mode."""
import asyncio, logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from core.config import settings
logger = logging.getLogger("openclaw.slack")

class SlackBot:
    def __init__(self, agent_pool):
        self.agent_pool = agent_pool
        self.status = {"connected": False, "team": None}
        self._app = None
        self._handler = None
        self._running = False

    async def start(self):
        self._running = True
        self._app = AsyncApp(token=settings.SLACK_BOT_TOKEN)
        @self._app.message(".*")
        async def handle_message(message, say, client):
            response = await self.agent_pool.handle_message("slack", message.get("user"), "slack_user", message.get("text", ""), message.get("channel"))
            if response: await say(response)
        @self._app.command("/swarm")
        async def swarm_command(ack, say): await ack(); await say(f"🐝 Swarm: {await self.agent_pool.status}")
        @self._app.command("/agent")
        async def agent_command(ack, say, command):
            await ack()
            query = command.get("text", "")
            if not query: await say("Usage: /agent <question>"); return
            response = await self.agent_pool.direct_query(query, "slack")
            await say(response)
        self._handler = AsyncSocketModeHandler(self._app, settings.SLACK_APP_TOKEN)
        logger.info("[Slack] Starting Socket Mode...")
        self.status["connected"] = True
        await self._handler.start_async()

    async def stop(self):
        self._running = False; self.status["connected"] = False
        if self._handler: await self._handler.close_async()
        logger.info("[Slack] Stopped.")
