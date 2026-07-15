"""OpenClaw Empire — Master Orchestrator"""
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.core.logger import logger
from app.brain.ai_client import AIBrain
from app.agents.base import BaseAgent


class OrchestratorAgent(BaseAgent):
    """Routes tasks to appropriate specialist agents."""

    def __init__(self, brain: Optional[AIBrain] = None):
        super().__init__("Bob", "orchestrator", brain)
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Dict] = []
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []

    def register_agent(self, agent: BaseAgent):
        """Register a specialist agent."""
        self.agents[agent.name.lower()] = agent
        logger.info(f"[ORCHESTRATOR] Registered agent: {agent.name}")

    def classify_intent(self, message: str) -> str:
        """Classify user intent and return agent name."""
        msg = message.lower()

        if any(k in msg for k in ["deploy", "server", "infrastructure", "docker", "ci/cd", "github"]):
            return "dave"
        if any(k in msg for k in ["code", "write", "function", "bug", "fix", "pr", "review"]):
            return "coder"
        if any(k in msg for k in ["content", "youtube", "blog", "seo", "social", "video", "script"]):
            return "carla"
        if any(k in msg for k in ["revenue", "money", "income", "passive", "affiliate", "product", "business"]):
            return "alice"
        if any(k in msg for k in ["research", "trend", "market", "competitor", "analyze", "data"]):
            return "researcher"
        if any(k in msg for k in ["security", "audit", "vulnerability", "scan", "permission"]):
            return "security"
        if any(k in msg for k in ["test", "qa", "quality", "verify", "validate", "check"]):
            return "qa"
        if any(k in msg for k in ["growth", "marketing", "traffic", "conversion", "users", "seo"]):
            return "gbaby"

        return "gbaby"  # Default

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Process a goal through the full pipeline."""
        task_id = f"task_{int(time.time())}_{random.randint(1000,9999)}"
        logger.info(f"[ORCHESTRATOR] Processing goal #{task_id}: {task[:80]}")

        # Step 1: Classify
        agent_name = self.classify_intent(task)
        logger.info(f"[ORCHESTRATOR] Routed to agent: {agent_name}")

        # Step 2: Execute with agent
        agent = self.agents.get(agent_name)
        if not agent:
            logger.warning(f"[ORCHESTRATOR] Agent {agent_name} not found, using self")
            agent = self

        try:
            result = await agent.execute(task, context)
            self.completed_tasks.append(task_id)
            logger.info(f"[ORCHESTRATOR] Task #{task_id} completed")
            return f"✅ **{agent.name}** completed task #{task_id}\n\n{result[:1500]}"
        except Exception as e:
            self.failed_tasks.append(task_id)
            logger.error(f"[ORCHESTRATOR] Task #{task_id} failed: {e}")
            return f"❌ Task #{task_id} failed: {str(e)}"

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "registered_agents": list(self.agents.keys()),
            "queue_length": len(self.task_queue),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks)
        })
        return status
