"""
Alice — Planning & Project Management Agent
Breaks down tasks, creates schedules, manages projects.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from worker.ai_worker import call_groq_sync
from memory.elite_memory import get_memory

logger = logging.getLogger("agent.alice")

ALICE_PERSONA = """You are Alice, the Planning and Project Management Agent for OpenClaw Elite.
Your responsibilities:
- Break down complex tasks into actionable steps
- Create project timelines and schedules
- Manage priorities and dependencies
- Coordinate multi-agent workflows
- Track progress against milestones
- Identify blockers and risks

Planning methodology:
1. Understand the goal clearly
2. Identify all required steps
3. Determine dependencies between steps
4. Estimate effort for each step
5. Assign steps to appropriate agents
6. Build a timeline with milestones
7. Identify risks and mitigation strategies

Output format:
- Goal statement
- Phase breakdown
- Step-by-step plan (with owners)
- Timeline estimates
- Dependency map
- Risk assessment
- Success criteria
"""


class AliceAgent:
    """Alice — The strategic planner of OpenClaw Elite."""

    def __init__(self):
        self.memory = get_memory()
        self.name = "Alice"
        self.role = "planning"

    async def handle(self, message: str, context: dict = None) -> dict:
        context = context or {}
        plan_type = self._classify_planning(message)

        if plan_type == "task_breakdown":
            result = self._break_down_task(message, context)
        elif plan_type == "project_plan":
            result = self._create_project_plan(message, context)
        elif plan_type == "schedule":
            result = self._create_schedule(message, context)
        elif plan_type == "workflow":
            result = self._design_workflow(message, context)
        else:
            result = self._general_planning(message, context)

        self.memory.store_conversation(
            thread_id=context.get("thread_id", "default"),
            user_id=context.get("user_id", "unknown"),
            platform=context.get("platform", "unknown"),
            message=message,
            response=result[:1000],
            intent=f"plan_{plan_type}",
            agent="alice",
            confidence=0.92
        )

        if plan_type in ["task_breakdown", "project_plan"]:
            self._store_plan_tasks(result, context)

        return {
            "agent": "alice",
            "response": result,
            "type": plan_type,
            "plan_structure": self._extract_plan_structure(result)
        }

    def _classify_planning(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["break down", "steps", "how to", "task", "subtask"]):
            return "task_breakdown"
        if any(w in msg_lower for w in ["project", "roadmap", "milestone", "phase"]):
            return "project_plan"
        if any(w in msg_lower for w in ["schedule", "timeline", "when", "calendar", "deadline"]):
            return "schedule"
        if any(w in msg_lower for w in ["workflow", "process", "automation", "pipeline"]):
            return "workflow"
        return "general_planning"

    def _break_down_task(self, message: str, context: dict) -> str:
        prompt = f"""Break down the following task into actionable steps:
{message}
For each step:
1. Clear description
2. Estimated effort (hours)
3. Required agent (Bob/Carla/Dave/Alice)
4. Dependencies (which steps must complete first)
5. Deliverable/output
Format as a structured plan with phases."""
        return call_groq_sync(ALICE_PERSONA, prompt)

    def _create_project_plan(self, message: str, context: dict) -> str:
        prompt = f"""Create a comprehensive project plan for:
{message}
Include:
## Project Overview
## Goals & Objectives
## Phases & Milestones
## Task Breakdown (with owners and estimates)
## Timeline
## Resource Requirements
## Risk Assessment
## Success Criteria
## Communication Plan"""
        return call_groq_sync(ALICE_PERSONA, prompt)

    def _create_schedule(self, message: str, context: dict) -> str:
        prompt = f"""Create a detailed schedule for:
{message}
Include:
- Start and end dates (relative if specific dates unknown)
- Daily/weekly breakdown
- Buffer time for risks
- Check-in points
- Final delivery date"""
        return call_groq_sync(ALICE_PERSONA, prompt)

    def _design_workflow(self, message: str, context: dict) -> str:
        prompt = f"""Design a workflow for:
{message}
Include:
- Trigger conditions
- Step-by-step flow
- Decision points
- Agent assignments
- Error handling
- Completion criteria"""
        return call_groq_sync(ALICE_PERSONA, prompt)

    def _general_planning(self, message: str, context: dict) -> str:
        return call_groq_sync(ALICE_PERSONA, message)

    def _store_plan_tasks(self, plan_text: str, context: dict):
        lines = plan_text.split("\n")
        current_phase = "General"
        for line in lines:
            if line.strip().startswith("##") or line.strip().startswith("**Phase"):
                current_phase = line.strip().strip("#* ")
            elif line.strip().startswith("-") or line.strip().startswith("1.") or line.strip().startswith("2."):
                if len(line.strip()) > 10:
                    task_id = f"task_{hash(line.strip()) % 100000}"
                    self.memory.store_task(
                        task_id=task_id,
                        description=line.strip(),
                        agent="alice",
                        context={"phase": current_phase, "user_id": context.get("user_id"), "source": "plan"}
                    )

    def _extract_plan_structure(self, plan_text: str) -> dict:
        lines = plan_text.split("\n")
        phases = []
        tasks = []
        for line in lines:
            if "phase" in line.lower() or line.strip().startswith("##"):
                phases.append(line.strip())
            elif line.strip().startswith("-") or any(line.strip().startswith(str(i)) for i in range(10)):
                tasks.append(line.strip())
        return {
            "phases_count": len(phases),
            "tasks_count": len(tasks),
            "phases": phases[:5],
            "has_timeline": "timeline" in plan_text.lower() or "schedule" in plan_text.lower()
        }
