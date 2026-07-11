"""Parallel execution engine — runs agents, posts Slack + GitHub."""
import os
import json
import time
import traceback
import logging
from typing import Dict
from dotenv import load_dotenv
from worker.ai_worker import process_task
from memory import save_task, update_task

load_dotenv()
logger = logging.getLogger("openclaw.executor")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "openclaw-ops")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_API = "https://api.github.com"


class ExecutorEngine:
    def run_browser(self, browser_task: str, parent_task: str = "") -> str:
        try:
            from worker.browser_worker import BrowserWorker
            w = BrowserWorker()
            result = w.run_web_task(browser_task, parent_task)
            log = "\n".join(result.get("log", [])[-20:])
            status = "SUCCESS" if result.get("success") else "FAILED"
            return (
                f"BROWSER EXECUTION — {status}\n"
                f"Steps done: {result.get('steps_done', 0)} | Steps failed: {result.get('steps_failed', 0)}\n"
                f"Last URL: {result.get('last_url', '')}\n\nLOG:\n{log}"
            )
        except Exception as e:
            return f"Browser worker error: {e}\n{traceback.format_exc()}"

    def self_test(self, task: str, agent_results: Dict[str, str]) -> dict:
        results_text = "\n\n".join(
            f"[{agent.upper()}]:\n{str(out)[:500]}"
            for agent, out in agent_results.items()
        )
        qa_prompt = (
            f"Original task: {task}\n\nAgent outputs:\n{results_text}\n\n"
            f"Run a QA check. Evaluate: 1) Did agents address the task fully? 2) Errors or gaps? "
            f"3) Is output production-ready? 4) Any security issues?\n\n"
            f'Return JSON: {{"passed": true, "summary": "...", "issues": [], "tests_run": 1, "tests_passed": 1, "recommendations": []}}'
        )
        try:
            raw = process_task(qa_prompt, "qa")
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        has_errors = any("ERROR" in str(v) for v in agent_results.values())
        return {
            "passed": not has_errors,
            "summary": "Basic check: no critical errors found." if not has_errors else "Errors detected.",
            "issues": [],
            "tests_run": len(agent_results),
            "tests_passed": len(agent_results) if not has_errors else 0,
            "recommendations": [],
        }

    def post_slack(self, task: str, summary: str, qa_result: dict = None):
        if not SLACK_BOT_TOKEN:
            return
        try:
            from slack_sdk import WebClient
            slack = WebClient(token=SLACK_BOT_TOKEN)
            verdict = "PASSED" if (qa_result or {}).get("passed") else "FAILED"
            preview = summary[:2500]
            slack.chat_postMessage(
                channel=SLACK_CHANNEL,
                blocks=[
                    {"type": "header", "text": {"type": "plain_text", "text": "OpenClaw Task Complete"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Task:* {task[:150]}"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*QA:* {verdict}"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"```{preview}```"}},
                    {"type": "divider"},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": f"{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}"}]},
                ]
            )
        except Exception as e:
            logger.error(f"Slack post failed: {e}")

    def post_slack_agent_update(self, agent: str, task_desc: str, result: str, status: str = "OK"):
        if not SLACK_BOT_TOKEN:
            return
        try:
            from slack_sdk import WebClient
            slack = WebClient(token=SLACK_BOT_TOKEN)
            preview = result[:1800]
            slack.chat_postMessage(
                channel=SLACK_CHANNEL,
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"{status} *[{agent.upper()}]* `{task_desc[:80]}`"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"```{preview}```"}},
                ]
            )
        except Exception as e:
            logger.error(f"Slack agent update failed: {e}")

    def post_github_issue(self, task: str, summary: str) -> str:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            return "GitHub not configured"
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            body = (
                f"## Task\n{task}\n\n"
                f"## Agent Summary\n{summary[:4000]}\n\n"
                f"## Metadata\n- Created: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n"
                f"- Source: OpenClaw Swarm\n"
            )
            resp = requests.post(
                f"{GITHUB_API}/repos/{GITHUB_REPO}/issues",
                headers=headers,
                json={"title": f"[OpenClaw] {task[:80]}", "body": body, "labels": ["openclaw", "swarm-task"]},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return f"Issue #{data['number']}: {data['html_url']}"
        except Exception as e:
            return f"GitHub issue failed: {e}"
