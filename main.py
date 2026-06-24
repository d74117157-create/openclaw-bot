#!/usr/bin/env python3
"""
OpenClaw Elite — Autonomous Multi-Agent AI System
AI Workforce, not a chatbot.

Pipeline:
User Message -> Intent Classification -> Confidence Score -> Agent Selection -> 
Execution Plan -> Execution -> Self-Verification -> Response

Specialist Agents:
- Bob: Conversation, Customer Support, User Interaction, Explanations
- Carla: Research, Fact Gathering, Web Intelligence, Competitive Analysis
- Dave: Coding, Debugging, GitHub, Infrastructure, Deployments
- Alice: Planning, Scheduling, Project Management, Task Breakdown
"""
import os
import sys
import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.config import Config
from shared.logging import setup_logging, get_logger
from memory.db import init_db
from memory.elite_memory import get_memory, init_elite_memory
from worker.intent_router import get_router, classify_intent
from worker.verification import get_verifier
from worker.monitoring import get_monitoring
from worker.approval import get_approval_framework
from worker.agents.bob import BobAgent
from worker.agents.carla import CarlaAgent
from worker.agents.dave import DaveAgent
from worker.agents.alice import AliceAgent

# Gateways
from gateway.telegram_bot import TelegramGateway
from gateway.discord_bot import DiscordGateway
from gateway.slack_bot import SlackGateway

setup_logging("openclaw_elite")
logger = get_logger("elite_orchestrator")

AGENT_MAP = {
    "bob": BobAgent,
    "carla": CarlaAgent,
    "dave": DaveAgent,
    "alice": AliceAgent,
}


