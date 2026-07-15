"""GBaby — Growth Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class GBabyAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("GBaby", "growth", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = f"As the growth marketer, plan the marketing strategy for: {task}"
        result = self._think(prompt, context, max_tokens=2000)
        return result
