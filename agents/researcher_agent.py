from agents.base_agent import BaseAgent
from typing import Dict, Any
class ResearcherAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1; self.status = "working"
        return f"🔬 Researcher Agent at your service.\nQuery: *{message}*\n_Context: {context.get('platform', 'unknown')}_"
