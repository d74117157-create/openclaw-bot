#!/usr/bin/env python3
"""AI Worker — Background process that consumes tasks from Redis and calls Groq API.

Runs as a separate process/container. Can be scaled horizontally.
"""

import os
import sys
import asyncio
import json
import logging
import signal
from datetime import datetime

import aiohttp

from memory import get_redis, pop_task, complete_task, register_agent, heartbeat_agent
from worker.slack_reporter import SlackReporter

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ai_worker")

# ─── Config ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
AGENT_ID = os.getenv("HOSTNAME", f"worker_{os.getpid()}")

if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not set — AI worker cannot function")
    # Don't exit immediately — let it fail gracefully on task processing

slack = SlackReporter()
shutdown_event = asyncio.Event()


async def call_groq(question: str) -> str:
    """Call Groq API with the question."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are OpenClaw, a helpful AI assistant. Be concise but thorough."},
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GROQ_API_URL, headers=headers, json=payload, timeout=60) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Groq API error {resp.status}: {text[:500]}")

            data = await resp.json()
            return data["choices"][0]["message"]["content"]


async def post_to_discord(channel_id: str, content: str, task_id: str):
    """Post result back to Discord channel via bot (using Redis pub/sub or direct HTTP)."""
    # Store result so the gateway bot can pick it up and post
    # For now, we use a simple Redis-based approach where the bot polls
    r = get_redis()
    r.lpush(f"openclaw:results:{channel_id}", json.dumps({
        "task_id": task_id,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }))
    logger.info(f"Result queued for channel {channel_id}")


async def process_task(task: dict):
    """Process a single task."""
    task_id = task["id"]
    question = task["question"]
    channel_id = task.get("channel_id")
    username = task.get("username", "unknown")

    logger.info(f"Processing task {task_id}: {question[:80]}...")

    try:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not configured")

        answer = await call_groq(question)

        # Store completion
        complete_task(task_id, answer, success=True)

        # Queue for Discord delivery
        if channel_id:
            await post_to_discord(channel_id, answer, task_id)

        # Slack notification (no-op if webhook not set)
        await slack.notify_task_complete(
            task_id=task_id,
            username=username,
            question=question,
            answer=answer[:500],  # Truncate for Slack
        )

        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.exception(f"Task {task_id} failed")
        error_msg = f"❌ Error: {str(e)[:500]}"
        complete_task(task_id, error_msg, success=False)

        if channel_id:
            await post_to_discord(channel_id, error_msg, task_id)

        await slack.notify_task_failed(
            task_id=task_id,
            username=username,
            question=question,
            error=str(e)[:500],
        )


async def heartbeat_loop():
    """Send periodic heartbeats to Redis."""
    while not shutdown_event.is_set():
        try:
            heartbeat_agent(AGENT_ID)
        except Exception:
            logger.warning("Heartbeat failed")
        await asyncio.wait_for(shutdown_event.wait(), timeout=30)


async def worker_loop():
    """Main worker loop — consume tasks from Redis."""
    logger.info(f"AI Worker {AGENT_ID} starting...")
    register_agent(AGENT_ID, {"status": "active", "model": GROQ_MODEL})

    while not shutdown_event.is_set():
        try:
            task = pop_task()
            if task is None:
                await asyncio.sleep(1)
                continue

            await process_task(task)

        except Exception as e:
            logger.exception("Worker loop error")
            await asyncio.sleep(5)


def handle_signal(sig):
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_event.set()


async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    # Run worker and heartbeat concurrently
    await asyncio.gather(
        worker_loop(),
        heartbeat_loop(),
        return_exceptions=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
