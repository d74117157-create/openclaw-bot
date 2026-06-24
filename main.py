#!/usr/bin/env python3
"""OpenClaw Swarm — Multi-Platform AI Agent System

SUPERIOR TO VIKTOR:
- Viktor: Slack-only, single-agent, closed-source, $75M VC-backed
- OpenClaw: Discord + Telegram + Slack + Web, multi-agent swarm, open-source, yours

Architecture:
  ┌─────────────────────────────────────────┐
  │         OpenClaw Swarm Kernel           │
  ├─────────────────────────────────────────┤
  │  Discord Bot  │  Telegram Bot  │  Slack  │
  │  (Gateway)    │  (Gateway)   │ (Gateway)│
  ├─────────────────────────────────────────┤
  │      Redis Message Bus + Memory         │
  ├─────────────────────────────────────────┤
  │  Coder │ Researcher │ Ops │ Growth │ QA │
  │  Agent │   Agent    │Agent│ Agent  │Agent│
  ├─────────────────────────────────────────┤
  │        Groq LLM (Llama 3/Mixtral)       │
  └─────────────────────────────────────────┘

Platforms: Discord, Telegram, Slack, Web API
Agents: Coder, Researcher, Ops, Growth, QA, Memory
Memory: Redis-backed with vector search
Deployment: Render, Railway, Docker, VPS
"""

import os
import sys
import asyncio
import signal
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

import discord
from discord import app_commands
from discord.ext import commands, tasks

# Platform gateways
from gateway.discord_bot import DiscordGateway
from gateway.telegram_bot import TelegramGateway
from gateway.slack_bot import SlackGateway
from gateway.web_api import WebGateway

# Memory & Bus
from memory import get_redis, push_task, get_task_status, get_recent_tasks
from shared.message_bus import MessageBus

# Agent swarm
from worker.agents.coder import CoderAgent
from worker.agents.researcher import ResearcherAgent
from worker.agents.ops import OpsAgent
from worker.agents.growth import GrowthAgent
from worker.agents.qa import QAAgent
from worker.agents.orchestrator import OrchestratorAgent

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("openclaw")

# ─── Config ────────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
OWNER_ID = os.getenv("OWNER_ID")

