"""
Carla — Research & Intelligence Agent
Gathers facts, performs web intelligence, competitive analysis.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from worker.ai_worker import process_task, call_groq_sync
from memory.elite_memory import get_memory

logger = logging.getLogger("agent.carla")

CARLA_PERSONA = """You are Carla, the Research and Intelligence Agent for OpenClaw Elite.
Your responsibilities:
- Conduct thorough research on any topic
- Gather facts from available information
- Perform competitive analysis
- Synthesize intelligence reports
- Identify trends and patterns
- Verify claims and cross-reference sources

Research methodology:
1. Define the research question clearly
2. Identify key information needs
3. Gather data systematically
4. Analyze and synthesize findings
5. Present structured, actionable intelligence
6. Cite sources and confidence levels

Output format:
- Executive Summary (2-3 sentences)
- Key Findings (bullet points)
- Detailed Analysis
- Sources & Confidence
- Recommendations
"""


class CarlaAgent:
    """Carla — The research powerhouse of OpenClaw Elite."""

    def __init__(self):
        self.memory = get_memory()
        self.name = "Carla"
        self.role = "research"
        self.web_search_enabled = bool(os.environ.get("SERPAPI_KEY") or os.environ.get("BRAVE_API_KEY"))

    async def handle(self, message: str, context: dict = None) -> dict:
        context = context or {}
        research_type = self._classify_research(message)
        plan = self._build_research_plan(message, research_type)
        findings = []
        for step in plan:
            finding = self._execute_research_step(step)
            findings.append(finding)
        synthesis = self._synthesize(findings, message)

        self.memory.store_conversation(
            thread_id=context.get("thread_id", "default"),
            user_id=context.get("user_id", "unknown"),
            platform=context.get("platform", "unknown"),
            message=message,
            response=synthesis[:1000],
            intent=f"research_{research_type}",
            agent="carla",
            confidence=0.88
        )

        return {
            "agent": "carla",
            "response": synthesis,
            "type": "research",
            "findings_count": len(findings),
            "research_type": research_type
        }

    def _classify_research(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["competitor", "competition", "vs", "versus", "compare"]):
            return "competitive_analysis"
        if any(w in msg_lower for w in ["market", "industry", "trend", "growth"]):
            return "market_research"
        if any(w in msg_lower for w in ["how to", "tutorial", "guide", "steps"]):
            return "informational"
        if any(w in msg_lower for w in ["data", "statistics", "numbers", "metrics"]):
            return "data_analysis"
        return "general_research"

    def _build_research_plan(self, message: str, research_type: str) -> List[dict]:
        plans = {
            "competitive_analysis": [
                {"step": 1, "action": "identify_competitors", "query": f"Who are the main competitors in: {message}"},
                {"step": 2, "action": "gather_metrics", "query": f"Key metrics and positioning for: {message}"},
                {"step": 3, "action": "analyze_gaps", "query": f"Market gaps and opportunities in: {message}"},
            ],
            "market_research": [
                {"step": 1, "action": "market_size", "query": f"Market size and growth for: {message}"},
                {"step": 2, "action": "trends", "query": f"Current trends in: {message}"},
                {"step": 3, "action": "forecast", "query": f"Future outlook for: {message}"},
            ],
            "informational": [
                {"step": 1, "action": "core_concepts", "query": f"Core concepts of: {message}"},
                {"step": 2, "action": "practical_steps", "query": f"Practical implementation of: {message}"},
            ],
            "data_analysis": [
                {"step": 1, "action": "collect_data", "query": f"Available data on: {message}"},
                {"step": 2, "action": "analyze_patterns", "query": f"Patterns and insights from: {message}"},
            ],
            "general_research": [
                {"step": 1, "action": "broad_search", "query": message},
                {"step": 2, "action": "deep_dive", "query": f"Detailed analysis of: {message}"},
            ]
        }
        return plans.get(research_type, plans["general_research"])

    def _execute_research_step(self, step: dict) -> dict:
        query = step["query"]
        web_results = []
        if self.web_search_enabled:
            web_results = self._web_search(query)
        prompt = f"""Research query: {query}
Web search results: {json.dumps(web_results) if web_results else 'No web search available'}
Provide a comprehensive research finding. Be factual, cite specific details, and indicate confidence level."""
        finding = call_groq_sync(CARLA_PERSONA, prompt)
        return {"step": step["step"], "action": step["action"], "finding": finding, "sources": web_results}

    def _web_search(self, query: str) -> List[dict]:
        return []

    def _synthesize(self, findings: List[dict], original_query: str) -> str:
        findings_text = "\n\n".join([
            f"### Finding {f['step']}: {f['action']}\n{f['finding']}"
            for f in findings
        ])
        prompt = f"""Synthesize the following research findings into a structured intelligence report.
Original query: {original_query}
Findings:
{findings_text}
Format:
## Executive Summary
## Key Findings
## Detailed Analysis
## Confidence Assessment
## Recommendations"""
        return call_groq_sync(CARLA_PERSONA, prompt)

    def quick_fact(self, question: str) -> str:
        prompt = f"Provide a concise, factual answer to: {question}. If uncertain, say so."
        return call_groq_sync(CARLA_PERSONA, prompt)
