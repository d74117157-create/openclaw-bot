"""
OpenClaw Elite — Monitoring System
Background agents for deployment, uptime, error, and repository monitoring.
"""
import os
import json
import time
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from memory.elite_memory import get_memory
try:
    from worker.slack_reporter import SlackReporter
except ImportError:
    class SlackReporter:
        def send_alert(self, level, message, details=None):
            logging.getLogger("monitoring").info(f"[{level}] {message}")

logger = logging.getLogger("monitoring")

# Alert thresholds
ALERT_CONFIG = {
    "deployment_failure_threshold": 1,
    "uptime_check_interval": 300,  # 5 minutes
    "error_rate_threshold": 5,  # errors per hour
    "repo_staleness_threshold": 86400,  # 24 hours
}


class MonitoringAgent:
    """Base class for background monitoring agents."""

    def __init__(self, name: str, check_interval: int = 60):
        self.name = name
        self.check_interval = check_interval
        self.running = False
        self.alert_history = []
        self._thread = None

    def start(self):
        """Start monitoring in background thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"[{self.name}] Monitoring started")

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f"[{self.name}] Monitoring stopped")

    def _run_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self.check()
            except Exception as e:
                logger.error(f"[{self.name}] Check error: {e}")
            time.sleep(self.check_interval)

    def check(self):
        """Override in subclasses."""
        pass

    def alert(self, level: str, message: str, details: dict = None):
        """Send alert through all configured channels."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name,
            "level": level,
            "message": message,
            "details": details or {}
        }
        self.alert_history.append(alert)

        # Log alert
        log_func = logger.warning if level == "warning" else logger.error
        log_func(f"[{self.name}] ALERT ({level}): {message}")

        # Send to Slack if configured
        try:
            reporter = SlackReporter()
            reporter.send_alert(level, message, details)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

        # Store in memory
        try:
            memory = get_memory()
            memory.store_conversation(
                thread_id="monitoring_alerts",
                user_id="system",
                platform="internal",
                message=f"{self.name} alert",
                response=message,
                intent="monitoring_alert",
                agent=self.name,
                confidence=1.0
            )
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")


class DeploymentMonitor(MonitoringAgent):
    """Monitor deployment status and health."""

    def __init__(self):
        super().__init__("DeploymentMonitor", check_interval=300)
        self.memory = get_memory()

    def check(self):
        """Check recent deployments for failures."""
        recent = self.memory.get_deployments(limit=10)
        failures = [d for d in recent if d["status"] in ["failed", "error", "rollback"]]

        if len(failures) >= ALERT_CONFIG["deployment_failure_threshold"]:
            self.alert(
                "critical",
                f"Deployment failures detected: {len(failures)} recent failures",
                {"failures": failures[:3], "total_checked": len(recent)}
            )

        # Check for deployments stuck in "in_progress" for too long
        stuck = [d for d in recent if d["status"] == "in_progress"]
        for dep in stuck:
            created = datetime.fromisoformat(dep["created"].replace("Z", "+00:00"))
            if datetime.utcnow() - created > timedelta(hours=1):
                self.alert(
                    "warning",
                    f"Deployment stuck in progress: {dep['project']} on {dep['platform']}",
                    {"deployment": dep}
                )


class UptimeMonitor(MonitoringAgent):
    """Monitor system uptime and health."""

    def __init__(self):
        super().__init__("UptimeMonitor", check_interval=ALERT_CONFIG["uptime_check_interval"])
        self.check_urls = []
        self._load_urls()

    def _load_urls(self):
        """Load URLs to monitor from environment."""
        urls_env = os.environ.get("MONITOR_URLS", "")
        if urls_env:
            self.check_urls = [u.strip() for u in urls_env.split(",") if u.strip()]

    def check(self):
        """Check uptime of configured endpoints."""
        import urllib.request

        for url in self.check_urls:
            try:
                req = urllib.request.Request(url, method="HEAD")
                req.add_header("User-Agent", "OpenClaw-Monitor/1.0")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        self.alert(
                            "warning",
                            f"Endpoint returning error: {url} (status {resp.status})",
                            {"url": url, "status": resp.status}
                        )
            except Exception as e:
                self.alert(
                    "critical",
                    f"Endpoint unreachable: {url}",
                    {"url": url, "error": str(e)}
                )


