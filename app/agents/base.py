"""OpenClaw Empire — Base Agent (with Verification Layer)"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.brain.ai_client import AIBrain
from app.verification.truth_checker import TruthChecker
from app.verification.completion_validator import CompletionValidator


class BaseAgent(ABC):
    """Abstract base class for all swarm agents — now with verification."""

    def __init__(self, name: str, agent_type: str, brain: Optional[AIBrain] = None):
        self.name = name
        self.agent_type = agent_type
        self.brain = brain
        self.status = "idle"
        self.messages_handled = 0
        self.last_action = None
        self.created_at = datetime.utcnow().isoformat()
        self.truth_checker = TruthChecker()
        self.validator = CompletionValidator()
        logger.info(f"[AGENT] {name} ({agent_type}) initialized with verification")

    def is_ready(self) -> bool:
        return self.status == "idle" or self.status == "online"

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute a task. Must be implemented by subclasses."""
        pass

    def _think(self, prompt: str, context: Dict[str, Any] = None, max_tokens: int = 2000) -> Dict[str, Any]:
        """Use AI brain to process a prompt with verification."""
        if not self.brain or not self.brain.is_configured():
            return {
                "response": f"[{self.name}] AI brain not configured. Cannot process: {prompt[:50]}...",
                "confidence": 0.0,
                "verification_status": "needs_human_review",
                "evidence": [],
                "warnings": ["AI brain not configured"]
            }

        self.status = "working"
        try:
            raw_response = self.brain.chat(prompt, agent_type=self.agent_type, max_tokens=max_tokens)
            truth_report = self.truth_checker.check(raw_response, self.name, self.agent_type)
            validation = self.validator.validate(self.agent_type, raw_response, context)

            self.messages_handled += 1
            self.last_action = {
                "task": prompt[:100],
                "result": raw_response[:200],
                "confidence": truth_report.confidence_score,
                "verification": truth_report.verification_status,
                "time": datetime.utcnow().isoformat()
            }

            return {
                "response": raw_response,
                "confidence": truth_report.confidence_score,
                "verification_status": truth_report.verification_status,
                "evidence": truth_report.evidence_used,
                "warnings": truth_report.warnings,
                "unsupported_claims": truth_report.unsupported_claims,
                "validation": {
                    "is_valid": validation.is_valid,
                    "checks_passed": validation.checks_passed,
                    "checks_failed": validation.checks_failed,
                    "recommendation": validation.recommendation
                }
            }
        finally:
            self.status = "idle"

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "messages_handled": self.messages_handled,
            "last_action": self.last_action,
            "created_at": self.created_at
        }
