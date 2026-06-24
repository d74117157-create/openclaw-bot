"""
Bob — Conversation & Customer Support Agent
Handles user interaction, explanations, greetings, and general communication.
"""
import logging
from typing import Dict, Any, Optional

from worker.ai_worker import call_groq_sync
from memory.elite_memory import get_memory

logger = logging.getLogger("agent.bob")

BOB_PERSONA = """You are Bob, the Conversation and Customer Support Agent for OpenClaw Elite.
Your responsibilities:
- Engage in natural, friendly conversation
- Provide clear explanations of complex topics
- Handle customer support inquiries with empathy
- Welcome new users and guide them through onboarding
- Answer FAQs about the OpenClaw system
- Summarize and communicate results from other agents

Personality traits:
- Friendly, patient, and professional
- Uses clear, concise language
- Adapts tone to the user's style
- Proactive in offering help
- Never makes up information

When responding:
1. Be warm and approachable
2. Break down complex answers into digestible parts
3. Use formatting for readability
4. Ask clarifying questions when needed
5. Acknowledge user's context and previous interactions
"""


class BobAgent:
    """Bob — The friendly face of OpenClaw Elite."""

    def __init__(self):
        self.memory = get_memory()
        self.name = "Bob"
        self.role = "conversation"

    async def handle(self, message: str, context: dict = None) -> dict:
        context = context or {}
        user_id = context.get("user_id", "unknown")
        user_profile = self.memory.get_user_profile(user_id)
        enriched_prompt = self._build_prompt(message, user_profile, context)
        response = call_groq_sync(BOB_PERSONA, enriched_prompt)

        self.memory.store_conversation(
            thread_id=context.get("thread_id", "default"),
            user_id=user_id,
            platform=context.get("platform", "unknown"),
            message=message,
            response=response,
            intent="conversation",
            agent="bob",
            confidence=0.95
        )

        return {
            "agent": "bob",
            "response": response,
            "type": "conversation",
            "requires_follow_up": self._needs_follow_up(message, response)
        }

    def _build_prompt(self, message: str, user_profile: dict, context: dict) -> str:
        parts = [f"User message: {message}"]
        if user_profile:
            prefs = user_profile.get("preferences", {})
            if prefs.get("communication_style"):
                parts.append(f"User prefers {prefs['communication_style']} communication.")
            if prefs.get("expertise_level"):
                parts.append(f"User expertise level: {prefs['expertise_level']}.")
        recent = self.memory.get_user_conversations(context.get("user_id"), limit=3)
        if recent:
            parts.append("Recent context:")
            for conv in recent[-2:]:
                parts.append(f"  - User: {conv['message'][:100]}")
        return "\n".join(parts)

    def _needs_follow_up(self, message: str, response: str) -> bool:
        if "?" in message and "?" not in response[-200:]:
            return True
        if any(w in message.lower() for w in ["help", "issue", "problem", "error"]):
            if "resolved" not in response.lower() and "fixed" not in response.lower():
                return True
        return False

    def explain(self, topic: str, detail_level: str = "medium") -> str:
        prompt = f"Explain '{topic}' at {detail_level} detail level. Make it clear and engaging."
        return call_groq_sync(BOB_PERSONA, prompt)

    def summarize_results(self, results: list, task_description: str) -> str:
        summary_prompt = f"""Summarize the following agent results for the user.
Original task: {task_description}

Results:
"""
        for r in results:
            summary_prompt += f"\n[{r.get('agent', 'unknown').upper()}]: {str(r.get('result', ''))[:500]}"
        summary_prompt += "\n\nProvide a clear, user-friendly summary highlighting key outcomes and any action items."
        return call_groq_sync(BOB_PERSONA, summary_prompt)
