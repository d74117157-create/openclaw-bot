#!/usr/bin/env python3
"""Orchestrator Agent — The brain that routes tasks to the right specialist

SUPERIOR TO VIKTOR: Viktor is a single monolithic agent.
OpenClaw has a swarm of specialized agents coordinated by an orchestrator.

Agents:
  - Orchestrator: Classifies intent, routes to specialists
  - Coder: Writes code, reviews PRs, deploys apps
  - Researcher: Searches web, analyzes data, writes reports
  - Ops: Manages infrastructure, CI/CD, monitoring
  - Growth: Marketing, SEO, social media, analytics
  - QA: Tests code, finds bugs, ensures quality
"""

import os
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

import aiohttp

from shared.message_bus import MessageBus

logger = logging.getLogger("agent.orchestrator")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class BaseAgent:
    """Base class for all swarm agents."""

    def __init__(self, bus: MessageBus, name: str, agent_type: str):
        self.bus = bus
        self.name = name
        self.agent_type = agent_type
        self.capabilities: List[str] = []
        self._ready = True

    def is_ready(self) -> bool:
        return self._ready

    async def process(self, context: dict) -> str:
        """Process a task. Override in subclasses."""
        raise NotImplementedError

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call Groq LLM."""
        if not GROQ_API_KEY:
            return "Error: GROQ_API_KEY not configured"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_URL, headers=headers, json=payload, timeout=60) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return "API Error %d: %s" % (resp.status, text[:200])

                data = await resp.json()
                return data["choices"][0]["message"]["content"]


class OrchestratorAgent(BaseAgent):
    """Routes tasks to the appropriate specialist agent."""

    def __init__(self, bus: MessageBus):
        super().__init__(bus, "orchestrator", "router")
        self.capabilities = ["intent_classification", "task_routing", "context_management"]

    async def classify_intent(self, message: str) -> str:
        """Classify user intent and return agent name."""

        # Quick keyword matching for speed
        msg_lower = message.lower()

        if any(k in msg_lower for k in ["deploy", "server", "infrastructure", "docker", "ci/cd", "pipeline", "hosting", "render", "railway"]):
            return "ops"

        if any(k in msg_lower for k in ["code", "write", "function", "class", "api", "bug", "fix", "pr", "review", "commit", "github", "merge", "deploy app"]):
            return "coder"

        if any(k in msg_lower for k in ["research", "search", "find", "analyze", "data", "report", "study", "market", "competitor", "trend"]):
            return "researcher"

        if any(k in msg_lower for k in ["marketing", "seo", "social", "twitter", "linkedin", "growth", "users", "traffic", "conversion", "ads"]):
            return "growth"

        if any(k in msg_lower for k in ["test", "qa", "quality", "bug report", "verify", "check", "validate", "assert"]):
            return "qa"

        # Default to researcher for general questions
        return "researcher"

    async def process(self, context: dict) -> str:
        """Orchestrator processes meta-tasks about the swarm itself."""
        return "I am the orchestrator. I route tasks to specialist agents. Use /agents to see the swarm."
