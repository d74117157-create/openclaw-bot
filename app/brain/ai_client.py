"""OpenClaw Empire — AI Brain with Cascading Fallback"""
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger


class AIBrain:
    """Unified AI client with provider fallback chain."""

    PROVIDERS = ["groq", "openai", "anthropic", "xai"]

    def __init__(self):
        self.providers = self._check_providers()
        self.primary = self._pick_primary()
        self.total_calls = 0
        self.failed_calls = 0
        logger.info(f"[AI_BRAIN] Providers: {list(self.providers.keys())}")
        logger.info(f"[AI_BRAIN] Primary: {self.primary}")

    def _check_providers(self) -> Dict[str, bool]:
        return {
            "groq": bool(settings.groq_api_key and settings.groq_api_key.startswith("gsk_")),
            "openai": bool(settings.openai_api_key and settings.openai_api_key.startswith("sk-")),
            "anthropic": bool(settings.anthropic_api_key and settings.anthropic_api_key.startswith("sk-ant-")),
            "xai": bool(settings.xai_api_key),
        }

    def _pick_primary(self) -> str:
        for provider in self.PROVIDERS:
            if self.providers.get(provider):
                return provider
        return "none"

    def is_configured(self) -> bool:
        return self.primary != "none"

    def chat(self, prompt: str, system: str = None, agent_type: str = "orchestrator", 
             max_tokens: int = 2000) -> str:
        """Send prompt to AI with fallback."""
        self.total_calls += 1

        system_prompt = system or self._get_system_prompt(agent_type)

        for provider in self.PROVIDERS:
            if not self.providers.get(provider):
                continue
            try:
                result = self._call_provider(provider, system_prompt, prompt, max_tokens)
                logger.info(f"[AI_BRAIN] {provider} responded ({len(result)} chars)")
                return result
            except Exception as e:
                logger.warning(f"[AI_BRAIN] {provider} failed: {e}")
                self.failed_calls += 1
                continue

        return "Error: No AI provider available. Check API keys."

    def _call_provider(self, provider: str, system: str, prompt: str, max_tokens: int) -> str:
        if provider == "groq":
            return self._call_groq(system, prompt, max_tokens)
        elif provider == "openai":
            return self._call_openai(system, prompt, max_tokens)
        elif provider == "anthropic":
            return self._call_anthropic(system, prompt, max_tokens)
        elif provider == "xai":
            return self._call_xai(system, prompt, max_tokens)
        raise ValueError(f"Unknown provider: {provider}")

    def _call_groq(self, system: str, prompt: str, max_tokens: int) -> str:
        import httpx
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens
            },
            timeout=60.0
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _call_openai(self, system: str, prompt: str, max_tokens: int) -> str:
        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content

    def _call_anthropic(self, system: str, prompt: str, max_tokens: int) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text

    def _call_xai(self, system: str, prompt: str, max_tokens: int) -> str:
        import httpx
        resp = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.xai_api_key}", "Content-Type": "application/json"},
            json={
                "model": "grok-2-latest",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens
            },
            timeout=60.0
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _get_system_prompt(self, agent_type: str) -> str:
        prompts = {
            "orchestrator": "You are the Orchestrator. Coordinate all agents. Give high-level strategy.",
            "coder": "You are the Coder Agent. Write clean, production-ready Python. No explanations, just working code.",
            "researcher": "You are the Researcher Agent. Find market trends, competitor analysis, and data.",
            "ops": "You are the Ops Agent. Monitor systems, handle deployments, manage infrastructure.",
            "growth": "You are the Growth Agent. Optimize marketing, SEO, social media, and conversion funnels.",
            "qa": "You are the QA Agent. Test code, verify deployments, catch bugs. Be ruthless.",
            "business": "You are the Business Agent. Identify products, revenue opportunities, and market gaps.",
            "content": "You are the Content Agent. Create engaging YouTube scripts, blog posts, and social content.",
            "security": "You are the Security Agent. Audit code, scan for vulnerabilities, enforce permissions.",
        }
        return prompts.get(agent_type, prompts["orchestrator"])

    def get_stats(self) -> Dict:
        return {
            "primary": self.primary,
            "providers": self.providers,
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round((self.total_calls - self.failed_calls) / max(self.total_calls, 1) * 100, 1)
        }