class OpenClawElite:
    """The autonomous multi-agent AI workforce."""

    def __init__(self):
        self.config = Config()
        self.gateways = {}
        self.agents = {}
        self.memory = get_memory()
        self.router = get_router()
        self.verifier = get_verifier()
        self.monitoring = get_monitoring()
        self.approval = get_approval_framework()
        self.start_time = 0

    async def initialize(self):
        """Initialize all subsystems."""
        logger.info("Initializing OpenClaw Elite...")
        self.start_time = asyncio.get_event_loop().time()

        # Initialize databases
        init_db()
        init_elite_memory()

        # Validate config
        errors = Config.validate()
        if errors:
            logger.error(f"Configuration errors: {errors}")

        # Initialize specialist agents
        for agent_id, agent_class in AGENT_MAP.items():
            try:
                self.agents[agent_id] = agent_class()
                logger.info(f"Agent {agent_id} initialized")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_id}: {e}")

        # Initialize gateways
        await self._init_gateways()

        # Start monitoring
        self.monitoring.start_all()

        # Log startup
        logger.info("OpenClaw Elite initialized successfully")

    async def _init_gateways(self):
        """Initialize all platform gateways."""
        if Config.TELEGRAM_BOT1_TOKEN or Config.TELEGRAM_BOT2_TOKEN:
            try:
                self.gateways["telegram"] = TelegramGateway(self)
                logger.info("Telegram Gateway initialized")
            except Exception as e:
                logger.error(f"Failed to init Telegram: {e}")

        if Config.DISCORD_TOKEN:
            try:
                self.gateways["discord"] = DiscordGateway(self)
                logger.info("Discord Gateway initialized")
            except Exception as e:
                logger.error(f"Failed to init Discord: {e}")

        if Config.SLACK_BOT_TOKEN:
            try:
                self.gateways["slack"] = SlackGateway(self)
                logger.info("Slack Gateway initialized")
            except Exception as e:
                logger.error(f"Failed to init Slack: {e}")

    async def route_message(self, platform: str, user_id: str, username: str, 
                           message: str, channel_id: str) -> str:
        """Route incoming message through the full Elite pipeline."""
        logger.info(f"[{platform}] {username}: {message}")

        thread_id = f"{platform}_{user_id}_{channel_id}"

        # 1. Store user profile if new
        self._ensure_user_profile(user_id, platform, username)

        # 2. Get resume context for returning users
        resume_context = self.memory.get_resume_context(user_id)
        if resume_context["has_previous_session"]:
            logger.info(f"Resuming session for {username}")

        # 3. Intent Classification
        routing = classify_intent(message, user_context={
            "user_id": user_id,
            "platform": platform,
            "username": username,
            "resume_context": resume_context
        })

        logger.info(f"Routing: intent={routing['intent']}, agent={routing['agent']}, "
                   f"confidence={routing['confidence']}, risk={routing['risk_level']}")

        # 4. Check if clarification needed
        if routing["requires_clarification"]:
            clarifying_question = self.router.get_clarifying_question(message, 
                self.router.classify(message, {"user_id": user_id}))
            await self._send_response(platform, channel_id, 
                f"🤔 {clarifying_question}\n\n_Your message was classified with {routing['confidence']:.0%} confidence. I want to make sure I help you correctly._")
            return "clarification_requested"

        # 5. Check approval for risky actions
        if routing["requires_approval"]:
            approval_req = self.approval.request_approval(
                action=routing["intent"],
                details={"message": message, "agent": routing["agent"], "platform": platform},
                requester=f"{username}@{platform}"
            )
            await self._send_response(platform, channel_id,
                f"⚠️ **Approval Required**\n\n"
                f"Action: `{routing['intent']}`\n"
                f"Risk Level: **{routing['risk_level'].upper()}**\n"
                f"Agent: {routing['agent'].upper()}\n\n"
                f"This action requires your explicit approval.\n"
                f"Approval ID: `{approval_req.id}`\n\n"
                f"Reply with `approve {approval_req.id}` to proceed or `deny {approval_req.id}` to cancel.")
            return approval_req.id

        # 6. Execute
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        self.memory.store_task(
            task_id=task_id,
            description=message,
            agent=routing["agent"],
            priority="medium",
            context={"user_id": user_id, "platform": platform, "intent": routing["intent"]}
        )

        # Execute asynchronously
        asyncio.create_task(self._execute_task(
            task_id, message, routing, platform, channel_id, user_id, thread_id
        ))

        return task_id

    async def _execute_task(self, task_id: str, message: str, routing: dict,
                           platform: str, channel_id: str, user_id: str, thread_id: str):
        """Execute the task with the selected agent(s)."""
        execution_log = []
        agent_results = []

        try:
            # Single agent execution
            primary_agent = routing["agent"]

            if primary_agent in self.agents:
                agent = self.agents[primary_agent]
                context = {
                    "user_id": user_id,
                    "platform": platform,
                    "thread_id": thread_id,
                    "task_id": task_id
                }

                logger.info(f"Executing with {primary_agent}")
                execution_log.append({"type": "agent_start", "agent": primary_agent, "task_id": task_id})

                result = await agent.handle(message, context)
                agent_results.append(result)

                execution_log.append({"type": "agent_complete", "agent": primary_agent, "status": "success"})

                # Multi-agent execution plan
                if routing.get("execution_plan") and len(routing["execution_plan"]) > 1:
                    logger.info("Executing multi-agent plan")
                    for step in routing["execution_plan"]:
                        step_agent = step.get("agent")
                        if step_agent != primary_agent and step_agent in self.agents:
                            step_result = await self.agents[step_agent].handle(
                                step.get("description", message), context
                            )
                            agent_results.append(step_result)
                            execution_log.append({"type": "agent_complete", "agent": step_agent, "status": "success"})
            else:
                # Fallback to Bob for unknown agents
                logger.warning(f"Unknown agent {primary_agent}, falling back to Bob")
                result = await self.agents["bob"].handle(message, {
                    "user_id": user_id, "platform": platform, "thread_id": thread_id
                })
                agent_results.append(result)

            # Self-verification
            verification = self.verifier.verify(message, agent_results, execution_log)

            # Update task
            final_response = self._build_final_response(agent_results, verification, routing)
            self.memory.update_task(task_id, status="completed", result=final_response)

            # Store conversation
            self.memory.store_conversation(
                thread_id=thread_id,
                user_id=user_id,
                platform=platform,
                message=message,
                response=final_response,
                intent=routing["intent"],
                agent=primary_agent,
                confidence=routing["confidence"]
            )

            # Send response
            if verification.can_respond:
                await self._send_response(platform, channel_id, final_response, task_id)
            else:
                await self._send_response(platform, channel_id,
                    f"⚠️ I processed your request but need to verify a few things:\n\n"
                    f"{chr(10).join(verification.issues)}\n\n"
                    f"{final_response}", task_id)

            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            self.memory.update_task(task_id, status="failed", result=str(e))
            await self._send_response(platform, channel_id,
                f"❌ I encountered an error while processing your request:\n```\n{str(e)[:500]}\n```\n\n"
                f"Please try again or rephrase your request.", task_id)

    def _build_final_response(self, agent_results: List[dict], verification: Any, routing: dict) -> str:
        """Build the final response from agent results."""
        if len(agent_results) == 1:
            return agent_results[0].get("response", "No response generated")

        # Multi-agent: use Bob to synthesize
        if "bob" in self.agents:
            return self.agents["bob"].summarize_results(agent_results, "")

        # Fallback: concatenate
        parts = []
        for result in agent_results:
            agent_name = result.get("agent", "unknown").upper()
            response = result.get("response", "")
            parts.append(f"**[{agent_name}]**\n{response}")
        return "\n\n".join(parts)

    async def _send_response(self, platform: str, channel_id: str, content: str, task_id: str = None):
        """Send response through appropriate gateway."""
        gateway = self.gateways.get(platform)
        if gateway:
            try:
                await gateway.send_message(channel_id, content, task_id)
            except Exception as e:
                logger.error(f"Failed to send response via {platform}: {e}")

    def _ensure_user_profile(self, user_id: str, platform: str, username: str):
        """Ensure user has a profile in memory."""
        existing = self.memory.get_user_profile(user_id)
        if not existing:
            self.memory.store_user_profile(
                user_id=user_id,
                platform=platform,
                username=username,
                preferences={},
                goals=[],
                context={"first_seen": datetime.utcnow().isoformat()}
            )
            logger.info(f"New user profile created: {username} ({user_id})")

    async def handle_approval(self, approval_id: str, approved: bool, reason: str = None) -> dict:
        """Handle approval/denial of a pending request."""
        if approved:
            result = self.approval.approve(approval_id)
            # Re-execute the approved task
            # (In production, we'd retrieve the original task and re-run)
            return {"status": "approved", "details": result}
        else:
            result = self.approval.deny(approval_id, reason or "User denied")
            return {"status": "denied", "details": result}

    def get_stats(self) -> dict:
        """Get system statistics."""
        uptime = asyncio.get_event_loop().time() - self.start_time if self.start_time else 0
        return {
            "uptime_seconds": int(uptime),
            "gateways": list(self.gateways.keys()),
            "agents": list(self.agents.keys()),
            "tasks_total": len(self.memory.get_open_tasks()),
            "tasks_done": len([t for t in self.memory.get_open_tasks() if t["status"] == "completed"]),
            "tasks_failed": len([t for t in self.memory.get_open_tasks() if t["status"] == "failed"]),
            "pending_approvals": len(self.approval.get_pending()),
            "monitoring_status": self.monitoring.get_status()
        }

    async def start(self):
        """Start the Elite system."""
        await self.initialize()

        # Start all gateways
        tasks = []
        for name, gateway in self.gateways.items():
            tasks.append(asyncio.create_task(gateway.start()))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Keep alive if no gateways
            while True:
                await asyncio.sleep(3600)


async def main():
    """Main entry point."""
    elite = OpenClawElite()
    await elite.start()


if __name__ == "__main__":
    asyncio.run(main())
