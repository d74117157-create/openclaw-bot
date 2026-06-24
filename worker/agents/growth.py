#!/usr/bin/env python3
"""Growth Agent — Marketing, SEO, social media, analytics

SUPERIOR TO VIKTOR: Viktor doesn't do marketing.
OpenClaw Growth handles your entire growth stack.

Capabilities:
- SEO optimization and keyword research
- Social media content generation
- Email marketing campaigns
- Analytics and conversion tracking
- A/B test design
- Competitor marketing analysis
"""

import os
import logging

from worker.agents.orchestrator import BaseAgent
from shared.message_bus import MessageBus

logger = logging.getLogger("agent.growth")


class GrowthAgent(BaseAgent):
    """Specialist agent for growth/marketing tasks."""

    def __init__(self, bus: MessageBus):
        super().__init__(bus, "growth", "growth_marketer")
        self.capabilities = [
            "seo", "content_marketing", "social_media",
            "email_marketing", "analytics", "ab_testing",
            "conversion_optimization", "competitor_analysis"
        ]

    async def process(self, context: dict) -> str:
        """Process growth tasks."""
        message = context.get("message", "")
        msg_lower = message.lower()

        if "seo" in msg_lower or "keyword" in msg_lower:
            return await self._seo_task(message)
        elif "social" in msg_lower or "twitter" in msg_lower or "linkedin" in msg_lower:
            return await self._social_media(message)
        elif "email" in msg_lower or "newsletter" in msg_lower:
            return await self._email_marketing(message)
        elif "content" in msg_lower or "blog" in msg_lower or "article" in msg_lower:
            return await self._content_creation(message)
        else:
            return await self._growth_strategy(message)

    async def _seo_task(self, prompt: str) -> str:
        """SEO optimization."""
        system = """You are an SEO expert. Provide:
1. Keyword research and prioritization
2. On-page optimization recommendations
3. Technical SEO audit items
4. Content gap analysis
5. Backlink strategy"""
        return await self._call_llm(system, prompt)

    async def _social_media(self, prompt: str) -> str:
        """Generate social media content."""
        system = """You are a social media strategist. Generate:
1. Platform-specific posts (Twitter/X, LinkedIn, Instagram)
2. Content calendar suggestions
3. Hashtag research
4. Engagement hooks
5. Call-to-action optimization"""
        return await self._call_llm(system, prompt)

    async def _email_marketing(self, prompt: str) -> str:
        """Email marketing campaigns."""
        system = """You are an email marketing expert. Generate:
1. Subject line variations (A/B test)
2. Email body copy
3. Segmentation strategy
4. Send time optimization
5. Follow-up sequences"""
        return await self._call_llm(system, prompt)

    async def _content_creation(self, prompt: str) -> str:
        """Create marketing content."""
        system = """You are a content strategist. Create:
1. Blog post outlines
2. Article drafts
3. Landing page copy
4. Case study frameworks
5. White paper structures"""
        return await self._call_llm(system, prompt)

    async def _growth_strategy(self, prompt: str) -> str:
        """Overall growth strategy."""
        system = """You are a growth hacker. Design a comprehensive growth strategy:
1. Acquisition channels
2. Activation tactics
3. Retention loops
4. Referral mechanisms
5. Revenue optimization"""
        return await self._call_llm(system, prompt)


# ── Functional shim for backward-compat with agents/__init__.py ──
from shared.message_bus import get_default_bus as _get_bus

def run(task: str) -> str:
    """Sync shim — runs agent via default bus. Used by AGENT_DISPATCH."""
    import asyncio
    agent = GrowthAgent(_get_bus())
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, agent.process({"task": task, "message": task}))
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(agent.process({"task": task, "message": task}))
    except Exception as e:
        return f"Agent error: {e}"
