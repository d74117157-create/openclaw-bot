"""Slack Reporter — Optional webhook notifications for task events.

No-ops gracefully if SLACK_WEBHOHOOK_URL is not set.
Wired into ai_worker.py to post on task completion/failure.
"""

import os
import json
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger("slack_reporter")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


class SlackReporter:
    """Sends Slack notifications via incoming webhook."""

    def __init__(self):
        self.webhook_url = SLACK_WEBHOOK_URL
        self.enabled = bool(self.webhook_url)
        if self.enabled:
            logger.info("Slack reporter enabled")
        else:
            logger.info("Slack reporter disabled (SLACK_WEBHOOK_URL not set)")

    async def _send(self, payload: dict) -> bool:
        """Send payload to Slack webhook."""
        if not self.enabled:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        return True
                    else:
                        text = await resp.text()
                        logger.warning("Slack webhook returned %d: %s", resp.status, text[:200])
                        return False
        except Exception as e:
            logger.warning("Slack notification failed: %s", e)
            return False

    async def notify_task_complete(
        self,
        task_id: str,
        username: str,
        question: str,
        answer: str,
    ) -> bool:
        """Notify Slack that a task completed successfully."""
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        payload = {
            "text": "OpenClaw Task Completed",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "OpenClaw Task Completed",
                        "emoji": True,
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Task ID:*\n`%s`" % task_id},
                        {"type": "mrkdwn", "text": "*User:*\n%s" % username},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Question:*\n>%s" % question[:500],
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Answer:*\n>%s" % answer[:1000],
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": " %s" % ts}
                    ]
                },
            ]
        }
        return await self._send(payload)

    async def notify_task_failed(
        self,
        task_id: str,
        username: str,
        question: str,
        error: str,
    ) -> bool:
        """Notify Slack that a task failed."""
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        payload = {
            "text": "OpenClaw Task Failed",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "OpenClaw Task Failed",
                        "emoji": True,
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Task ID:*\n`%s`" % task_id},
                        {"type": "mrkdwn", "text": "*User:*\n%s" % username},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Question:*\n>%s" % question[:500],
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Error:*\n`%s`" % error[:1000],
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": " %s" % ts}
                    ]
                },
            ]
        }
        return await self._send(payload)

    async def notify_startup(self, agent_id: str) -> bool:
        """Notify Slack that a worker started."""
        payload = {
            "text": "OpenClaw Worker Started: %s" % agent_id,
        }
        return await self._send(payload)

    async def notify_shutdown(self, agent_id: str) -> bool:
        """Notify Slack that a worker shut down."""
        payload = {
            "text": "OpenClaw Worker Shut Down: %s" % agent_id,
        }
        return await self._send(payload)
