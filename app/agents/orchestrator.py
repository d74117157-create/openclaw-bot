"""OpenClaw Empire — Master Orchestrator (with QA Review Pipeline)

Every important task follows:
User Goal → Viktor → Worker Agent → QA Agent Review → Verification → Final Response
"""
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.core.logger import logger
from app.brain.ai_client import AIBrain
from app.agents.base import BaseAgent


class OrchestratorAgent(BaseAgent):
    """Routes tasks to appropriate specialist agents with QA review."""

    def __init__(self, brain: Optional[AIBrain] = None):
        super().__init__("Bob", "orchestrator", brain)
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Dict] = []
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.qa_agent: Optional[BaseAgent] = None

    def register_agent(self, agent: BaseAgent):
        """Register a specialist agent."""
        self.agents[agent.name.lower()] = agent
        if agent.agent_type == "qa":
            self.qa_agent = agent
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

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a goal through the full pipeline with QA review."""
        task_id = f"task_{int(time.time())}_{random.randint(1000,9999)}"
        logger.info(f"[ORCHESTRATOR] Processing goal #{task_id}: {task[:80]}")

        # Step 1: Classify
        agent_name = self.classify_intent(task)
        logger.info(f"[ORCHESTRATOR] Routed to agent: {agent_name}")

        # Step 2: Execute with worker agent
        agent = self.agents.get(agent_name)
        if not agent:
            logger.warning(f"[ORCHESTRATOR] Agent {agent_name} not found, using self")
            agent = self

        try:
            agent_result = await agent.execute(task, context)

            # Step 3: QA Review (if QA agent available)
            qa_review = None
            if self.qa_agent and hasattr(self.qa_agent, 'review'):
                logger.info(f"[ORCHESTRATOR] Sending to QA review")
                qa_review = await self.qa_agent.review(agent_result, task)

                # If QA rejects, try once more with feedback
                if not qa_review.get("approved", True):
                    logger.warning(f"[ORCHESTRATOR] QA rejected — retrying with feedback")
                    feedback = qa_review.get("review", {}).get("response", "")
                    retry_task = f"{task}\n\nQA Feedback: {feedback[:500]}"
                    agent_result = await agent.execute(retry_task, context)
                    qa_review = await self.qa_agent.review(agent_result, task)

            self.completed_tasks.append(task_id)

            # Build verified response
            response_text = agent_result.get("response", "")
            confidence = agent_result.get("confidence", 0)
            verification_status = agent_result.get("verification_status", "unverified")
            warnings = agent_result.get("warnings", [])
            validation = agent_result.get("validation", {})

            # Never say "Done" without proof
            if verification_status in ["suspected_hallucination", "needs_human_review"]:
                final_status = "needs_review"
                response_text = f"⚠️ **This response requires human review**\n\nConfidence: {confidence}\nWarnings: {', '.join(warnings)}\n\n{response_text}"
            elif not validation.get("is_valid", True):
                final_status = "unverified"
                response_text = f"⚠️ **Unverified completion claim**\n\n{validation.get('recommendation', '')}\n\n{response_text}"
            else:
                final_status = "completed"

            logger.info(f"[ORCHESTRATOR] Task #{task_id} {final_status}")

            return {
                "task_id": task_id,
                "status": final_status,
                "agent": agent_name,
                "confidence": confidence,
                "verification_status": verification_status,
                "validation": validation,
                "warnings": warnings,
                "qa_review": qa_review,
                "result": response_text,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.failed_tasks.append(task_id)
            logger.error(f"[ORCHESTRATOR] Task #{task_id} failed: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "agent": agent_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "registered_agents": list(self.agents.keys()),
            "queue_length": len(self.task_queue),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks)
        })
        return status
