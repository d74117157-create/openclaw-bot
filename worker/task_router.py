"""
OpenClaw Task Router
Routes user requests to specific agent handlers.
"""
import logging
import json
from typing import Any
from shared.config import Config

logger = logging.getLogger("task_router")

class TaskRouter:
    """Simple router for handling user messages."""
    
    def __init__(self, swarm):
        self.swarm = swarm
        
    async def handle(self, message: str) -> str:
        """Route message to appropriate logic."""
        msg = message.lower().strip()
        
        if msg == "status" or msg == "/status":
            stats = self.swarm.get_stats()
            return (
                "🧠 *OpenClaw Master Brain Status*\n\n"
                f"⏱ Uptime: {int(stats['uptime_seconds'])}s\n"
                f"🌐 Platforms: {', '.join(stats['gateways'])}\n"
                f"📊 Total Tasks: {stats['tasks_total']}\n"
                f"✅ Completed: {stats['tasks_done']}\n"
                f"❌ Failed: {stats['tasks_failed']}"
            )
            
        if msg == "help" or msg == "/help":
            return (
                "🤖 *OpenClaw Master Brain Help*\n\n"
                "Available Commands:\n"
                "• `status` - Show system health\n"
                "• `agents` - List active agents\n"
                "• `deploy <repo>` - Deploy code\n"
                "• Any question - Ask the AI swarm"
            )

        if msg.startswith("deploy"):
            return "🚀 Deployment module triggered. Checking repository..."

        # Default: Route to LLM
        return await self._call_llm(message)

    async def _call_llm(self, prompt: str) -> str:
        """Call the primary LLM configured in the brain."""
        try:
            llm_config = Config.get_llm_config()
            # Placeholder for actual LLM call logic
            # In a real scenario, we would use openai or groq client here
            return f"🧠 Brain processed: {prompt}\n\n(LLM Response Placeholder - Provider: {llm_config['provider']})"
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"❌ LLM Error: {e}"
