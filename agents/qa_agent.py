from agents.base_agent import BaseAgent
from typing import Dict, Any
class QAAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1; self.status = "working"
        return f"🧪 QA Agent online.\nQuery: *{message}*\n_Context: {context.get('platform', 'unknown')}_"
