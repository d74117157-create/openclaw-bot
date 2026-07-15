"""OpenClaw Empire — Base Agent"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.brain.ai_client import AIBrain


class BaseAgent(ABC):
    """Abstract base class for all swarm agents."""

    def __init__(self, name: str, agent_type: str, brain: Optional[AIBrain] = None):
        self.name = name
        self.agent_type = agent_type
        self.brain = brain
        self.status = "idle"
        self.messages_handled = 0
        self.last_action = None
        self.created_at = datetime.utcnow().isoformat()
        logger.info(f"[AGENT] {name} ({agent_type}) initialized")

    def is_ready(self) -> bool:
        return self.status == "idle" or self.status == "online"

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute a task. Must be implemented by subclasses."""
        pass

    def _think(self, prompt: str, context: Dict[str, Any] = None, max_tokens: int = 2000) -> str:
        """Use AI brain to process a prompt."""
        if not self.brain or not self.brain.is_configured():
            return f"[{self.name}] AI brain not configured. Cannot process: {prompt[:50]}..."

        self.status = "working"
        try:
            result = self.brain.chat(prompt, agent_type=self.agent_type, max_tokens=max_tokens)
            self.messages_handled += 1
            self.last_action = {"task": prompt[:100], "result": result[:200], "time": datetime.utcnow().isoformat()}
            return result
        finally:
            self.status = "idle"

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "messages_handled": self.messages_handled,
            "last_action": self.last_action,
            "created_at": self.created_at
        }
