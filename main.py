#!/usr/bin/env python3
"""
OpenClaw Master Brain — Unified Swarm Controller
Controls Telegram, Discord, Slack, and AI Agents from one place.
"""
import os
import asyncio
import logging
import sys
from typing import Dict, Any

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.config import Config
from shared.logging import setup_logging, get_logger
from memory.db import init_db, save_task, update_task, get_stats
from gateway.telegram_bot import TelegramGateway
from gateway.discord_bot import DiscordGateway
from gateway.slack_bot import SlackGateway
from worker.task_router import TaskRouter

# Setup logging
setup_logging("openclaw")
logger = get_logger("master_brain")

class OpenClawSwarm:
    """The unified swarm coordinator."""
    
    def __init__(self):
        self.config = Config()
        self.gateways = {}
        self.agents = {}
        self.router = TaskRouter(self)
        self.start_time = 0
        
    async def initialize(self):
        """Initialize memory and all components."""
        logger.info("🧠 Initializing OpenClaw Master Brain...")
        self.start_time = asyncio.get_event_loop().time()
        init_db()
        Config.log_config()
        
        # Validate config
        errors = Config.validate()
        if errors:
            logger.error(f"❌ Configuration errors: {errors}")
            
        # Initialize Gateways
        if Config.TELEGRAM_BOT1_TOKEN or Config.TELEGRAM_BOT2_TOKEN:
            try:
                self.gateways["telegram"] = TelegramGateway(self)
                logger.info("✅ Telegram Gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to init Telegram: {e}")

        if Config.DISCORD_TOKEN:
            try:
                self.gateways["discord"] = DiscordGateway(self)
                logger.info("✅ Discord Gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to init Discord: {e}")

        if Config.SLACK_BOT_TOKEN:
            try:
                self.gateways["slack"] = SlackGateway(self)
                logger.info("✅ Slack Gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to init Slack: {e}")

    async def route_message(self, platform: str, user_id: str, username: str, message: str, channel_id: str) -> str:
        """Route incoming messages to the AI swarm."""
        logger.info(f"📩 [{platform}] {username}: {message}")
        
        # Save task to memory
        task_id = save_task(
            desc=message,
            agent="orchestrator",
            platform=platform,
            user_id=user_id
        )
        
        # Async processing
        asyncio.create_task(self.process_task(task_id, platform, channel_id, message))
        
        return task_id

    async def process_task(self, task_id: str, platform: str, channel_id: str, message: str):
        """Process the task using AI workers and respond."""
        try:
            # Simple routing for now, can be expanded to full swarm orchestration
            result = await self.router.handle(message)
            
            # Update memory
            update_task(task_id, result, "done")
            
            # Deliver response back to the platform
            await self.deliver_response(platform, channel_id, result, task_id)
            
        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}")
            update_task(task_id, str(e), "failed")
            await self.deliver_response(platform, channel_id, f"Error: {e}", task_id)

    async def deliver_response(self, platform: str, channel_id: str, content: str, task_id: str):
        """Deliver the result back to the user on the original platform."""
        gateway = self.gateways.get(platform)
        if gateway:
            await gateway.send_message(channel_id, content, task_id)
        else:
            logger.error(f"Gateway for {platform} not found")

    def get_stats(self) -> Dict[str, Any]:
        """Get swarm health and statistics."""
        db_stats = get_stats()
        return {
            "uptime_seconds": asyncio.get_event_loop().time() - self.start_time,
            "gateways": list(self.gateways.keys()),
            "tasks_total": db_stats.get("tasks_total", 0),
            "tasks_done": db_stats.get("tasks_done", 0),
            "tasks_failed": db_stats.get("tasks_failed", 0),
        }

async def main():
    """Main entry point."""
    swarm = OpenClawSwarm()
    await swarm.initialize()
    
    # Start all gateways
    tasks = []
    for name, gateway in swarm.gateways.items():
        logger.info(f"🚀 Starting {name} gateway...")
        tasks.append(asyncio.create_task(gateway.start()))
        
    if not tasks:
        logger.error("No gateways started. Check your environment variables.")
        # Don't exit, maybe web api or something else is running
        while True:
            await asyncio.sleep(3600)

    logger.info("🧠 OpenClaw Master Brain is ONLINE")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 OpenClaw shutting down...")
