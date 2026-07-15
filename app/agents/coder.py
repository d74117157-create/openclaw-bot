"""Coder Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class CoderAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Coder", "coder", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = f"As the senior developer, write production-ready code for: {task}"
        result = self._think(prompt, context, max_tokens=4000)
        return result
