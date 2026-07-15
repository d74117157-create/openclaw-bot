"""Viktor — Strategic Reasoning Agent"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class ViktorAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("Viktor", "orchestrator", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        prompt = f"As the strategic leader, analyze this goal and create a high-level execution plan: {task}"
        return self._think(prompt, context, max_tokens=2000)
