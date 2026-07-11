"""Empire Mesh - Multi-cloud health monitoring and node coordination."""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List

EMPIRE_NODES = [
    {"name": "Render Primary", "url": "https://openclaw-bot.onrender.com/health", "region": "us-east"},
    {"name": "OCI Worker", "url": "http://OCI_PLACEHOLDER:8000/health", "region": "oracle-cloud"},
]

class EmpireMesh:
    def __init__(self):
        self.node_status: Dict[str, dict] = {}
        self.last_check = None

    async def health_check(self) -> Dict:
        """Check all empire nodes."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for node in EMPIRE_NODES:
                tasks.append(self._check_node(session, node))
            results = await asyncio.gather(*tasks, return_exceptions=True)

        self.node_status = {r["name"]: r for r in results if isinstance(r, dict)}
        self.last_check = datetime.utcnow().isoformat()
        return self.node_status

    async def _check_node(self, session: aiohttp.ClientSession, node: dict) -> dict:
        try:
            async with session.get(node["url"], timeout=10) as resp:
                return {
                    "name": node["name"],
                    "region": node["region"],
                    "status": "ONLINE" if resp.status == 200 else "DEGRADED",
                    "code": resp.status,
                    "url": node["url"],
                    "checked_at": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "name": node["name"],
                "region": node["region"],
                "status": "OFFLINE",
                "error": str(e),
                "url": node["url"],
                "checked_at": datetime.utcnow().isoformat()
            }

    def get_summary(self) -> str:
        lines = ["=== EMPIRE MESH STATUS ===", f"Last check: {self.last_check}", ""]
        for name, status in self.node_status.items():
            emoji = "🟢" if status["status"] == "ONLINE" else "🔴"
            lines.append(f"{emoji} {name} ({status['region']}): {status['status']}")
        return "\n".join(lines)
