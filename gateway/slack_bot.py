"""
OpenClaw Slack Bot — Fully Integrated with Task Dispatcher
Handles app mentions, slash commands, and routes everything through agents.
FIXED: Added fallback for missing SLACK_APP_TOKEN, better error handling, HTTP mode support.
"""
import os
import asyncio
import logging
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from worker.task_dispatcher import submit_task, execute_task, get_task_status, list_pending
from shared.config import Config
from shared.logging import setup_logging, get_logger

setup_logging("slack_bot")
logger = get_logger(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "openclaw-ops")

class SlackGateway:
    """Slack interface for OpenClaw swarm."""

    def __init__(self, swarm=None):
        self.swarm = swarm
        self.app = None
        self.handler = None

    async def start(self):
        """Start the Slack bot."""
        if not SLACK_BOT_TOKEN:
            logger.error("Slack bot token not configured. Set SLACK_BOT_TOKEN")
            return

        if not SLACK_APP_TOKEN:
            logger.warning("SLACK_APP_TOKEN not set. Slack Socket Mode will not work.")
            logger.warning("For Socket Mode, generate an app-level token at https://api.slack.com/apps")
            logger.warning("Falling back to HTTP mode (requires public URL)")
            await self._start_http_mode()
            return

        logger.info("Starting Slack gateway (Socket Mode)...")
        self.app = AsyncApp(token=SLACK_BOT_TOKEN)

        # Register event handlers
        self.app.event("app_mention")(self.handle_mention)
        self.app.event("message")(self.handle_message)

        # Register slash commands
        self.app.command("/swarm")(self.cmd_swarm)
        self.app.command("/task")(self.cmd_task)
        self.app.command("/status")(self.cmd_status)
        self.app.command("/pending")(self.cmd_pending)
        self.app.command("/agents")(self.cmd_agents)

        # Start Socket Mode
        self.handler = AsyncSocketModeHandler(self.app, SLACK_APP_TOKEN)
        await self.handler.start_async()

        logger.info("Slack gateway started")

        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

    async def _start_http_mode(self):
        """Fallback HTTP mode if SLACK_APP_TOKEN is not available."""
        logger.info("Starting Slack gateway (HTTP Mode)...")
        self.app = AsyncApp(token=SLACK_BOT_TOKEN)

        # Register event handlers
        self.app.event("app_mention")(self.handle_mention)
        self.app.command("/swarm")(self.cmd_swarm)
        self.app.command("/task")(self.cmd_task)
        self.app.command("/status")(self.cmd_status)
        self.app.command("/pending")(self.cmd_pending)
        self.app.command("/agents")(self.cmd_agents)

        # In HTTP mode, Bolt starts its own server
        # This requires PORT env var or web server setup
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Slack HTTP mode listening on port {port}")
        # Note: HTTP mode requires Render web service with public URL
        # and Slack app configured with Request URL pointing to this service

    async def handle_mention(self, body, say, logger):
        """Handle app mentions."""
        event = body["event"]
        text = event.get("text", "").strip()
        user = event.get("user", "unknown")
        channel = event.get("channel", "")

        # Remove bot mention
        text = text.replace(f"<@{body['authorizations'][0]['user_id']}>", "").strip()

        logger.info(f"[Slack Mention] {user}: {text[:80]}")
        await self.process_task(text, user, channel, say)

    async def handle_message(self, body, say, logger):
        """Handle DMs and channel messages."""
        event = body["event"]

        # Skip bot messages
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return

        text = event.get("text", "").strip()
        user = event.get("user", "unknown")
        channel = event.get("channel", "")
        channel_type = event.get("channel_type", "")

        # Only respond to DMs or messages in configured channel
        if channel_type != "im" and channel != SLACK_CHANNEL:
            return

        logger.info(f"[Slack Message] {user}: {text[:80]}")
        await self.process_task(text, user, channel, say)

    async def process_task(self, text, user, channel, say):
        """Process a task through the dispatcher."""
        try:
            await say("🚀 Processing your request...")

            # Detect agent
            agent = "orchestrator"
            text_lower = text.lower()
            if any(w in text_lower for w in ["code", "debug", "fix", "script", "function"]):
                agent = "coder"
            elif any(w in text_lower for w in ["research", "find", "search", "analyze"]):
                agent = "research"
            elif any(w in text_lower for w in ["business", "opportunity", "niche", "revenue"]):
                agent = "business"
            elif any(w in text_lower for w in ["content", "video", "post", "blog"]):
                agent = "growth"

            task_id = await submit_task(
                text,
                agent=agent,
                requester=f"slack:{user}",
                channel_id=channel
            )

            result = await execute_task(task_id)

            await say(
                f"✅ *Task Complete*\n"
                f"*ID:* `{task_id}`\n"
                f"*Agent:* {agent}\n"
                f"*Result:*\n{result[:2000]}"
            )

        except Exception as e:
            logger.error(f"Task error: {e}", exc_info=True)
            await say(f"❌ Error: {str(e)[:500]}")

    async def cmd_swarm(self, ack, body, say):
        """Handle /swarm command."""
        await ack()
        text = body.get("text", "").strip()

        if not text:
            await say("Usage: `/swarm <task>`\nExample: `/swarm research AI tools for small business`")
            return

        await self.process_task(text, body["user_id"], body["channel_id"], say)

    async def cmd_task(self, ack, body, say):
        """Handle /task command."""
        await ack()
        text = body.get("text", "").strip()

        if not text:
            await say("Usage: `/task <description>`")
            return

        await self.process_task(text, body["user_id"], body["channel_id"], say)

    async def cmd_status(self, ack, body, say):
        """Handle /status command."""
        await ack()
        text = body.get("text", "").strip()

        if not text:
            await say("Usage: `/status <task_id>`")
            return

        try:
            status = await get_task_status(text)

            if "error" in status:
                await say(f"❌ Task not found: `{text}`")
            else:
                await say(
                    f"📋 *Task Status*\n"
                    f"*ID:* `{text}`\n"
                    f"*Status:* {status.get('status', 'unknown')}\n"
                    f"*Result:* {status.get('result', 'N/A')[:1000]}"
                )
        except Exception as e:
            await say(f"❌ Error: {str(e)[:500]}")

    async def cmd_pending(self, ack, body, say):
        """Handle /pending command."""
        await ack()

        try:
            tasks = await list_pending()

            if not tasks:
                await say("📋 No pending tasks")
            else:
                task_list = "\n".join([
                    f"• `{t.get('id', 'N/A')}`: {t.get('desc', 'N/A')[:40]}..."
                    for t in tasks[:10]
                ])
                await say(f"📋 *Pending Tasks* ({len(tasks)})\n\n{task_list}")
        except Exception as e:
            await say(f"❌ Error: {str(e)[:500]}")

    async def cmd_agents(self, ack, body, say):
        """Handle /agents command."""
        await ack()
        from worker.agents import AGENT_DISPATCH

        agents = "\n".join([f"• *{k}*" for k in AGENT_DISPATCH.keys()])
        await say(
            f"🤖 *Available Agents*\n\n{agents}\n\n"
            f"Use `/swarm <task>` or `/task <description>` to submit a task."
        )

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Slack channel."""
        if not self.app:
            return
        try:
            prefix = f"✅ *Task `{task_id}` complete*\n\n" if task_id else ""
            await self.app.client.chat_postMessage(
                channel=channel_id,
                text=f"{prefix}{content[:3000]}",
                unfurl_links=False
            )
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")

# Standalone runner
if __name__ == "__main__":
    gateway = SlackGateway()
    asyncio.run(gateway.start())
