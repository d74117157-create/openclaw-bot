import asyncio
import logging
from memory.db import init_db, save_task, update_task, get_pending_tasks, get_stats
from worker.ai_worker import process_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_state = {"autopilot": False, "task": None}
AUTOPILOT_INTERVAL = 10

def init_kernel():
    init_db()
    logger.info("Kernel ready.")

def handle_task(task):
    task_id = save_task(task)
    try:
        result = process_task(task)
        update_task(task_id, result, status="done")
    except Exception as exc:
        result = "Error: " + str(exc)
        update_task(task_id, result, status="failed")
    return result

def get_status():
    return get_stats()

def is_autopilot_on():
    return _state["autopilot"]

def enable_autopilot(loop):
    if _state["autopilot"]:
        return
    _state["autopilot"] = True
    _state["task"] = loop.create_task(_autopilot_loop())
    logger.info("Autopilot ENABLED.")

def disable_autopilot():
    if not _state["autopilot"]:
        return
    _state["autopilot"] = False
    if _state["task"]:
        _state["task"].cancel()
        _state["task"] = None
    logger.info("Autopilot DISABLED.")

async def _autopilot_loop():
    while _state["autopilot"]:
        try:
            pending = get_pending_tasks()
            for t in pending:
                result = process_task(t["task"])
                update_task(t["id"], result, status="done")
        except Exception as exc:
            logger.error("Autopilot error: %s", exc)
        await asyncio.sleep(AUTOPILOT_INTERVAL)
