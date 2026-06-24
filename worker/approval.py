"""
OpenClaw Elite — Approval Framework
Safe actions proceed automatically. Risky actions require explicit approval.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

from memory.elite_memory import get_memory

logger = logging.getLogger("approval")

class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"


# Action classification
SAFE_ACTIONS = {
    "research", "reading_files", "planning", "analysis", "query", "search",
    "summarize", "explain", "suggest", "recommend", "draft", "preview",
    "status_check", "monitoring", "reporting", "log_review", "conversation",
    "explain_code", "review_code", "suggest_improvement", "generate_plan"
}

CAUTION_ACTIONS = {
    "deploy_staging", "create_branch", "create_pr", "create_issue",
    "update_config", "modify_file", "run_tests", "lint_code"
}

DANGEROUS_ACTIONS = {
    "deploy_production", "delete_data", "delete_branch", "force_push",
    "modify_credentials", "rotate_keys", "update_secrets", "external_messaging",
    "financial_transaction", "destructive_git_operation"
}


class ApprovalRequest:
    """Represents a request requiring approval."""

    def __init__(self, action: str, details: dict, requester: str, risk_level: RiskLevel):
        self.id = f"approval_{hash(json.dumps(details, sort_keys=True)) % 1000000}"
        self.action = action
        self.details = details
        self.requester = requester
        self.risk_level = risk_level
        self.status = "pending"
        self.created_at = datetime.utcnow().isoformat()
        self.approved_at = None
        self.approved_by = None
        self.denied_at = None
        self.denied_reason = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "details": self.details,
            "requester": self.requester,
            "risk_level": self.risk_level.value,
            "status": self.status,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "denied_at": self.denied_at,
            "denied_reason": self.denied_reason
        }


class ApprovalFramework:
    """Manages approval workflow for risky actions."""

    def __init__(self):
        self.pending_requests = {}
        self.approved_requests = {}
        self.denied_requests = {}
        self.auto_approve_safe = True
        self.memory = get_memory()

    def assess_action(self, action: str, details: dict = None) -> dict:
        """Assess if an action requires approval."""
        details = details or {}

        # Check explicit action classification
        if action in SAFE_ACTIONS:
            return {
                "requires_approval": False,
                "risk_level": RiskLevel.SAFE.value,
                "reason": "Action is in safe actions list",
                "auto_approved": self.auto_approve_safe
            }

        if action in DANGEROUS_ACTIONS:
            return {
                "requires_approval": True,
                "risk_level": RiskLevel.DANGEROUS.value,
                "reason": "Action is in dangerous actions list — explicit approval required",
                "auto_approved": False
            }

        if action in CAUTION_ACTIONS:
            return {
                "requires_approval": True,
                "risk_level": RiskLevel.CAUTION.value,
                "reason": "Action is in caution list — approval recommended",
                "auto_approved": False
            }

        # Default: assess based on details
        return self._heuristic_assess(action, details)

    def _heuristic_assess(self, action: str, details: dict) -> dict:
        """Heuristic risk assessment for unclassified actions."""
        details_str = json.dumps(details).lower()

        dangerous_indicators = ["production", "prod", "live", "delete", "remove", "purge", 
                                "credential", "secret", "token", "password", "force"]
        caution_indicators = ["deploy", "push", "merge", "modify", "update", "change"]

        if any(ind in details_str for ind in dangerous_indicators):
            return {
                "requires_approval": True,
                "risk_level": RiskLevel.DANGEROUS.value,
                "reason": "Dangerous keywords detected in action details",
                "auto_approved": False
            }

        if any(ind in details_str for ind in caution_indicators):
            return {
                "requires_approval": True,
                "risk_level": RiskLevel.CAUTION.value,
                "reason": "Caution keywords detected in action details",
                "auto_approved": False
            }

        return {
            "requires_approval": False,
            "risk_level": RiskLevel.SAFE.value,
            "reason": "No risk indicators detected",
            "auto_approved": self.auto_approve_safe
        }

    def request_approval(self, action: str, details: dict, requester: str = "system") -> ApprovalRequest:
        """Create an approval request."""
        assessment = self.assess_action(action, details)
        risk_level = RiskLevel(assessment["risk_level"])

        req = ApprovalRequest(action, details, requester, risk_level)
        self.pending_requests[req.id] = req

        # Store in memory
        self.memory.store_task(
            task_id=req.id,
            description=f"Approval request: {action}",
            agent="approval_framework",
            priority="high",
            context={"approval_request": req.to_dict()}
        )

        logger.info(f"Approval requested: {req.id} for action '{action}' ({risk_level.value})")
        return req

    def approve(self, approval_id: str, approver: str = "user") -> dict:
        """Approve a pending request."""
        if approval_id not in self.pending_requests:
            return {"error": "Approval request not found"}

        req = self.pending_requests.pop(approval_id)
        req.status = "approved"
        req.approved_at = datetime.utcnow().isoformat()
        req.approved_by = approver
        self.approved_requests[approval_id] = req

        # Update memory
        self.memory.update_task(approval_id, status="approved")

        logger.info(f"Approval granted: {approval_id} by {approver}")
        return {"success": True, "request": req.to_dict()}

    def deny(self, approval_id: str, reason: str = "No reason provided") -> dict:
        """Deny a pending request."""
        if approval_id not in self.pending_requests:
            return {"error": "Approval request not found"}

        req = self.pending_requests.pop(approval_id)
        req.status = "denied"
        req.denied_at = datetime.utcnow().isoformat()
        req.denied_reason = reason
        self.denied_requests[approval_id] = req

        # Update memory
        self.memory.update_task(approval_id, status="denied")

        logger.info(f"Approval denied: {approval_id} — {reason}")
        return {"success": True, "request": req.to_dict()}

    def get_pending(self) -> List[dict]:
        """Get all pending approval requests."""
        return [req.to_dict() for req in self.pending_requests.values()]

    def get_history(self, limit: int = 50) -> List[dict]:
        """Get approval history."""
        all_reqs = list(self.approved_requests.values()) + list(self.denied_requests.values())
        all_reqs.sort(key=lambda x: x.created_at, reverse=True)
        return [req.to_dict() for req in all_reqs[:limit]]


# Singleton
_approval_framework = None

def get_approval_framework() -> ApprovalFramework:
    global _approval_framework
    if _approval_framework is None:
        _approval_framework = ApprovalFramework()
    return _approval_framework
