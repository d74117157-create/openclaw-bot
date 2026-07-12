"""
AI Brain — Unified LLM client for the Superswarm
Supports: Groq (primary), xAI Grok, OpenAI, Anthropic Claude
Auto-fallback chain for maximum uptime.
"""
import os
import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

# API Keys from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class AIBrain:
    """
    Unified AI brain with cascading fallback:
    1. Groq (fastest, cheapest) → llama-3.3-70b-versatile
    2. xAI Grok → grok-2-latest
    3. OpenAI → gpt-4o-mini
    4. Anthropic Claude → claude-3-haiku
    """

    SYSTEM_PROMPT = """You are Viktor A.I., the intelligence core of the KingLulu Digital Empire.
You operate a multi-agent bot swarm across Discord, Telegram, Slack, and YouTube.
Your purpose: generate revenue, automate content, trade crypto, and grow the empire.
Be concise, tactical, and results-oriented. When asked about code, provide working Python.
When asked about strategy, give actionable steps. When asked about trading, be risk-aware.
Current date: {date}. Empire target: $20,000/month passive income."""

    AGENT_PROMPTS = {
        "orchestrator": "You are the Orchestrator. Coordinate all agents. Give high-level strategy and routing decisions.",
        "coder": "You are the Coder Agent. Write clean, production-ready Python. Fix bugs. Deploy code. No explanations, just working code.",
        "researcher": "You are the Researcher Agent. Find market trends, competitor analysis, and data. Be thorough and cite sources.",
        "ops": "You are the Ops Agent. Monitor systems, handle deployments, manage infrastructure. Alert on issues. Fix problems.",
        "growth": "You are the Growth Agent. Optimize marketing, SEO, social media, and conversion funnels. Track metrics.",
        "qa": "You are the QA Agent. Test code, verify deployments, catch bugs before they hit production. Be ruthless.",
    }

    def __init__(self):
        self.providers = self._check_providers()
        self.primary = self._pick_primary()
        self.total_calls = 0
        self.failed_calls = 0
        print(f"[AI_BRAIN] Providers available: {list(self.providers.keys())}")
        print(f"[AI_BRAIN] Primary: {self.primary}")

    def _check_providers(self) -> Dict[str, bool]:
        return {
            "groq": bool(GROQ_API_KEY),
            "grok": bool(GROK_API_KEY),
            "openai": bool(OPENAI_API_KEY),
            "anthropic": bool(ANTHROPIC_API_KEY),
        }

    def _pick_primary(self) -> str:
        for provider in ["groq", "grok", "openai", "anthropic"]:
            if self.providers.get(provider):
                return provider
        return "none"

    def is_configured(self) -> bool:
        return self.primary != "none"

    def think(self, message: str, agent_type: str = "orchestrator", 
              context: Dict[str, Any] = None, max_tokens: int = 1024) -> str:
        """
        Main entry point. Send message to AI and get response.
        Tries primary provider, falls back through chain.
        """
        self.total_calls += 1
        context = context or {}

        system = self._build_system_prompt(agent_type, context)

        providers_to_try = [p for p in ["groq", "grok", "openai", "anthropic"] 
                           if self.providers.get(p)]

        for provider in providers_to_try:
            try:
                response = self._call_provider(provider, system, message, max_tokens)
                if response:
                    return response
            except Exception as e:
                print(f"[AI_BRAIN] {provider} failed: {e}")
                continue

        self.failed_calls += 1
        return self._fallback_response(message, agent_type, context)

    def _build_system_prompt(self, agent_type: str, context: Dict) -> str:
        base = self.SYSTEM_PROMPT.format(date=datetime.utcnow().strftime("%Y-%m-%d"))
        agent_specific = self.AGENT_PROMPTS.get(agent_type, "")
        platform = context.get("platform", "unknown")
        user = context.get("user", "unknown")
        return f"{base}\n\n{agent_specific}\nPlatform: {platform}\nUser: {user}"

    def _call_provider(self, provider: str, system: str, message: str, max_tokens: int) -> Optional[str]:
        if provider == "groq":
            return self._call_groq(system, message, max_tokens)
        elif provider == "grok":
            return self._call_grok(system, message, max_tokens)
        elif provider == "openai":
            return self._call_openai(system, message, max_tokens)
        elif provider == "anthropic":
            return self._call_anthropic(system, message, max_tokens)
        return None

    def _call_groq(self, system: str, message: str, max_tokens: int) -> Optional[str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        return None

    def _call_grok(self, system: str, message: str, max_tokens: int) -> Optional[str]:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-2-latest",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        return None

    def _call_openai(self, system: str, message: str, max_tokens: int) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        return None

    def _call_anthropic(self, system: str, message: str, max_tokens: int) -> Optional[str]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": message}]
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
        if "content" in data:
            return data["content"][0]["text"]
        return None

    def _fallback_response(self, message: str, agent_type: str, context: Dict) -> str:
        platform = context.get("platform", "unknown")
        return f"🧠 **Viktor A.I** (offline mode)\n\nI received your message on {platform}, but no AI provider is configured.\n\nSet one of these in Render env vars:\n• `GROQ_API_KEY` (recommended)\n• `GROK_API_KEY` (xAI)\n• `OPENAI_API_KEY`\n• `ANTHROPIC_API_KEY`\n\nYour message: *{message[:200]}...*"

    def get_status(self) -> Dict:
        return {
            "primary": self.primary,
            "providers": self.providers,
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "success_rate": f"{((self.total_calls - self.failed_calls) / self.total_calls * 100):.1f}%" if self.total_calls > 0 else "N/A"
        }

# Singleton
_brain_instance = None

def get_brain() -> AIBrain:
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AIBrain()
    return _brain_instance
