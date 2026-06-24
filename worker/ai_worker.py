#!/usr/bin/env python3
"""AI Worker — Processes tasks for the OpenClaw swarm.

Exports:
  - process_task: Main task processing function
  - orchestrate_task: Task orchestration
  - AGENT_PERSONAS: Agent personality definitions
"""

import os
import sys
import asyncio
import json
import logging
import signal
from datetime import datetime

import aiohttp

from memory import save_task, update_task, get_stats, save_decision

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ai_worker")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

AGENT_PERSONAS = {
    "coder": "You are an expert software engineer. Write clean, production-ready code.",
    "researcher": "You are a research analyst. Provide thorough, well-sourced analysis.",
    "ops": "You are a DevOps engineer. Focus on infrastructure, CI/CD, and reliability.",
    "growth": "You are a growth marketer. Focus on user acquisition and retention.",
    "qa": "You are a QA engineer. Find bugs and ensure quality.",
}


async def call_groq(system_prompt: str, user_prompt: str) -> str:
    """Call Groq API."""
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not configured"

    headers = {
        "Authorization": "Bearer %s" % GROQ_API_KEY,
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
        async with session.post(GROQ_API_URL, headers=headers, json=payload, timeout=60) as resp:
            if resp.status != 200:
                text = await resp.text()
                return "API Error %d: %s" % (resp.status, text[:200])
            data = await resp.json()
            return data["choices"][0]["message"]["content"]


def process_task(description: str, agent: str = "researcher") -> str:
    """Process a task synchronously (for simple cases)."""
    # Run async function in sync context
    return asyncio.run(_process_task_async(description, agent))


async def _process_task_async(description: str, agent: str) -> str:
    """Async task processing."""
    persona = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["researcher"])
    return await call_groq(persona, description)


async def orchestrate_task(description: str, channel_id: str = None) -> str:
    """Orchestrate a complex task across multiple agents."""
    # Determine which agent to use based on keywords
    desc_lower = description.lower()

    if any(k in desc_lower for k in ["code", "write", "function", "bug", "fix", "deploy"]):
        agent = "coder"
    elif any(k in desc_lower for k in ["server", "infrastructure", "docker", "ci/cd"]):
        agent = "ops"
    elif any(k in desc_lower for k in ["market", "seo", "social", "growth", "users"]):
        agent = "growth"
    elif any(k in desc_lower for k in ["test", "qa", "quality", "bug"]):
        agent = "qa"
    else:
        agent = "researcher"

    # Save task
    task_id = save_task(description, agent)
    logger.info("Task %s assigned to %s", task_id, agent)

    # Process
    result = await _process_task_async(description, agent)

    # Update task
    update_task(task_id, result, "done")

    return result


# For running as standalone worker
shutdown_event = asyncio.Event()

async def worker_loop():
    """Main worker loop for standalone mode."""
    logger.info("AI Worker starting...")
    while not shutdown_event.is_set():
        await asyncio.sleep(1)

def handle_signal(sig):
    logger.info("Received signal %s, shutting down...", sig)
    shutdown_event.set()

async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))
    await worker_loop()

if __name__ == "__main__":
    asyncio.run(main())


# ── Backward-compat shim: _chat(system, user) → sync wrapper around call_groq ──
def _chat(system_prompt: str, user_prompt: str) -> str:
    """Sync wrapper for call_groq. Used by reviewer, research, memory_agent."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, call_groq(system_prompt, user_prompt))
                return future.result(timeout=60)
        else:
            return loop.run_until_complete(call_groq(system_prompt, user_prompt))
    except Exception as e:
        return f"LLM error: {e}"


def call_groq_sync(system_prompt: str, user_prompt: str) -> str:
    """Synchronous wrapper for Groq API call."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, use a new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, call_groq(system_prompt, user_prompt))
                return future.result()
        return loop.run_until_complete(call_groq(system_prompt, user_prompt))
    except RuntimeError:
        # No event loop running
        return asyncio.run(call_groq(system_prompt, user_prompt))
