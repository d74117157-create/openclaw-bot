from agents.base_agent import BaseAgent
from typing import Dict, Any

class OrchestratorAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"

        if self.brain.is_configured():
            response = self._think(message, context, max_tokens=2048)
            self.status = "idle"
            return response

        # Fallback if no AI configured
        self.status = "idle"
        return f"🐝 **OpenClaw Orchestrator** (standby mode)\n\nYour message: *{message}*\n\nAgents: Coder 🧑‍💻 | Researcher 🔬 | Ops 🛠️ | Growth 📈 | QA 🧪\n_Context: {context.get('platform', 'unknown')}_\n\n⚠️ No AI brain configured. Set GROQ_API_KEY or GROK_API_KEY in env vars."
