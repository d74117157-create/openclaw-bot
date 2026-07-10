"""
OpenClaw — worker/agents/coder.py
CODER AGENT: Builds production-grade bots, APIs, scripts, integrations.
"""
import os
from worker.ai_worker import process_task, _chat

SYSTEM = (
    "You are the CODER AGENT of OpenClaw. You write production-grade Python, JavaScript, or bash code. "
    "You build bots, APIs, Discord apps, Slack apps, GitHub Actions, Railway services, Docker configs. "
    "Rules: clean architecture, modularity, full error handling, logging on every critical path. "
    "Always output complete, runnable code — never stubs or pseudocode. "
    "Add docstrings to every class and function. "
    "Never hardcode secrets — always use environment variables."
)


def build_discord_bot(spec: str) -> str:
    return _chat(SYSTEM, f"Build a complete Discord bot (discord.py 2.x) for: {spec}")


def build_slack_app(spec: str) -> str:
    return _chat(SYSTEM, f"Build a complete Slack app (slack-bolt) for: {spec}")


def build_api(spec: str) -> str:
    return _chat(SYSTEM, f"Build a complete FastAPI REST API for: {spec}")


def build_github_action(spec: str) -> str:
    return _chat(SYSTEM, f"Build a complete GitHub Actions workflow YAML for: {spec}")


def build_dockerfile(spec: str) -> str:
    return _chat(SYSTEM, f"Build a production Dockerfile for: {spec}")


def fix_code(broken_code: str, error: str) -> str:
    return _chat(
        SYSTEM,
        f"Fix this code error:\nERROR: {error}\n\nCODE:\n{broken_code}"
    )


def refactor_code(code: str, goal: str) -> str:
    return _chat(SYSTEM, f"Refactor this code for {goal}:\n{code}")


def run(task: str) -> str:
    return process_task(task, "coder")
