"""
Alert Manager — Multi-platform alert distribution.
Sends security findings to Slack, Discord, and Telegram.
NEVER stores or logs secrets.
"""
import json
import logging
from typing import List, Optional
from dataclasses import asdict

import aiohttp

logger = logging.getLogger("guardian.alerts")


class AlertManager:
    """Distributes security alerts across configured channels."""

    def __init__(self, config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_alert(self, finding) -> dict:
        """Send a single finding to all configured channels."""
        results = {"slack": False, "discord": False, "telegram": False, "logged": False}
        self._log_locally(finding)
        results["logged"] = True

        if self.config.slack_webhook_url:
            try:
                await self._send_slack(finding)
                results["slack"] = True
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

        if self.config.discord_webhook_url:
            try:
                await self._send_discord(finding)
                results["discord"] = True
            except Exception as e:
                logger.error(f"Failed to send Discord alert: {e}")

        if self.config.telegram_bot_token and self.config.telegram_chat_id:
            try:
                await self._send_telegram(finding)
                results["telegram"] = True
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")

        return results

    async def send_digest(self, findings: List) -> dict:
        """Send a digest of multiple findings."""
        if not findings:
            return {}
        results = {}
        if self.config.slack_webhook_url:
            try:
                await self._send_slack_digest(findings)
                results["slack"] = True
            except Exception as e:
                logger.error(f"Failed to send Slack digest: {e}")
        if self.config.discord_webhook_url:
            try:
                await self._send_discord_digest(findings)
                results["discord"] = True
            except Exception as e:
                logger.error(f"Failed to send Discord digest: {e}")
        if self.config.telegram_bot_token and self.config.telegram_chat_id:
            try:
                await self._send_telegram_digest(findings)
                results["telegram"] = True
            except Exception as e:
                logger.error(f"Failed to send Telegram digest: {e}")
        return results

    def _log_locally(self, finding):
        severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "🔵"}
        emoji = severity_emoji.get(finding.severity, "⚪")
        logger.warning(
            f"{emoji} SECURITY ALERT [{finding.severity}] {finding.category}: {finding.title} | "
            f"Resource: {finding.resource} | Status: {finding.remediation_status}"
        )

    async def _send_slack(self, finding):
        color_map = {"CRITICAL": "#FF0000", "HIGH": "#FF8C00", "MEDIUM": "#FFD700", "LOW": "#00FF00", "INFO": "#0000FF"}
        payload = {
            "attachments": [{
                "color": color_map.get(finding.severity, "#808080"),
                "title": f"{finding.severity} — {finding.title}",
                "fields": [
                    {"title": "Category", "value": finding.category, "short": True},
                    {"title": "Resource", "value": f"`{finding.resource}`", "short": True},
                    {"title": "Description", "value": finding.description, "short": False},
                    {"title": "Recommendation", "value": finding.recommendation, "short": False},
                    {"title": "Status", "value": finding.remediation_status, "short": True},
                    {"title": "Time", "value": finding.timestamp, "short": True}
                ],
                "footer": "OpenClaw Security Guardian",
                "ts": finding.timestamp
            }]
        }
        async with self.session.post(self.config.slack_webhook_url, json=payload) as resp:
            resp.raise_for_status()

    async def _send_slack_digest(self, findings):
        critical = sum(1 for f in findings if f.severity == "CRITICAL")
        high = sum(1 for f in findings if f.severity == "HIGH")
        medium = sum(1 for f in findings if f.severity == "MEDIUM")
        low = sum(1 for f in findings if f.severity == "LOW")
        payload = {
            "text": f"🛡️ *Security Guardian Digest*\n"
                    f"Total findings: {len(findings)}\n"
                    f"🔴 Critical: {critical} | 🟠 High: {high} | 🟡 Medium: {medium} | 🟢 Low: {low}"
        }
        async with self.session.post(self.config.slack_webhook_url, json=payload) as resp:
            resp.raise_for_status()

    async def _send_discord(self, finding):
        color_map = {"CRITICAL": 0xFF0000, "HIGH": 0xFF8C00, "MEDIUM": 0xFFD700, "LOW": 0x00FF00, "INFO": 0x0000FF}
        embed = {
            "title": f"🛡️ {finding.severity} — {finding.title}",
            "color": color_map.get(finding.severity, 0x808080),
            "fields": [
                {"name": "Category", "value": finding.category, "inline": True},
                {"name": "Resource", "value": f"`{finding.resource}`", "inline": True},
                {"name": "Description", "value": finding.description, "inline": False},
                {"name": "Recommendation", "value": finding.recommendation, "inline": False},
                {"name": "Status", "value": finding.remediation_status, "inline": True},
                {"name": "Time", "value": finding.timestamp, "inline": True}
            ],
            "footer": {"text": "OpenClaw Security Guardian"},
            "timestamp": finding.timestamp
        }
        payload = {"embeds": [embed]}
        async with self.session.post(self.config.discord_webhook_url, json=payload) as resp:
            resp.raise_for_status()

    async def _send_discord_digest(self, findings):
        critical = sum(1 for f in findings if f.severity == "CRITICAL")
        high = sum(1 for f in findings if f.severity == "HIGH")
        medium = sum(1 for f in findings if f.severity == "MEDIUM")
        low = sum(1 for f in findings if f.severity == "LOW")
        embed = {
            "title": "🛡️ Security Guardian Digest",
            "color": 0x3498db,
            "description": f"**Total findings:** {len(findings)}\n"
                          f"🔴 Critical: {critical}\n"
                          f"🟠 High: {high}\n"
                          f"🟡 Medium: {medium}\n"
                          f"🟢 Low: {low}",
            "footer": {"text": "OpenClaw Security Guardian"}
        }
        payload = {"embeds": [embed]}
        async with self.session.post(self.config.discord_webhook_url, json=payload) as resp:
            resp.raise_for_status()

    async def _send_telegram(self, finding):
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "🔵"}
        message = (
            f"{emoji.get(finding.severity, '⚪')} *{finding.severity}* — {finding.title}\n"
            f"\n📂 *Category:* `{finding.category}`\n"
            f"📍 *Resource:* `{finding.resource}`\n"
            f"\n📝 *Description:*\n{finding.description}\n"
            f"\n💡 *Recommendation:*\n{finding.recommendation}\n"
            f"\n📊 *Status:* {finding.remediation_status}\n"
            f"🕐 *Time:* {finding.timestamp}"
        )
        url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        payload = {"chat_id": self.config.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()

    async def _send_telegram_digest(self, findings):
        critical = sum(1 for f in findings if f.severity == "CRITICAL")
        high = sum(1 for f in findings if f.severity == "HIGH")
        medium = sum(1 for f in findings if f.severity == "MEDIUM")
        low = sum(1 for f in findings if f.severity == "LOW")
        message = (
            f"🛡️ *Security Guardian Digest*\n"
            f"\n📊 *Total Findings:* {len(findings)}\n"
            f"🔴 Critical: {critical}\n"
            f"🟠 High: {high}\n"
            f"🟡 Medium: {medium}\n"
            f"🟢 Low: {low}"
        )
        url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        payload = {"chat_id": self.config.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()
