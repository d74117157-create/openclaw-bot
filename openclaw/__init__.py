"""OpenClaw Elite - Multi-Agent Bot Swarm Platform.

This package wraps the original OpenClaw codebase with structured
async interfaces, health monitoring, and type safety.
"""

__version__ = "4.0.0"
__author__ = "OpenClaw Team"

# Re-export original modules for backward compatibility
from main import OpenClaw
from kernel import GitHubKernel
from bot_factory import BotFactory
from worker.ai_worker import AIWorker
from worker.task_router import TaskRouter
from worker.executor import ExecutorEngine
from worker.github_agent import GitHubAgent
from worker.slack_reporter import SlackReporter
from worker.self_test import SelfTest
from gateway.bot import OpenClawBot
from gateway.slack_bot import SlackBotGateway
from memory import init_db, save_task, get_tasks, get_stats

__all__ = [
    "OpenClaw", "GitHubKernel", "BotFactory",
    "AIWorker", "TaskRouter", "ExecutorEngine",
    "GitHubAgent", "SlackReporter", "SelfTest",
    "OpenClawBot", "SlackBotGateway",
    "init_db", "save_task", "get_tasks", "get_stats",
]
