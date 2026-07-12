"""Base class for all AI agents — now with real AI brain."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from ai_brain import get_brain

logger = logging.getLogger("openclaw.agent")

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.status = "idle"
        self.messages_handled = 0
        self.brain = get_brain()

    @abstractmethod
    async def respond(self, message: str, context: Dict[str, Any]) -> str: pass

    async def reload(self): 
        logger.info(f"Agent '{self.name}' reloaded.")

    def _think(self, message: str, context: Dict[str, Any], max_tokens: int = 1024) -> str:
        """Use the AI brain to generate a real response."""
        return self.brain.think(message, agent_type=self.name, context=context, max_tokens=max_tokens)
