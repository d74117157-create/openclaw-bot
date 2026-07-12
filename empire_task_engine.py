"""
Empire Task Engine — Autonomous Task Assignment & Execution
Viktor A.I assigns tasks to agents, tracks progress, escalates blockers.
"""
import os
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ai_brain import get_brain

TASK_DB_PATH = os.getenv("EMPIRE_TASK_DB", "/tmp/empire-tasks.json")

class EmpireTaskEngine:
    """
    The central nervous system of the empire.
    Creates tasks, assigns to agents, tracks completion, escalates failures.
    """

    PRIORITY_LEVELS = {"critical": 1, "high": 2, "medium": 3, "low": 4}

    AGENT_CAPABILITIES = {
        "coder": ["code", "deploy", "fix", "build", "script", "api", "bot"],
        "researcher": ["research", "analyze", "find", "data", "trend", "market"],
        "growth": ["market", "promote", "seo", "social", "content", "advertise", "scale"],
        "ops": ["monitor", "deploy", "fix", "health", "server", "infrastructure"],
        "qa": ["test", "verify", "check", "audit", "review"],
        "orchestrator": ["coordinate", "plan", "strategy", "decide", "route"],
    }

    def __init__(self):
        self.tasks: List[Dict] = []
        self.completed: List[Dict] = []
        self.brain = get_brain()
        self._load()

    def _load(self):
        if os.path.exists(TASK_DB_PATH):
            try:
                with open(TASK_DB_PATH, 'r') as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.completed = data.get("completed", [])
            except:
                pass

    def _save(self):
        with open(TASK_DB_PATH, 'w') as f:
            json.dump({"tasks": self.tasks, "completed": self.completed}, f, indent=2, default=str)

    def create_task(self, title: str, description: str, agent_type: str = "auto",
                   priority: str = "medium", platform: str = "empire",
                   deadline_hours: int = 24, metadata: Dict = None) -> str:
        """Create a new empire task."""
        task_id = f"task_{int(time.time())}_{random.randint(1000,9999)}"

        if agent_type == "auto":
            agent_type = self._pick_agent_for_task(title + " " + description)

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "agent_type": agent_type,
            "priority": priority,
            "platform": platform,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "deadline": (datetime.utcnow() + timedelta(hours=deadline_hours)).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "metadata": metadata or {},
            "attempts": 0,
            "blockers": []
        }

        self.tasks.append(task)
        self._save()
        print(f"[TASK_ENGINE] Created: {title} → {agent_type} ({priority})")
        return task_id

    def _pick_agent_for_task(self, text: str) -> str:
        """Auto-assign agent based on task keywords."""
        text_lower = text.lower()
        scores = {}
        for agent, capabilities in self.AGENT_CAPABILITIES.items():
            score = sum(1 for cap in capabilities if cap in text_lower)
            scores[agent] = score
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "orchestrator"

    def get_next_task(self, agent_type: str) -> Optional[Dict]:
        """Get highest priority pending task for an agent type."""
        pending = [t for t in self.tasks 
                   if t["status"] in ["queued", "blocked"] 
                   and t["agent_type"] == agent_type]
        if not pending:
            return None

        # Sort by priority then deadline
        pending.sort(key=lambda t: (self.PRIORITY_LEVELS.get(t["priority"], 3), t["deadline"]))
        return pending[0]

    def start_task(self, task_id: str):
        """Mark task as in-progress."""
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = "in_progress"
                t["started_at"] = datetime.utcnow().isoformat()
                t["attempts"] += 1
                self._save()
                print(f"[TASK_ENGINE] Started: {t['title']}")
                return True
        return False

    def complete_task(self, task_id: str, result: str):
        """Mark task complete with result."""
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = "completed"
                t["completed_at"] = datetime.utcnow().isoformat()
                t["result"] = result
                self.tasks.remove(t)
                self.completed.append(t)
                self._save()
                print(f"[TASK_ENGINE] Completed: {t['title']}")
                return True
        return False

    def block_task(self, task_id: str, reason: str):
        """Block task with reason."""
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = "blocked"
                t["blockers"].append({"reason": reason, "time": datetime.utcnow().isoformat()})
                self._save()
                print(f"[TASK_ENGINE] Blocked: {t['title']} — {reason}")
                return True
        return False

    def get_dashboard(self) -> Dict:
        """Get full empire task dashboard."""
        by_status = {}
        by_agent = {}
        for t in self.tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
            by_agent[t["agent_type"]] = by_agent.get(t["agent_type"], 0) + 1

        overdue = [t for t in self.tasks 
                   if t["status"] in ["queued", "in_progress", "blocked"]
                   and datetime.fromisoformat(t["deadline"]) < datetime.utcnow()]

        return {
            "total_active": len(self.tasks),
            "total_completed": len(self.completed),
            "by_status": by_status,
            "by_agent": by_agent,
            "overdue": len(overdue),
            "overdue_tasks": [t["title"] for t in overdue[:5]],
            "recent_completed": [t["title"] for t in self.completed[-5:]],
        }

    def auto_execute(self):
        """Run one cycle of autonomous task execution."""
        print("[TASK_ENGINE] Running auto-execution cycle...")

        for agent_type in self.AGENT_CAPABILITIES.keys():
            task = self.get_next_task(agent_type)
            if task and task["status"] == "queued":
                self.start_task(task["id"])

                # Use AI brain to execute the task
                if self.brain.is_configured():
                    prompt = f"Execute this empire task:\n\nTitle: {task['title']}\nDescription: {task['description']}\nPlatform: {task['platform']}\n\nProvide a detailed execution plan and result."
                    result = self.brain.think(prompt, agent_type=agent_type, 
                                              context={"platform": task["platform"], "task_id": task["id"]})
                    self.complete_task(task["id"], result)
                else:
                    self.complete_task(task["id"], f"Auto-executed by {agent_type} agent (AI offline)")

# Singleton
_task_engine = None

def get_task_engine() -> EmpireTaskEngine:
    global _task_engine
    if _task_engine is None:
        _task_engine = EmpireTaskEngine()
    return _task_engine
