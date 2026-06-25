#!/usr/bin/env python3
"""
OpenClaw Elite — Autonomous Multi-Agent AI System
AI Workforce, not a chatbot.

Fully Integrated: Discord, 3x Telegram, Slack, Task Dispatcher, All Agents
"""
import os
import sys
import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.config import Config
from shared.logging import setup_logging, get_logger
from memory.db import init_db
from memory.elite_memory import get_memory, init_elite_memory
from worker.intent_router import get_router, classify_intent
from worker.verification import get_verifier
from worker.monitoring import get_monitoring
from worker.approval import get_approval_framework
from worker.task_dispatcher import get_dispatcher, submit_task, execute_task

# Import ALL agents
from worker.agents.bob import BobAgent
from worker.agents.carla import CarlaAgent
from worker.agents.dave import DaveAgent
from worker.agents.alice import AliceAgent
from worker.agents import AGENT_DISPATCH

# Gateways
from gateway.telegram_bot import TelegramGateway
from gateway.discord_bot import DiscordGateway
from gateway.slack_bot import SlackGateway

setup_logging("openclaw_elite")
logger = get_logger("elite_orchestrator")

# Agent map for direct instantiation (legacy support)
AGENT_MAP = {
    "bob": BobAgent,
    "carla": CarlaAgent,
    "dave": DaveAgent,
    "alice": AliceAgent,
}

class OpenClawElite:
    """The autonomous multi-agent AI workforce."""

    def __init__(self):
        self.config = Config()
        self.gateways = {}
        self.agents = {}
        self.memory = get_memory()
        self.router = get_router()
        self.verifier = get_verifier()
        self.monitoring = get_monitoring()
        self.approval = get_approval_framework()
        self.dispatcher = get_dispatcher()
        self.start_time = 0

    async def initialize(self):
        """Initialize all subsystems."""
        logger.info("Initializing OpenClaw Elite...")
        self.start_time = asyncio.get_event_loop().time()

        # Initialize databases
        init_db()
        init_elite_memory()

        # Validate config
        errors = Config.validate()
        if errors:
            logger.error(f"Configuration errors: {errors}")

        # Initialize specialist agents (legacy)
        for agent_id, agent_class in AGENT_MAP.items():
            try:
                self.agents[agent_id] = agent_class()
                logger.info(f"Agent {agent_id} initialized")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_id}: {e}")

        # Initialize gateways
        await self._init_gateways()

        # Start monitoring
        self.monitoring.start_all()

        # Log startup
        logger.info("OpenClaw Elite initialized successfully")

    async def _init_gateways(self):
        """Initialize all platform gateways."""
        # Telegram (supports up to 3 bots)
        telegram_tokens = [
            os.environ.get("TELEGRAM_BOT1_TOKEN", ""),
            os.environ.get("TELEGRAM_BOT2_TOKEN", ""),
            os.environ.get("TELEGRAM_BOT3_TOKEN", ""),
        ]
        if any(telegram_tokens):
            try:
                self.gateways["telegram"] = TelegramGateway(self)
                active_bots = sum(1 for t in telegram_tokens if t)
                logger.info(f"Telegram Gateway initialized ({active_bots} bot(s))")
            except Exception as e:
                logger.error(f"Failed to init Telegram: {e}")

        # Discord
        if Config.DISCORD_TOKEN:
            try:
                self.gateways["discord"] = DiscordGateway(self)
                logger.info("Discord Gateway initialized")
            except Exception as e:
                logger.error(f"Failed to init Discord: {e}")

        # Slack
        if Config.SLACK_BOT_TOKEN and Config.SLACK_APP_TOKEN:
            try:
                self.gateways["slack"] = SlackGateway(self)
                logger.info("Slack Gateway initialized")
            except Exception as e:
                logger.error(f"Failed to init Slack: {e}")

    async def route_message(self, platform: str, user_id: str, username: str,
                           message: str, channel_id: str) -> str:
        """Route incoming message through the full Elite pipeline."""
        logger.info(f"[{platform}] {username}: {message}")

        # Use task dispatcher for all platforms
        try:
            task_id = await submit_task(
                message,
                agent="orchestrator",
                requester=f"{platform}:{username}",
                channel_id=channel_id
            )

            result = await execute_task(task_id)

            # Send response back
            await self._send_response(platform, channel_id, result, task_id)

            return task_id

        except Exception as e:
            logger.error(f"Task dispatch failed: {e}", exc_info=True)
            await self._send_response(
                platform, channel_id,
                f"❌ Error processing your request: {str(e)[:500]}",
                None
            )
            return f"error_{uuid.uuid4().hex[:8]}"

    async def _send_response(self, platform: str, channel_id: str, content: str, task_id: str = None):
        """Send response through appropriate gateway."""
        gateway = self.gateways.get(platform)
        if gateway:
            try:
                await gateway.send_message(channel_id, content, task_id)
            except Exception as e:
                logger.error(f"Failed to send response via {platform}: {e}")

    def get_stats(self) -> dict:
        """Get system statistics."""
        uptime = asyncio.get_event_loop().time() - self.start_time if self.start_time else 0
        return {
            "uptime_seconds": int(uptime),
            "gateways": list(self.gateways.keys()),
            "agents": list(self.agents.keys()),
            "dispatch_agents": list(AGENT_DISPATCH.keys()),
            "tasks_total": len(self.memory.get_open_tasks()),
            "tasks_done": len([t for t in self.memory.get_open_tasks() if t["status"] == "completed"]),
            "tasks_failed": len([t for t in self.memory.get_open_tasks() if t["status"] == "failed"]),
            "pending_approvals": len(self.approval.get_pending()),
            "monitoring_status": self.monitoring.get_status()
        }

    async def start(self):
        """Start the Elite system."""
        await self.initialize()

        # Start all gateways
        tasks = []
        for name, gateway in self.gateways.items():
            tasks.append(asyncio.create_task(gateway.start()))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Keep alive if no gateways
            logger.warning("No gateways configured. Bot is idle.")
            logger.info("Set DISCORD_TOKEN, TELEGRAM_BOT1_TOKEN, or SLACK_BOT_TOKEN to activate.")
            while True:
                await asyncio.sleep(3600)

async def main():
    """Main entry point."""
    elite = OpenClawElite()
    await elite.start()

if __name__ == "__main__":
    asyncio.run(main())
