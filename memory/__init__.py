"""Redis-backed memory layer for OpenClaw.

Provides task queue, status tracking, and agent registry.
"""

import os
import json
import uuid
from datetime import datetime
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def get_redis() -> redis.Redis:
    """Get a Redis connection."""
    return redis.from_url(REDIS_URL, decode_responses=True)


def push_task(payload: dict) -> str:
    """Queue a task and return its ID."""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    payload["id"] = task_id
    payload["status"] = "queued"
    payload["created_at"] = datetime.utcnow().isoformat()

    r = get_redis()
    pipe = r.pipeline()
    pipe.hset(f"openclaw:task:{task_id}", mapping={
        "data": json.dumps(payload),
        "status": "queued",
        "created_at": payload["created_at"],
    })
    pipe.lpush("openclaw:queue", task_id)
    pipe.execute()

    return task_id


def pop_task() -> dict | None:
    """Pop a task from the queue (blocking)."""
    r = get_redis()
    result = r.brpop("openclaw:queue", timeout=5)
    if result is None:
        return None

    _, task_id = result
    task_data = r.hget(f"openclaw:task:{task_id}", "data")
    if task_data is None:
        return None

    r.hset(f"openclaw:task:{task_id}", "status", "processing")
    r.lpush("openclaw:processing", task_id)

    return json.loads(task_data)


def complete_task(task_id: str, result: str, success: bool = True):
    """Mark a task as completed/failed."""
    r = get_redis()
    status = "completed" if success else "failed"

    pipe = r.pipeline()
    pipe.hset(f"openclaw:task:{task_id}", mapping={
        "status": status,
        "result": result,
        "completed_at": datetime.utcnow().isoformat(),
    })
    pipe.lrem("openclaw:processing", 0, task_id)
    pipe.incr(f"openclaw:stats:{status}")
    pipe.execute()


def get_task_status(task_id: str) -> dict | None:
    """Get task status and result."""
    r = get_redis()
    data = r.hgetall(f"openclaw:task:{task_id}")
    if not data:
        return None
    return {
        "id": task_id,
        "status": data.get("status", "unknown"),
        "result": data.get("result"),
        "created_at": data.get("created_at"),
        "completed_at": data.get("completed_at"),
    }


def get_recent_tasks(limit: int = 10) -> list:
    """Get recent tasks from queue history."""
    r = get_redis()
    # Get all task keys, sort by creation time
    keys = r.keys("openclaw:task:*")
    tasks = []
    for key in keys[:limit * 2]:  # Over-fetch to account for missing
        data = r.hgetall(key)
        if data and "data" in data:
            try:
                task = json.loads(data["data"])
                task["status"] = data.get("status", "unknown")
                task["result"] = data.get("result")
                tasks.append(task)
            except json.JSONDecodeError:
                continue

    # Sort by created_at descending
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tasks[:limit]


def register_agent(agent_id: str, info: dict):
    """Register an AI worker agent."""
    r = get_redis()
    r.sadd("openclaw:agents", agent_id)
    r.hset(f"openclaw:agent:{agent_id}", mapping={
        "status": info.get("status", "active"),
        "last_seen": datetime.utcnow().isoformat(),
        **{k: str(v) for k, v in info.items() if k not in ("status",)},
    })


def heartbeat_agent(agent_id: str):
    """Update agent heartbeat."""
    r = get_redis()
    r.hset(f"openclaw:agent:{agent_id}", "last_seen", datetime.utcnow().isoformat())
