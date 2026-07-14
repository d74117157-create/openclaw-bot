from agents.base_agent import BaseAgent
from typing import Dict, Any
import os

class GrowthAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"
        assets_dir = "assets/marketing"
        existing = []
        if os.path.exists(assets_dir):
            for root, _, files in os.walk(assets_dir):
                for f in files:
                    existing.append(os.path.join(root, f))
        if self.brain.is_configured():
            response = self._think(message, context, max_tokens=2048)
            self.status = "idle"
            return f"""📈 **Growth Agent** (Real Mode)

{response}

_Existing assets: {len(existing)} files_
_Assets dir: {assets_dir}_"""
        self.status = "idle"
        return f"📈 Growth Agent\nAssets created: {len(existing)}\nQuery: {message}"
