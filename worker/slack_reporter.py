"""Dedicated Slack reporter for real-time swarm updates."""
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("openclaw.slack_reporter")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "openclaw-ops")

AGENT_EMOJI = {
    "orchestrator": "brain", "coder": "coder", "reviewer": "reviewer",
    "qa": "qa", "ops": "ops", "research": "research",
    "growth": "growth", "memory": "memory", "github": "github", "browser": "browser",
}


def _client():
    if not SLACK_BOT_TOKEN:
        return None
    try:
        from slack_sdk import WebClient
        return WebClient(token=SLACK_BOT_TOKEN)
    except Exception:
        return None


def _ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())


def task_started(task: str, plan: list, needs_browser: bool = False):
    slack = _client()
    if not slack:
        return
    agent_list = " -> ".join(f"`{p.get('agent','')}`" for p in plan)
    try:
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=[
                {"type": "header", "text": {"type": "plain_text", "text": "OpenClaw — New Task Started"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Task:* {task[:200]}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Plan:* {agent_list}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Browser:* {'Yes' if needs_browser else 'No'} | *Agents:* {len(plan)}"}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"{_ts()}"}]},
            ]
        )
    except Exception as e:
        logger.error(f"task_started: {e}")


def agent_complete(agent: str, task_desc: str, result: str, success: bool = True):
    slack = _client()
    if not slack:
        return
    status = "Complete" if success else "Failed"
    preview = result[:1500]
    try:
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": f"[{agent.upper()}] {status} — {task_desc[:100]}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"```{preview}```"}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"{_ts()}"}]},
            ]
        )
    except Exception as e:
        logger.error(f"agent_complete: {e}")


def task_complete(task: str, qa_result: dict, github_url: str = ""):
    slack = _client()
    if not slack:
        return
    verdict = "PASSED" if qa_result.get("passed") else "FAILED"
    score = qa_result.get("score", 0)
    try:
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "OpenClaw — Task Complete"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Task:* {task[:150]}\n*QA:* {verdict} ({score}/100)"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Summary:* {qa_result.get('summary', '')[:200]}"}},
        ]
        if github_url:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*GitHub Issue:* {github_url}"}})
        blocks.append({"type": "divider"})
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"OpenClaw Swarm OS | {_ts()}"}]})
        slack.chat_postMessage(channel=SLACK_CHANNEL, blocks=blocks)
    except Exception as e:
        logger.error(f"task_complete: {e}")


def deployment_alert(service: str, status: str, env: str = "production", url: str = ""):
    slack = _client()
    if not slack:
        return
    icon = "OK" if status.lower() in ("success", "deployed", "live") else "FAIL"
    color = "good" if icon == "OK" else "danger"
    try:
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            attachments=[{
                "color": color,
                "title": f"Deploy: {service}",
                "text": f"Status: {status} | Env: {env}" + (f"\n{url}" if url else ""),
                "footer": "OpenClaw OPS",
                "ts": int(time.time()),
            }]
        )
    except Exception as e:
        logger.error(f"deployment_alert: {e}")


def error_alert(context: str, error: str):
    slack = _client()
    if not slack:
        return
    try:
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            attachments=[{
                "color": "danger",
                "title": "OpenClaw Error",
                "text": f"Context: {context}\nError: {error[:500]}",
                "footer": "OpenClaw",
                "ts": int(time.time()),
            }]
        )
    except Exception as e:
        logger.error(f"error_alert: {e}")


def bot_online(bot_name: str):
    slack = _client()
    if not slack:
        return
    try:
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*{bot_name}* is online and ready."}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"OpenClaw Swarm OS booted | {_ts()}"}]},
            ]
        )
    except Exception as e:
        logger.error(f"bot_online: {e}")
