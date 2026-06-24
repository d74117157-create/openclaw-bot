"""Memory module — simple in-memory storage for OpenClaw tasks and decisions."""

import json
import os
from datetime import datetime

# In-memory storage (will be lost on restart — use Redis for persistence)
_tasks = {}
_decisions = []
_deployments = []


def init_db():
    """Initialize the database."""
    print("[memory] init_db called")
    _tasks.clear()
    _decisions.clear()
    _deployments.clear()


def save_task(description, agent="unknown"):
    """Save a new task and return its ID."""
    task_id = "task_%d" % len(_tasks)
    _tasks[task_id] = {
        "id": task_id,
        "description": description,
        "agent": agent,
        "status": "pending",
        "result": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    print("[memory] save_task: %s" % task_id)
    return task_id


def update_task(task_id, result, status="done"):
    """Update a task with its result."""
    if task_id in _tasks:
        _tasks[task_id]["result"] = result
        _tasks[task_id]["status"] = status
        _tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
    print("[memory] update_task: %s -> %s" % (task_id, status))


def get_pending_tasks():
    """Get all pending tasks."""
    return [t for t in _tasks.values() if t["status"] == "pending"]


def get_stats():
    """Get system statistics."""
    return {
        "tasks_total": len(_tasks),
        "tasks_done": len([t for t in _tasks.values() if t["status"] == "done"]),
        "tasks_failed": len([t for t in _tasks.values() if t["status"] == "failed"]),
        "tasks_pending": len([t for t in _tasks.values() if t["status"] == "pending"]),
        "decisions": len(_decisions),
        "deployments": len(_deployments),
    }


def save_decision(action, context, outcome="pending"):
    """Save a decision for audit trail."""
    _decisions.append({
        "action": action,
        "context": context,
        "outcome": outcome,
        "timestamp": datetime.utcnow().isoformat(),
    })
    print("[memory] save_decision: %s" % action)


def save_deployment(repo, branch, status="triggered"):
    """Save a deployment record."""
    _deployments.append({
        "repo": repo,
        "branch": branch,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    })
    print("[memory] save_deployment: %s/%s" % (repo, branch))
