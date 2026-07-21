"""OpenClaw Empire — Autonomous Task Scheduler

Runs daily and weekly tasks automatically.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("openclaw.scheduler")


@dataclass
class ScheduledTask:
    name: str
    schedule: str  # "daily" or "weekly"
    hour: int
    minute: int
    action: Callable
    enabled: bool = True
    last_run: Optional[datetime] = None


class TaskScheduler:
    """Autonomous empire task scheduler."""

    DAILY_TASKS = [
        ("content_research", 9, 0),
        ("script_generation", 10, 0),
        ("product_ideas", 11, 0),
        ("marketing_analysis", 14, 0),
        ("system_health_report", 18, 0),
    ]

    WEEKLY_TASKS = [
        ("revenue_review", 0, 9, 0),      # Sunday 9:00
        ("optimization_report", 0, 10, 0),  # Sunday 10:00
        ("new_automation_opportunities", 0, 11, 0),
    ]

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.tasks: List[ScheduledTask] = []
        self._running = False
        self._task_handles = []
        self._build_tasks()

    def _build_tasks(self):
        """Build the task list."""
        for name, hour, minute in self.DAILY_TASKS:
            self.tasks.append(ScheduledTask(
                name=name,
                schedule="daily",
                hour=hour,
                minute=minute,
                action=self._get_action(name)
            ))

        for name, weekday, hour, minute in self.WEEKLY_TASKS:
            self.tasks.append(ScheduledTask(
                name=name,
                schedule="weekly",
                hour=hour,
                minute=minute,
                action=self._get_action(name)
            ))

    def _get_action(self, name: str) -> Callable:
        """Get the action for a task name."""
        actions = {
            "content_research": self._content_research,
            "script_generation": self._script_generation,
            "product_ideas": self._product_ideas,
            "marketing_analysis": self._marketing_analysis,
            "system_health_report": self._system_health_report,
            "revenue_review": self._revenue_review,
            "optimization_report": self._optimization_report,
            "new_automation_opportunities": self._new_automation_opportunities,
        }
        return actions.get(name, self._noop)

    async def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("[Scheduler] Already running")
            return

        self._running = True
        logger.info("[Scheduler] Task engine started")
        logger.info(f"[Scheduler] {len(self.tasks)} tasks registered")

        for task in self.tasks:
            if task.enabled:
                handle = asyncio.create_task(self._run_task(task))
                self._task_handles.append(handle)

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        for handle in self._task_handles:
            handle.cancel()
        self._task_handles = []
        logger.info("[Scheduler] Task engine stopped")

    async def _run_task(self, task: ScheduledTask):
        """Run a scheduled task loop."""
        while self._running:
            try:
                now = datetime.utcnow()
                next_run = self._calculate_next_run(task, now)
                wait_seconds = (next_run - now).total_seconds()

                if wait_seconds > 0:
                    logger.debug(f"[Scheduler] {task.name} next run in {wait_seconds:.0f}s")
                    await asyncio.sleep(min(wait_seconds, 3600))  # Max 1 hour sleep
                    continue

                # Time to run
                logger.info(f"[Scheduler] Running {task.name}")
                task.last_run = now

                if self.orchestrator:
                    try:
                        result = await self.orchestrator.execute(
                            self._get_prompt(task.name),
                            context={"source": "scheduler", "task": task.name}
                        )
                        logger.info(f"[Scheduler] {task.name} completed: {result.get('status')}")
                    except Exception as e:
                        logger.error(f"[Scheduler] {task.name} failed: {e}")
                else:
                    # Run action directly
                    await task.action()

                # Sleep until next cycle
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Scheduler] Task loop error: {e}")
                await asyncio.sleep(300)

    def _calculate_next_run(self, task: ScheduledTask, now: datetime) -> datetime:
        """Calculate next run time."""
        if task.schedule == "daily":
            next_run = now.replace(hour=task.hour, minute=task.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        else:
            # Weekly: find next occurrence of weekday
            days_ahead = (0 - now.weekday()) % 7
            next_run = now.replace(hour=task.hour, minute=task.minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
            if next_run <= now:
                next_run += timedelta(days=7)
            return next_run

    def _get_prompt(self, name: str) -> str:
        """Get the prompt for a scheduled task."""
        prompts = {
            "content_research": "Research trending topics for YouTube content this week. Identify 5 high-potential niches.",
            "script_generation": "Generate a YouTube script outline for the top trending topic. Include hook, structure, and CTA.",
            "product_ideas": "Analyze market gaps and suggest 3 new digital products to create. Include pricing and target audience.",
            "marketing_analysis": "Review current marketing channels and suggest optimizations for conversion rate improvement.",
            "system_health_report": "Generate a system health report: check all agents, verify database, summarize recent tasks.",
            "revenue_review": "Review all revenue streams. Calculate totals, identify top performers, suggest improvements.",
            "optimization_report": "Analyze system performance and suggest optimizations for speed, cost, and reliability.",
            "new_automation_opportunities": "Identify new processes that could be automated. Prioritize by impact and effort.",
        }
        return prompts.get(name, f"Execute scheduled task: {name}")

    # Task actions
    async def _content_research(self):
        logger.info("[Scheduler] Content research executed")

    async def _script_generation(self):
        logger.info("[Scheduler] Script generation executed")

    async def _product_ideas(self):
        logger.info("[Scheduler] Product ideas executed")

    async def _marketing_analysis(self):
        logger.info("[Scheduler] Marketing analysis executed")

    async def _system_health_report(self):
        logger.info("[Scheduler] System health report executed")

    async def _revenue_review(self):
        logger.info("[Scheduler] Revenue review executed")

    async def _optimization_report(self):
        logger.info("[Scheduler] Optimization report executed")

    async def _new_automation_opportunities(self):
        logger.info("[Scheduler] New automation opportunities executed")

    async def _noop(self):
        pass