class ErrorMonitor(MonitoringAgent):
    """Monitor error rates and patterns."""

    def __init__(self):
        super().__init__("ErrorMonitor", check_interval=3600)
        self.error_counts = {}
        self.memory = get_memory()

    def check(self):
        """Analyze error patterns from conversation history."""
        # Check recent failed tasks
        recent = self.memory.get_open_tasks()
        failed = [t for t in recent if t["status"] == "failed"]

        if len(failed) >= ALERT_CONFIG["error_rate_threshold"]:
            self.alert(
                "warning",
                f"High error rate: {len(failed)} failed tasks in recent period",
                {"failed_tasks": len(failed), "threshold": ALERT_CONFIG["error_rate_threshold"]}
            )

        # Check for repeated errors from same agent
        agent_errors = {}
        for task in failed:
            agent = task.get("agent", "unknown")
            agent_errors[agent] = agent_errors.get(agent, 0) + 1

        for agent, count in agent_errors.items():
            if count >= 3:
                self.alert(
                    "warning",
                    f"Agent {agent} has {count} consecutive failures",
                    {"agent": agent, "failure_count": count}
                )


class RepositoryMonitor(MonitoringAgent):
    """Monitor repository health and activity."""

    def __init__(self):
        super().__init__("RepositoryMonitor", check_interval=3600)
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.repo = os.environ.get("GITHUB_REPO", "")

    def check(self):
        """Check repository for issues."""
        if not self.github_token or not self.repo:
            return

        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json"
            }

            # Check open issues
            resp = requests.get(
                f"https://api.github.com/repos/{self.repo}/issues?state=open",
                headers=headers, timeout=15
            )
            if resp.status_code == 200:
                issues = resp.json()
                stale_issues = []
                for issue in issues:
                    created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                    if datetime.utcnow() - created > timedelta(days=7):
                        stale_issues.append(issue)

                if len(stale_issues) > 5:
                    self.alert(
                        "warning",
                        f"Repository has {len(stale_issues)} stale open issues",
                        {"stale_count": len(stale_issues), "total_open": len(issues)}
                    )

            # Check PRs
            resp = requests.get(
                f"https://api.github.com/repos/{self.repo}/pulls?state=open",
                headers=headers, timeout=15
            )
            if resp.status_code == 200:
                prs = resp.json()
                stale_prs = [p for p in prs if 
                    datetime.utcnow() - datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) > timedelta(days=3)]
                if len(stale_prs) > 3:
                    self.alert(
                        "warning",
                        f"Repository has {len(stale_prs)} stale open PRs",
                        {"stale_count": len(stale_prs), "total_open": len(prs)}
                    )

        except Exception as e:
            logger.error(f"Repository check failed: {e}")


class MonitoringSystem:
    """Orchestrates all background monitoring agents."""

    def __init__(self):
        self.agents = {
            "deployment": DeploymentMonitor(),
            "uptime": UptimeMonitor(),
            "error": ErrorMonitor(),
            "repository": RepositoryMonitor(),
        }
        self.running = False

    def start_all(self):
        """Start all monitoring agents."""
        if self.running:
            return
        self.running = True
        for agent in self.agents.values():
            agent.start()
        logger.info("All monitoring agents started")

    def stop_all(self):
        """Stop all monitoring agents."""
        self.running = False
        for agent in self.agents.values():
            agent.stop()
        logger.info("All monitoring agents stopped")

    def get_status(self) -> dict:
        """Get status of all monitoring agents."""
        return {
            "running": self.running,
            "agents": {
                name: {
                    "running": agent.running,
                    "alert_count": len(agent.alert_history),
                    "last_alert": agent.alert_history[-1] if agent.alert_history else None
                }
                for name, agent in self.agents.items()
            }
        }

    def get_alerts(self, level: str = None, limit: int = 50) -> List[dict]:
        """Get all alerts across all agents."""
        all_alerts = []
        for agent in self.agents.values():
            all_alerts.extend(agent.alert_history)

        all_alerts.sort(key=lambda x: x["timestamp"], reverse=True)

        if level:
            all_alerts = [a for a in all_alerts if a["level"] == level]

        return all_alerts[:limit]


# Singleton
_monitoring_system = None

def get_monitoring() -> MonitoringSystem:
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system
