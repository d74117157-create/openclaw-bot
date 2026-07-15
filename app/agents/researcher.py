"""Research Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class ResearcherAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Researcher", "researcher", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = f"As the research analyst, deep-dive into: {task}"
        result = self._think(prompt, context, max_tokens=3000)
        return result
