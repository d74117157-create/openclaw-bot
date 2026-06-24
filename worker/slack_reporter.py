#!/usr/bin/env python3
"""Slack Reporter — Optional webhook notifications.

Exports:
  - task_started: Notify when task starts
  - agent_complete: Notify when agent finishes
  - task_complete: Notify when task completes
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger("slack_reporter")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def _send(message: str):
    """Send message to Slack (placeholder — implement with requests/aiohttp if needed)."""
    if not SLACK_WEBHOOK_URL:
        return
    logger.info("[Slack] %s", message)


def task_started(task_id, description=None, needs_browser=False):
    """Notify that a task has started."""
    if isinstance(task_id, str):
        desc = description if description else task_id
        if isinstance(desc, list):
            desc = str(desc)
        _send("Task started: %s" % desc[:100])
    else:
        _send("Task started: %s" % str(task_id)[:100])


def agent_complete(agent, task_desc=None, result=None, success=True):
    """Notify that an agent has completed."""
    status = "✅" if success else "❌"
    msg = "%s Agent %s completed" % (status, agent)
    if result:
        msg += ": %s" % str(result)[:200]
    _send(msg)


def task_complete(task_id, result=None):
    """Notify that a task has completed."""
    msg = "Task %s complete" % task_id
    if result:
        msg += ": %s" % str(result)[:200]
    _send(msg)
