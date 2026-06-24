"""
Slack Gateway — OpenClaw Master Brain
"""
import os
import logging
import asyncio
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from shared.config import Config

logger = logging.getLogger("slack_gateway")

class SlackGateway:
    """Slack interface for the OpenClaw swarm."""

    def __init__(self, swarm):
        self.swarm = swarm
        self.app = AsyncApp(token=Config.SLACK_BOT_TOKEN)
        self.handler = None
        self._register_handlers()

    def _register_handlers(self):
        @self.app.event("app_mention")
        async def handle_mention(event, say):
            user_id = event.get("user")
            channel_id = event.get("channel")
            text = event.get("text")
            # Remove mention from text
            clean_text = text.split(">")[-1].strip()
            
            task_id = await self.swarm.route_message(
                platform="slack",
                user_id=user_id,
                username=user_id, # Slack user ID as username
                message=clean_text,
                channel_id=channel_id
            )
            await say(f"🧠 Task queued: `{task_id}`. Processing...")

        @self.app.command("/swarm")
        async def handle_swarm_command(ack, body, say):
            await ack()
            stats = self.swarm.get_stats()
            await say(f"🧠 *OpenClaw Status*\nUptime: {int(stats['uptime_seconds'])}s\nTasks: {stats['tasks_total']}")

    async def start(self):
        """Start the Slack bot using Socket Mode."""
        if not Config.SLACK_BOT_TOKEN or not Config.SLACK_APP_TOKEN:
            logger.error("SLACK_BOT_TOKEN or SLACK_APP_TOKEN not set")
            return
            
        self.handler = AsyncSocketModeHandler(self.app, Config.SLACK_APP_TOKEN)
        logger.info("Slack gateway starting in Socket Mode...")
        await self.handler.start_async()

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Slack channel."""
        try:
            prefix = f"✅ *Task `{task_id}` complete:*\n\n" if task_id else ""
            await self.app.client.chat_postMessage(
                channel=channel_id,
                text=f"{prefix}{content}"
            )
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
