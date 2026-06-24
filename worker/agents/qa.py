#!/usr/bin/env python3
"""QA Agent — Testing, quality assurance, bug hunting

SUPERIOR TO VIKTOR: Viktor doesn't systematically test.
OpenClaw QA ensures everything works before deployment.

Capabilities:
- Unit test generation
- Integration test design
- Bug reproduction and reporting
- Performance testing
- Security testing
- Accessibility auditing
"""

import os
import logging

from worker.agents.orchestrator import BaseAgent
from shared.message_bus import MessageBus

logger = logging.getLogger("agent.qa")


class QAAgent(BaseAgent):
    """Specialist agent for quality assurance."""

    def __init__(self, bus: MessageBus):
        super().__init__(bus, "qa", "quality_engineer")
        self.capabilities = [
            "unit_testing", "integration_testing", "e2e_testing",
            "performance_testing", "security_testing", "accessibility",
            "bug_reporting", "test_automation"
        ]

    async def process(self, context: dict) -> str:
        """Process QA tasks."""
        message = context.get("message", "")
        msg_lower = message.lower()

        if "unit test" in msg_lower or "pytest" in msg_lower or "jest" in msg_lower:
            return await self._generate_tests(message)
        elif "performance" in msg_lower or "load" in msg_lower or "benchmark" in msg_lower:
            return await self._performance_test(message)
        elif "security" in msg_lower or "penetration" in msg_lower or "vulnerability" in msg_lower:
            return await self._security_test(message)
        elif "accessibility" in msg_lower or "a11y" in msg_lower or "wcag" in msg_lower:
            return await self._accessibility_audit(message)
        else:
            return await self._general_qa(message)

    async def _generate_tests(self, prompt: str) -> str:
        """Generate unit tests."""
        system = """You are a test automation engineer. Generate comprehensive tests:
1. Happy path tests
2. Edge cases and boundary conditions
3. Error handling tests
4. Mock/stub setup
5. Parameterized tests for coverage

Use pytest for Python, Jest for JavaScript. Include setup instructions."""
        return await self._call_llm(system, prompt)

    async def _performance_test(self, prompt: str) -> str:
        """Design performance tests."""
        system = """You are a performance engineer. Design load tests:
1. Benchmark scenarios
2. Load patterns (ramp-up, spike, sustained)
3. Key metrics to measure
4. Bottleneck identification
5. Optimization recommendations"""
        return await self._call_llm(system, prompt)

    async def _security_test(self, prompt: str) -> str:
        """Security testing."""
        system = """You are a penetration tester. Design security tests:
1. OWASP Top 10 coverage
2. Input validation tests
3. Authentication/authorization tests
4. Data exposure tests
5. API security tests"""
        return await self._call_llm(system, prompt)

    async def _accessibility_audit(self, prompt: str) -> str:
        """Accessibility testing."""
        system = """You are an accessibility specialist. Audit for:
1. WCAG 2.1 AA compliance
2. Screen reader compatibility
3. Keyboard navigation
4. Color contrast
5. Focus management"""
        return await self._call_llm(system, prompt)

    async def _general_qa(self, prompt: str) -> str:
        """General QA advice."""
        system = "You are a QA lead. Provide expert guidance on testing strategy, tools, and best practices."
        return await self._call_llm(system, prompt)


# ── Functional shim for backward-compat with agents/__init__.py ──
from shared.message_bus import get_default_bus as _get_bus

def run(task: str) -> str:
    """Sync shim — runs agent via default bus. Used by AGENT_DISPATCH."""
    import asyncio
    agent = QAAgent(_get_bus())
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
