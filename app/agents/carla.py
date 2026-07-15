"""Carla — Content Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class CarlaAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Carla", "content", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = f"As the content creator, create this content: {task}"
        result = self._think(prompt, context, max_tokens=3000)
        return result
