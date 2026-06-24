#!/usr/bin/env python3
"""Researcher Agent — Searches, analyzes, and reports

SUPERIOR TO VIKTOR: Viktor has limited research depth.
OpenClaw Researcher can search the web, analyze data, and generate reports.

Capabilities:
- Web search and summarization
- Data analysis and visualization
- Market research and competitor analysis
- Academic paper summarization
- Trend identification
"""

import os
import logging
from typing import List, Dict

from worker.agents.orchestrator import BaseAgent
from shared.message_bus import MessageBus

logger = logging.getLogger("agent.researcher")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")


class ResearcherAgent(BaseAgent):
    """Specialist agent for research tasks."""

    def __init__(self, bus: MessageBus):
        super().__init__(bus, "researcher", "research_analyst")
        self.capabilities = [
            "web_search", "data_analysis", "market_research",
            "competitor_analysis", "trend_analysis", "report_writing"
        ]

    async def process(self, context: dict) -> str:
        """Process research tasks."""
        message = context.get("message", "")

        msg_lower = message.lower()

        if "competitor" in msg_lower or "vs" in msg_lower:
            return await self._competitor_analysis(message)
        elif "trend" in msg_lower or "market" in msg_lower:
            return await self._market_research(message)
        elif "data" in msg_lower or "analyze" in msg_lower:
            return await self._data_analysis(message)
        else:
            return await self._web_research(message)

    async def _web_research(self, query: str) -> str:
        """Search web and summarize findings."""
        # If Serper API available, use it; otherwise use LLM knowledge
        if SERPER_API_KEY:
            search_results = await self._search_serper(query)
            context = "Web search results:\n" + search_results
        else:
            context = "Using LLM knowledge base (no search API configured)."

        system = """You are a research analyst. Synthesize information into a clear, actionable report with:
1. Key findings (bullet points)
2. Sources or confidence level
3. Recommendations
4. Follow-up questions"""

        return await self._call_llm(system, "%s\n\nQuery: %s" % (context, query))

    async def _search_serper(self, query: str) -> str:
        """Search using Serper.dev API."""
        import aiohttp

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": 5}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                results = []
                for r in data.get("organic", []):
                    results.append("- %s: %s" % (r.get("title", ""), r.get("link", "")))
                return "\n".join(results)

    async def _competitor_analysis(self, query: str) -> str:
        """Analyze competitors."""
        system = """You are a competitive intelligence analyst. Analyze the competitive landscape:
1. Identify key competitors
2. Compare features/pricing
3. Identify gaps and opportunities
4. Provide strategic recommendations"""
        return await self._call_llm(system, query)

    async def _market_research(self, query: str) -> str:
        """Research market trends."""
        system = """You are a market research analyst. Provide:
1. Market size and growth
2. Key trends
3. Customer segments
4. Opportunities and threats"""
        return await self._call_llm(system, query)

    async def _data_analysis(self, query: str) -> str:
        """Analyze data."""
        system = """You are a data analyst. Analyze the provided data and provide:
1. Summary statistics
2. Key insights
3. Visualizations (describe what charts would show this)
4. Anomalies or outliers"""
        return await self._call_llm(system, query)
