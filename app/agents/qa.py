"""QA Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class QAAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("QA", "qa", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        prompt = f"As the QA engineer, test and validate: {task}"
        return self._think(prompt, context, max_tokens=2000)
