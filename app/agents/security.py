"""Security Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class SecurityAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Security", "security", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = f"As the security auditor, scan and report on: {task}"
        result = self._think(prompt, context, max_tokens=2000)
        return result
