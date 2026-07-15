"""Dave — DevOps Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class DaveAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Dave", "ops", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        prompt = f"As the DevOps engineer, handle this infrastructure/deployment task: {task}"
        return self._think(prompt, context, max_tokens=2000)
