"""Memory package for OpenClaw — backward-compatible, defensive."""
import logging
from .db import (
    init_db,
    save_task,
    update_task,
    get_pending_tasks,
    get_stats,
    save_decision,
    save_deployment,
    get_task,
    get_or_create_unified_user,
    search_decisions,
    get_recent_tasks,
    get_failed_tasks,
)

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"pending", "done", "failed", "running", "cancelled"}

def health_check() -> dict:
    """Return {'ok': True} if DB is reachable."""
    try:
        stats = get_stats()
        return {"ok": True, "stats": stats}
    except Exception as exc:
        logger.error("health_check failed: %s", exc)
        return {"ok": False, "error": str(exc)}

__all__ = [
    "init_db", "save_task", "update_task", "get_pending_tasks",
    "get_stats", "save_decision", "save_deployment", "get_task",
    "get_or_create_unified_user", "search_decisions",
    "get_recent_tasks", "get_failed_tasks", "health_check",
]
