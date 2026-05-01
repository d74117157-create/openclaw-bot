"""Kernel — central task handler and autopilot loop."""

import asyncio
import logging
from typing import Optional

from memory.db import init_db, save_task, update_task, get_pending_tasks, get_stats
from worker.ai_worker import process_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

_autopilot_enabled: bool = False
_autopilot_task: Optional[asyncio.Task] = None
AUTOPILOT_INTERVAL = 10  # seconds between sweeps


# -- Public API --

def init_kernel() -> None:
    """Initialise the database (called once on bot start)."""
    init_db()
    logger.info("Kernel ready.")


def handle_task(task: str) -> str:
    """Save a task, process it through the AI worker, and return the result."""
    task_id = save_task(task)
    logger.info("Processing task #%d: %s", task_id, task[:80])
    try:
        result = process_task(task)
        update_task(task_id, result, status="done")
        logger.info("Task #%d completed.", task_id)
    except Exception as exc:
        error_msg = f"Error: {exc}"
        update_task(task_id, error_msg, status="failed")
        logger.error("Task #%d failed: %s", task_id, exc)
        return error_msg
    return result


def get_status() -> dict:
    """Return task statistics for the !status command."""
    return get_stats()


# -- Autopilot --

def is_autopilot_on() -> bool:
    return _autopilot_enabled


def enable_autopilot(loop: asyncio.AbstractEventLoop) -> None:
    global _autopilot_enabled, _autopilot_task
    if _autopilot_enabled:
        return
    _autopilot_enabled = True
    _autopilot_task = loop.create_task(_autopilot_loop())
    logger.info("Autopilot ENABLED.")


def disable_autopilot() -> None:
    global _autopilot_enabled, _autopilot_task
    _autopilot_enabled = False
    if _autopilot_task and not _autopilot_task.done():
        _autopilot_task.cancel()
    _autopilot_task = None
    logger.info("Autopilot DISABLED.")


async def _autopilot_loop() -> None:
    """Background loop that drains the pending-task queue."""
    logger.info("Autopilot loop started (interval=%ds).", AUTOPILOT_INTERVAL)
    try:
        while _autopilot_enabled:
            pending = get_pending_tasks(limit=5)
            if pending:
                logger.info("Autopilot picked up %d pending task(s).", len(pending))
            for row in pending:
                task_id = row["id"]
                task_text = row["task"]
                try:
                    result = process_task(task_text)
                    update_task(task_id, result, status="done")
                    logger.info("Autopilot completed task #%d.", task_id)
                except Exception as exc:
                    update_task(task_id, str(exc), status="failed")
                    logger.error("Autopilot failed task #%d: %s", task_id, exc)
            await asyncio.sleep(AUTOPILOT_INTERVAL)
    except asyncio.CancelledError:
        logger.info("Autopilot loop cancelled.")
    except Exception as exc:
        logger.error("Autopilot loop crashed: %s", exc)
        global _autopilot_enabled
        _autopilot_enabled = False
