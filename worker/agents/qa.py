"""
OpenClaw — worker/agents/qa.py
QA AGENT: Tests workflows, bots, APIs, GitHub Actions, Railway deployments.
"""
from worker.ai_worker import process_task, _chat

SYSTEM = (
    "You are the QA AGENT of OpenClaw. You write comprehensive test plans and validate workflows. "
    "You test Discord bots, Slack apps, GitHub Actions, Railway deployments, and APIs. "
    "Rules: never approve unstable systems. "
    "Always return:\n"
    "TEST SUITE: <numbered test cases>\n"
    "EDGE CASES: <edge case scenarios>\n"
    "PASS CRITERIA: <what must pass for approval>\n"
    "VERDICT: APPROVED / BLOCKED\n"
    "PYTEST CODE: <runnable pytest code if applicable>"
)

def write_test_plan(spec: str) -> str:
    return _chat(SYSTEM, f"Write a full test plan for: {spec}")

def run(task: str) -> str:
    return process_task(task, "qa")
