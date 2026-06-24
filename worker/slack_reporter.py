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


def task_started(task_id: str, description: str):
    """Notify that a task has started."""
    _send("Task %s started: %s" % (task_id, description[:100]))


def agent_complete(agent: str, result: str):
    """Notify that an agent has completed."""
    _send("Agent %s completed: %s" % (agent, result[:200]))


def task_complete(task_id: str, result: str):
    """Notify that a task has completed."""
    _send("Task %s complete: %s" % (task_id, result[:200]))
