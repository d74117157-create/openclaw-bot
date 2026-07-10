"""Base class for all AI agents."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
logger = logging.getLogger("openclaw.agent")

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.status = "idle"
        self.messages_handled = 0
    @abstractmethod
    async def respond(self, message: str, context: Dict[str, Any]) -> str: pass
    async def reload(self): logger.info(f"Agent '{self.name}' reloaded.")
