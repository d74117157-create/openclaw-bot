"""
Dave — Coding & Infrastructure Agent
Writes code, debugs, manages GitHub, handles deployments.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from worker.ai_worker import process_task, call_groq_sync
from memory.elite_memory import get_memory

logger = logging.getLogger("agent.dave")

DAVE_PERSONA = """You are Dave, the Coding and Infrastructure Agent for OpenClaw Elite.
Your responsibilities:
- Write clean, production-ready code
- Debug and fix errors
- Manage GitHub operations (PRs, issues, branches)
- Handle infrastructure (Docker, CI/CD, cloud)
- Execute deployments safely
- Review code for quality and security

Coding standards:
- Follow PEP 8 for Python
- Include docstrings and type hints
- Write defensive code with error handling
- Never commit secrets or credentials
- Add logging for observability
- Include unit tests where appropriate

When uncertain about production changes: STOP and ask for approval.
"""


class DaveAgent:
    """Dave — The technical execution engine of OpenClaw Elite."""

    def __init__(self):
        self.memory = get_memory()
        self.name = "Dave"
        self.role = "coding"
        self.github_token = os.environ.get("GITHUB_TOKEN", "")

    async def handle(self, message: str, context: dict = None) -> dict:
        context = context or {}
        task_type = self._classify_task(message)
        risk = self._assess_risk(message)

        result = None
        if task_type == "code_generation":
            result = self._generate_code(message, context)
        elif task_type == "debugging":
            result = self._debug(message, context)
        elif task_type == "github_operation":
            result = await self._github_op(message, context)
        elif task_type == "deployment":
            result = await self._deploy(message, context)
        elif task_type == "infrastructure":
            result = self._infrastructure(message, context)
        else:
            result = self._general_tech(message, context)

        self.memory.store_conversation(
            thread_id=context.get("thread_id", "default"),
            user_id=context.get("user_id", "unknown"),
            platform=context.get("platform", "unknown"),
            message=message,
            response=str(result)[:1000],
            intent=f"tech_{task_type}",
            agent="dave",
            confidence=0.90
        )

        return {
            "agent": "dave",
            "response": result,
            "type": task_type,
            "risk_level": risk["level"],
            "requires_approval": risk["requires_approval"],
            "code_blocks": self._extract_code(result)
        }

    def _classify_task(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["deploy", "release", "publish", "go live"]):
            return "deployment"
        if any(w in msg_lower for w in ["bug", "error", "fix", "debug", "broken", "crash"]):
            return "debugging"
        if any(w in msg_lower for w in ["github", "pr", "pull request", "issue", "branch", "commit", "merge"]):
            return "github_operation"
        if any(w in msg_lower for w in ["docker", "terraform", "kubernetes", "infra", "server", "cloud"]):
            return "infrastructure"
        if any(w in msg_lower for w in ["write", "create", "function", "class", "code", "script", "build"]):
            return "code_generation"
        return "general_tech"

    def _assess_risk(self, message: str) -> dict:
        msg_lower = message.lower()
        dangerous = ["production", "prod", "live", "main branch", "force push", "delete"]
        caution = ["deploy", "merge", "push", "modify", "update"]
        if any(w in msg_lower for w in dangerous):
            return {"level": "dangerous", "requires_approval": True}
        if any(w in msg_lower for w in caution):
            return {"level": "caution", "requires_approval": True}
        return {"level": "safe", "requires_approval": False}

    def _generate_code(self, message: str, context: dict) -> str:
        prompt = f"""Write production-ready code for the following request:
{message}
Requirements:
- Include docstrings
- Add type hints
- Handle edge cases
- Include basic error handling
- Add a usage example
- If this is a complete file, include a shebang and module docstring
Output the code in a code block. After the code, briefly explain how it works."""
        return call_groq_sync(DAVE_PERSONA, prompt)

    def _debug(self, message: str, context: dict) -> str:
        prompt = f"""Debug the following issue:
{message}
Approach:
1. Identify the root cause
2. Explain why it happens
3. Provide the fixed code
4. Suggest prevention strategies"""
        return call_groq_sync(DAVE_PERSONA, prompt)

    async def _github_op(self, message: str, context: dict) -> str:
        if not self.github_token:
            return "GitHub token not configured. Cannot perform GitHub operations."
        prompt = f"""Analyze this GitHub operation request and provide the exact steps:
{message}
Available operations: create_issue, create_pr, list_issues, list_prs, get_repo_info, create_branch
Respond with JSON:
{{"operation": "...", "params": {{...}}, "reasoning": "..."}}"""
        analysis = call_groq_sync(DAVE_PERSONA, prompt)
        try:
            start = analysis.find("{")
            end = analysis.rfind("}") + 1
            if start >= 0 and end > start:
                plan = json.loads(analysis[start:end])
                return f"GitHub operation planned: {plan['operation']}\nReasoning: {plan['reasoning']}\n\n(Execution would happen here with actual GitHub API calls)"
            return analysis
        except json.JSONDecodeError:
            return f"GitHub analysis:\n{analysis}"

    async def _deploy(self, message: str, context: dict) -> str:
        prompt = f"""Create a deployment plan for:
{message}
Include:
1. Pre-deployment checks
2. Deployment steps
3. Rollback strategy
4. Verification steps
5. Monitoring plan
NOTE: This is a plan only. Actual deployment requires explicit approval."""
        return call_groq_sync(DAVE_PERSONA, prompt)

    def _infrastructure(self, message: str, context: dict) -> str:
        prompt = f"""Design infrastructure for:
{message}
Include:
- Architecture diagram (text-based)
- Required resources
- Configuration examples
- Security considerations
- Cost estimates (rough)"""
        return call_groq_sync(DAVE_PERSONA, prompt)

    def _general_tech(self, message: str, context: dict) -> str:
        return call_groq_sync(DAVE_PERSONA, message)

    def _extract_code(self, response: str) -> List[str]:
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        return code_blocks