# ─── Swarm Kernel ──────────────────────────────────────────────────────────────
class OpenClawSwarm:
    """The central brain — routes messages between platforms and agents."""

    def __init__(self):
        self.bus = MessageBus()
        self.redis = get_redis()
        self.agents: Dict[str, Any] = {}
        self.gateways: Dict[str, Any] = {}
        self.running = False
        self.start_time = datetime.utcnow()

        # Initialize agent swarm
        self._init_agents()

    def _init_agents(self):
        """Initialize the agent swarm."""
        self.agents = {
            "orchestrator": OrchestratorAgent(self.bus),
            "coder": CoderAgent(self.bus),
            "researcher": ResearcherAgent(self.bus),
            "ops": OpsAgent(self.bus),
            "growth": GrowthAgent(self.bus),
            "qa": QAAgent(self.bus),
        }
        logger.info(f"Swarm initialized with {len(self.agents)} agents")

    async def route_message(self, platform: str, user_id: str, username: str, 
                           message: str, channel_id: str, metadata: dict = None):
        """Route incoming message to the right agent."""

        # Build context
        context = {
            "platform": platform,
            "user_id": user_id,
            "username": username,
            "message": message,
            "channel_id": channel_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        # Determine which agent should handle this
        agent_name = await self.agents["orchestrator"].classify_intent(message)

        # Queue task for the agent
        task_id = push_task({
            "type": "agent_task",
            "agent": agent_name,
            "context": context,
            "status": "queued",
        })

        logger.info(f"Routed to {agent_name} | Task: {task_id} | User: {username} | Platform: {platform}")
        return task_id

    async def deliver_response(self, platform: str, channel_id: str, 
                              content: str, task_id: str = None):
        """Deliver response back to the originating platform."""
        gateway = self.gateways.get(platform)
        if gateway:
            await gateway.send_message(channel_id, content, task_id)
        else:
            logger.warning(f"No gateway for platform: {platform}")

    def get_stats(self) -> dict:
        """Get swarm statistics."""
        return {
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "agents": list(self.agents.keys()),
            "gateways": list(self.gateways.keys()),
            "tasks_completed": self.redis.get("openclaw:stats:completed") or 0,
            "tasks_failed": self.redis.get("openclaw:stats:failed") or 0,
            "queue_length": self.redis.llen("openclaw:queue"),
        }

# ─── Discord Gateway ───────────────────────────────────────────────────────────
class DiscordGateway(commands.Bot):
    """Discord interface for the swarm."""

    def __init__(self, swarm: OpenClawSwarm):
        self.swarm = swarm
        self.swarm.gateways["discord"] = self

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)

        # Register slash commands
        self._register_commands()

    def _register_commands(self):
        @self.tree.command(name="ask", description="Ask the swarm anything")
        @app_commands.describe(question="What do you want to know or do?")
        async def cmd_ask(interaction: discord.Interaction, question: str):
            await interaction.response.defer(thinking=True)

            task_id = await self.swarm.route_message(
                platform="discord",
                user_id=str(interaction.user.id),
                username=interaction.user.name,
                message=question,
                channel_id=str(interaction.channel_id),
                metadata={"guild_id": str(interaction.guild_id) if interaction.guild_id else None}
            )

            await interaction.followup.send(
                "Task queued: `%s`\nI'll reply here when it's done." % task_id
            )

        @self.tree.command(name="agents", description="List active swarm agents")
        async def cmd_agents(interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)

            embed = discord.Embed(title="OpenClaw Swarm Agents", color=0x00ff88)
            for name, agent in self.swarm.agents.items():
                status = "online" if agent.is_ready() else "booting"
                embed.add_field(
                    name=name.upper(),
                    value="Status: `%s`\nType: `%s`" % (status, agent.agent_type),
                    inline=False
                )
            await interaction.followup.send(embed=embed)

        @self.tree.command(name="status", description="Swarm system status")
        async def cmd_status(interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)

            stats = self.swarm.get_stats()
            embed = discord.Embed(title="OpenClaw Status", color=0x0099ff)
            embed.add_field(name="Queue", value=str(stats["queue_length"]), inline=True)
            embed.add_field(name="Completed", value=str(stats["tasks_completed"]), inline=True)
            embed.add_field(name="Failed", value=str(stats["tasks_failed"]), inline=True)
            embed.add_field(name="Uptime", value="%ds" % int(stats["uptime_seconds"]), inline=True)
            embed.add_field(name="Platforms", value=", ".join(stats["gateways"]), inline=False)
            await interaction.followup.send(embed=embed)

        @self.tree.command(name="deploy", description="Deploy code to production")
        @app_commands.describe(repo="GitHub repo", branch="Branch to deploy")
        async def cmd_deploy(interaction: discord.Interaction, repo: str, branch: str = "main"):
            await interaction.response.defer(thinking=True)

            task_id = await self.swarm.route_message(
                platform="discord",
                user_id=str(interaction.user.id),
                username=interaction.user.name,
                message="deploy %s %s" % (repo, branch),
                channel_id=str(interaction.channel_id),
            )
            await interaction.followup.send("Deploy queued: `%s`" % task_id)

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if channel:
                if task_id:
                    content = "Task `%s` complete:\n%s" % (task_id, content)
                await channel.send(content[:2000])  # Discord limit
        except Exception as e:
            logger.error("Discord send failed: %s", e)

    async def on_ready(self):
        logger.info("Discord gateway ready: %s", self.user)
        try:
            guild = discord.Object(id=int(GUILD_ID)) if GUILD_ID else None
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %d commands", len(synced))
        except Exception as e:
            logger.warning("Command sync: %s", e)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        # DM or mention handling
        if message.guild is None or self.user.mentioned_in(message):
            await self.swarm.route_message(
                platform="discord",
                user_id=str(message.author.id),
                username=message.author.name,
                message=message.content,
                channel_id=str(message.channel.id),
            )

        await self.process_commands(message)

# ─── Main Entry ──────────────────────────────────────────────────────────────
async def main():
    swarm = OpenClawSwarm()

    # Start Discord gateway
    if DISCORD_TOKEN:
        discord_bot = DiscordGateway(swarm)
        discord_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
        logger.info("Discord gateway starting...")
    else:
        discord_task = None
        logger.warning("DISCORD_TOKEN not set")

    # Start Telegram gateway
    if TELEGRAM_TOKEN:
        telegram_bot = TelegramGateway(swarm)
        telegram_task = asyncio.create_task(telegram_bot.start())
        logger.info("Telegram gateway starting...")
    else:
        telegram_task = None

    # Start Slack gateway
    if SLACK_BOT_TOKEN:
        slack_bot = SlackGateway(swarm)
        slack_task = asyncio.create_task(slack_bot.start())
        logger.info("Slack gateway starting...")
    else:
        slack_task = None

    # Start Web API
    web = WebGateway(swarm, port=WEB_PORT)
    web_task = asyncio.create_task(web.start())

    # Keep alive
    try:
        await asyncio.gather(
            *[t for t in [discord_task, telegram_task, slack_task, web_task] if t],
            return_exceptions=True
        )
    except asyncio.CancelledError:
        logger.info("Shutting down swarm...")

if __name__ == "__main__":
    asyncio.run(main())
