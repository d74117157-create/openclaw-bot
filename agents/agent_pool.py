"""AgentPool — manages all AI agents."""
import asyncio, logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from agents.coder_agent import CoderAgent
from agents.researcher_agent import ResearcherAgent
from agents.ops_agent import OpsAgent
from agents.growth_agent import GrowthAgent
from agents.qa_agent import QAAgent
from agents.orchestrator_agent import OrchestratorAgent
logger = logging.getLogger("openclaw.agents")

class AgentPool:
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self._running = False
        self._message_queue = asyncio.Queue()
        self._tasks: List[asyncio.Task] = []
        self.status = {"agents": {}, "total_messages": 0, "uptime": 0}

    async def start(self):
        self._running = True
        agent_classes = {"orchestrator": OrchestratorAgent, "coder": CoderAgent, "researcher": ResearcherAgent, "ops": OpsAgent, "growth": GrowthAgent, "qa": QAAgent}
        for name, cls in agent_classes.items():
            agent = cls(name=name)
            self.agents[name] = agent
            self.status["agents"][name] = {"status": "idle", "messages_handled": 0}
            logger.info(f"Agent '{name}' initialized.")
        self._tasks.append(asyncio.create_task(self._heartbeat()))
        self._tasks.append(asyncio.create_task(self._process_messages()))
        logger.info(f"Agent pool started with {len(self.agents)} agents.")

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        logger.info("Agent pool stopped.")

    async def reload(self):
        for agent in self.agents.values(): await agent.reload()

    async def handle_message(self, platform: str, user_id: str, username: str, content: str, channel_id: str) -> Optional[str]:
        await self._message_queue.put({"platform": platform, "user_id": user_id, "username": username, "content": content, "channel_id": channel_id, "timestamp": datetime.utcnow().isoformat()})
        self.status["total_messages"] += 1
        if any(kw in content.lower() for kw in ["code","python","bug","fix","deploy"]): return await self.agents["coder"].respond(content, {"user": username, "platform": platform})
        elif any(kw in content.lower() for kw in ["research","find","search","data"]): return await self.agents["researcher"].respond(content, {"user": username, "platform": platform})
        elif any(kw in content.lower() for kw in ["status","health","server","down"]): return await self.agents["ops"].respond(content, {"user": username, "platform": platform})
        elif any(kw in content.lower() for kw in ["growth","marketing","users","analytics"]): return await self.agents["growth"].respond(content, {"user": username, "platform": platform})
        else: return await self.agents["orchestrator"].respond(content, {"user": username, "platform": platform})

    async def direct_query(self, query: str, platform: str) -> str:
        return await self.agents["orchestrator"].respond(query, {"platform": platform, "direct": True})

    async def _heartbeat(self):
        while self._running:
            for name in self.agents: self.status["agents"][name]["status"] = "alive"
            await asyncio.sleep(30)
    async def _process_messages(self):
        while self._running:
            try: msg = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
            except asyncio.TimeoutError: continue
