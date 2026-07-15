"""Alice — Business Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class AliceAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Alice", "business", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        prompt = f"As the business strategist, analyze this revenue opportunity: {task}"
        return self._think(prompt, context, max_tokens=2000)
