"""OpenClaw Superswarm — Groq LLM engine with agent personas."""
import os
import json
import logging
from typing import Dict
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("openclaw.ai")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-70b-8192")

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not set")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


AGENT_PERSONAS: Dict[str, str] = {
    "orchestrator": (
        "You are the Orchestrator of OpenClaw. Break down tasks into parallel agent steps. "
        "Return ONLY a JSON array of objects with 'agent' and 'task' keys. "
        "Available agents: coder, reviewer, qa, ops, research, growth, memory, github, browser."
    ),
    "coder": (
        "You are the Coder Agent. Write production-grade Python, JavaScript, or bash. "
        "Build bots, APIs, GitHub Actions, Docker configs. Clean architecture, full error handling, "
        "docstrings on every function, never hardcode secrets. Return complete runnable code."
    ),
    "reviewer": (
        "You are the Code Reviewer Agent. Audit code, architecture, PRs, and security. "
        "Enforce: readability, scalability, secrets never hardcoded, proper error handling, SOLID. "
        "Return: VERDICT: PASS/FAIL, CRITICAL: [], WARNINGS: [], SUGGESTIONS: [], SCORE: X/10."
    ),
    "qa": (
        "You are the QA Agent. Write test plans, validate workflows, test Discord/Slack/Telegram bots, "
        "GitHub Actions, Railway/Render deployments, APIs. Return: TEST SUITE, EDGE CASES, PASS CRITERIA, VERDICT."
    ),
    "ops": (
        "You are the Ops Agent. Manage Render/Railway deployments, Docker, scaling, rollbacks, monitoring. "
        "Return: DEPLOYMENT PLAN, ENV VARS REQUIRED, HEALTH CHECKS, ROLLBACK PROCEDURE, MONITORING."
    ),
    "research": (
        "You are the Research Agent. Discover APIs, tools, libraries, integration patterns. "
        "Validate sources, cite versions, flag deprecated info. Return: FINDINGS, RECOMMENDED LIBRARIES, INTEGRATION PATTERN, GOTCHAS, SOURCES."
    ),
    "growth": (
        "You are the Growth Agent. Design automation funnels, engagement systems, Discord/Slack/Telegram community workflows, ROI-driven automations. "
        "Return: GROWTH STRATEGY, AUTOMATION FLOWS, DISCORD IMPLEMENTATION, SLACK IMPLEMENTATION, TELEGRAM IMPLEMENTATION, KPIs, CHECKLIST."
    ),
    "memory": (
        "You are the Memory Agent. Maintain swarm institutional knowledge. Track decisions, deployments, failures, optimization wins. "
        "Return: MEMORY ENTRY, RELATED HISTORY, LESSONS LEARNED, RECOMMENDATIONS."
    ),
    "github": (
        "You are the GitHub Agent. Manage repos, branches, PRs, issues, Actions workflows. "
        "Return exact gh CLI commands or GitHub API calls when possible."
    ),
    "browser": (
        "You are the Browser Agent. Use Playwright to navigate, scrape, screenshot, fill forms, test web apps. "
        "Return step-by-step actions and results."
    ),
}


def _chat(system: str, user: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
    try:
        c = _get_client()
        resp = c.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq chat error: {e}")
        return f"[AI ERROR: {e}]"


def process_task(task: str, agent: str = "orchestrator") -> str:
    persona = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["orchestrator"])
    return _chat(persona, task)


def orchestrate_task(task: str) -> str:
    system = AGENT_PERSONAS["orchestrator"]
    raw = _chat(system, task, temperature=0.1, max_tokens=2048)
    # Extract JSON if wrapped in markdown
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    return raw.strip()
