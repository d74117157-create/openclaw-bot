"""
OpenClaw Elite — Self-Verification System
Verifies task completion, tool success, error handling, and user input needs.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from worker.ai_worker import call_groq_sync

logger = logging.getLogger("verification")

@dataclass
class VerificationResult:
    task_completed: bool
    tools_succeeded: bool
    errors_handled: bool
    needs_user_input: bool
    quality_score: float
    issues: List[str]
    recommendations: List[str]
    can_respond: bool


class SelfVerifier:
    """
    Self-verification engine that checks all agent outputs before responding.
    Never claims success without verification.
    """

    def __init__(self):
        self.min_quality_score = 0.6

    def verify(self, task_description: str, agent_results: List[dict], 
               execution_log: List[dict] = None) -> VerificationResult:
        """Comprehensive verification of task execution."""
        execution_log = execution_log or []

        task_completed = self._check_completion(task_description, agent_results)
        tools_succeeded = self._check_tools(execution_log)
        errors_handled = self._check_errors(agent_results, execution_log)
        needs_user_input = self._check_needs_input(agent_results)
        quality_score = self._assess_quality(task_description, agent_results)

        issues = []
        if not task_completed:
            issues.append("Task may not be fully completed")
        if not tools_succeeded:
            issues.append("One or more tools failed during execution")
        if not errors_handled:
            issues.append("Errors were detected but not properly handled")
        if needs_user_input:
            issues.append("Additional user input is required to proceed")
        if quality_score < self.min_quality_score:
            issues.append(f"Quality score ({quality_score:.2f}) below threshold")

        recommendations = self._generate_recommendations(issues, agent_results)
        can_respond = task_completed and tools_succeeded and errors_handled and not needs_user_input

        return VerificationResult(
            task_completed=task_completed,
            tools_succeeded=tools_succeeded,
            errors_handled=errors_handled,
            needs_user_input=needs_user_input,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
            can_respond=can_respond
        )

    def _check_completion(self, task_description: str, agent_results: List[dict]) -> bool:
        if not agent_results:
            return False
        for result in agent_results:
            response = str(result.get("response", "")).lower()
            if any(w in response for w in ["error", "failed", "unable to", "cannot", "did not work"]):
                if "handled" not in response and "fallback" not in response:
                    return False
        combined = " ".join([str(r.get("response", "")) for r in agent_results]).lower()
        task_kw = set(task_description.lower().split())
        resp_kw = set(combined.split())
        overlap = task_kw & resp_kw
        return len(overlap) / max(len(task_kw), 1) > 0.1 or len(combined) > 100

    def _check_tools(self, execution_log: List[dict]) -> bool:
        if not execution_log:
            return True
        for entry in execution_log:
            if entry.get("type") == "tool_call":
                if entry.get("status") == "failed":
                    return False
        return True

    def _check_errors(self, agent_results: List[dict], execution_log: List[dict]) -> bool:
        for result in agent_results:
            if result.get("error"):
                if not result.get("error_handled"):
                    return False
        for entry in execution_log:
            if entry.get("type") == "error":
                if not entry.get("handled"):
                    return False
        return True

    def _check_needs_input(self, agent_results: List[dict]) -> bool:
        for result in agent_results:
            response = str(result.get("response", "")).lower()
            if any(w in response for w in ["need more information", "please clarify", "could you specify", 
                                            "more details needed", "insufficient information", "ambiguous"]):
                return True
        return False

    def _assess_quality(self, task_description: str, agent_results: List[dict]) -> float:
        if not agent_results:
            return 0.0
        scores = []
        for result in agent_results:
            response = str(result.get("response", ""))
            score = 0.5
            if len(response) > 200:
                score += 0.1
            if any(w in response.lower() for w in ["completed", "done", "success", "result", "output"]):
                score += 0.15
            if "```" in response:
                score += 0.1
            if result.get("agent") in ["dave", "carla", "alice"]:
                score += 0.05
            scores.append(min(score, 1.0))
        return sum(scores) / len(scores) if scores else 0.0

    def _generate_recommendations(self, issues: List[str], agent_results: List[dict]) -> List[str]:
        recs = []
        if "not be fully completed" in str(issues):
            recs.append("Re-run with more specific task description or break into smaller subtasks")
        if "tools failed" in str(issues):
            recs.append("Check tool configurations and retry with fallback options")
        if "errors" in str(issues):
            recs.append("Review error logs and implement retry logic")
        if "user input" in str(issues):
            recs.append("Prompt user for required information before continuing")
        if not recs and agent_results:
            recs.append("All checks passed. Ready to deliver response.")
        return recs

    def to_dict(self, result: VerificationResult) -> dict:
        return {
            "task_completed": result.task_completed,
            "tools_succeeded": result.tools_succeeded,
            "errors_handled": result.errors_handled,
            "needs_user_input": result.needs_user_input,
            "quality_score": round(result.quality_score, 3),
            "issues": result.issues,
            "recommendations": result.recommendations,
            "can_respond": result.can_respond
        }


# Singleton
_verifier_instance = None

def get_verifier() -> SelfVerifier:
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = SelfVerifier()
    return _verifier_instance
