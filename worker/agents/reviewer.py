"""
OpenClaw — worker/agents/reviewer.py
REVIEWER AGENT: Audits code, architecture, PRs, security.
"""
from worker.ai_worker import process_task, _chat

SYSTEM = (
    "You are the REVIEWER AGENT of OpenClaw. You audit code, architecture, PRs, and security posture. "
    "You reject fragile systems. You enforce: readability, scalability, secrets never hardcoded, "
    "proper error handling, and SOLID principles. "
    "Always return structured feedback in this format:\n"
    "VERDICT: PASS or FAIL\n"
    "CRITICAL: <list critical issues>\n"
    "WARNINGS: <list warnings>\n"
    "SUGGESTIONS: <list improvements>\n"
    "SCORE: X/10"
)


def review_code(code: str) -> str:
    return _chat(SYSTEM, f"Review this code:\n\n{code}")


def review_architecture(description: str) -> str:
    return _chat(SYSTEM, f"Review this architecture:\n\n{description}")


def review_pr(pr_title: str, pr_body: str, diff: str = "") -> str:
    content = f"PR Title: {pr_title}\nPR Body: {pr_body}"
    if diff:
        content += f"\n\nDiff:\n{diff[:3000]}"
    return _chat(SYSTEM, f"Review this pull request:\n\n{content}")


def security_audit(code: str) -> str:
    return _chat(
        SYSTEM,
        f"Perform a security audit on this code. Check for: hardcoded secrets, SQL injection, "
        f"unsafe evals, missing auth, exposed endpoints, insecure dependencies:\n\n{code}"
    )


def run(task: str) -> str:
    return process_task(task, "reviewer")
