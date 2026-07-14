from agents.base_agent import BaseAgent
from typing import Dict, Any
import os

class ResearcherAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"
        reports_dir = "assets/research"
        reports = []
        if os.path.exists(reports_dir):
            reports = [f for f in os.listdir(reports_dir) if f.endswith(".md")]
        if self.brain.is_configured():
            response = self._think(message, context, max_tokens=4096)
            self.status = "idle"
            return f"🔬 **Researcher Agent**\n\n{response}\n\n_Archive: {len(reports)} reports_"
        self.status = "idle"
        return f"🔬 Researcher Agent\nReports archive: {len(reports)}\nQuery: {message}"
