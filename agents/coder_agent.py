from agents.base_agent import BaseAgent
from typing import Dict, Any

class CoderAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"

        if self.brain.is_configured():
            response = self._think(message, context, max_tokens=4096)
            self.status = "idle"
            return f"🧑‍💻 **Coder Agent**\n\n{response}"

        self.status = "idle"
        return f"🧑‍💻 Coder Agent here!\nYou asked: *{message}*\n_Context: {context.get('platform', 'unknown')}_"
