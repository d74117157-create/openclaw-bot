from agents.base_agent import BaseAgent
from typing import Dict, Any
import os

class CoderAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"
        files = []
        try:
            for root, _, filenames in os.walk("."):
                for f in filenames:
                    if f.endswith(".py"):
                        files.append(os.path.join(root, f))
        except:
            pass
        file_list = "\n".join(files[:20]) if files else "No Python files found."
        if self.brain.is_configured():
            prompt = f"""You are the Coder Agent. User request: {message}

Repository files found:
{file_list}

If the user wants code, provide it. If they want a fix, analyze the file. Be specific."""
            response = self._think(prompt, context, max_tokens=4096)
            self.status = "idle"
            return f"🧑‍💻 **Coder Agent** (Real Mode)\n\n{response}\n\n_Repo files: {len(files)} found_"
        self.status = "idle"
        return f"🧑‍💻 Coder Agent (standby)\nFiles in repo: {len(files)}\nQuery: {message}"
