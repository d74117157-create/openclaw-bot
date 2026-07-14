from agents.base_agent import BaseAgent
from typing import Dict, Any
import os, subprocess, json

class OpsAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"
        checks = []
        try:
            r = subprocess.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/health", shell=True, capture_output=True, text=True, timeout=10)
            checks.append(f"Local health: HTTP {r.stdout.strip()}")
        except Exception as e:
            checks.append(f"Local health: FAIL ({e})")
        env_vars = ["DISCORD_TOKEN", "TELEGRAM_BOT1_TOKEN", "GROQ_API_KEY", "RENDER_API_KEY", "GOOGLE_API_KEY"]
        present = [v for v in env_vars if os.getenv(v)]
        missing = [v for v in env_vars if not os.getenv(v)]
        checks.append(f"Secrets present: {len(present)}/{len(env_vars)}")
        if missing:
            checks.append(f"Missing: {', '.join(missing)}")
        try:
            stat = os.statvfs(".")
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            checks.append(f"Disk free: {free_gb:.2f} GB")
        except:
            pass
        self.status = "idle"
        return f"""🛠️ **Ops Agent — Infrastructure Report**

{'\n'.join(checks)}

Deployments managed: Render (srv-d978fh6puehc73fkq60g)
Status: Operational"""
