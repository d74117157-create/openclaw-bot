from .core import init_db, save_task, update_task, get_pending_tasks, get_stats"""
OpenClaw — memory/__init__.py
Persistent SQLite task + decision memory for the swarm.
"""
import os, sqlite3, json
from datetime import datetime

DB_PATH = os.environ.get("MEMORY_DB", "openclaw_memory.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            desc     TEXT NOT NULL,
            agent    TEXT NOT NULL,
            status   TEXT DEFAULT 'pending',
            result   TEXT,
            created  TEXT DEFAULT (datetime('now')),
            updated  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS decisions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            context  TEXT NOT NULL,
            decision TEXT NOT NULL,
            outcome  TEXT,
            tags     TEXT,
            created  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS deployments (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            service   TEXT NOT NULL,
            version   TEXT,
            env       TEXT,
            status    TEXT DEFAULT 'deployed',
            notes     TEXT,
            created   TEXT DEFAULT (datetime('now'))
        );
        """)


def save_task(desc: str, agent: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO tasks (desc, agent, status) VALUES (?, ?, 'running')",
            (desc, agent)
        )
        return cur.lastrowid


def update_task(task_id: int, result: str, status: str = "done"):
    with _conn() as c:
        c.execute(
            "UPDATE tasks SET result=?, status=?, updated=datetime('now') WHERE id=?",
            (result, status, task_id)
        )


def save_decision(context: str, decision: str, outcome: str = "", tags: list = None):
    with _conn() as c:
        c.execute(
            "INSERT INTO decisions (context, decision, outcome, tags) VALUES (?, ?, ?, ?)",
            (context, decision, outcome, json.dumps(tags or []))
        )


def save_deployment(service: str, version: str, env: str, notes: str = ""):
    with _conn() as c:
        c.execute(
            "INSERT INTO deployments (service, version, env, notes) VALUES (?, ?, ?, ?)",
            (service, version, env, notes)
        )


def get_stats() -> dict:
    with _conn() as c:
        rows = c.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        total = c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        deploys = c.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
        decisions = c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    stats = {r["status"]: r["cnt"] for r in rows}
    stats["total_tasks"] = total
    stats["deployments"] = deploys
    stats["decisions"] = decisions
    return stats


def get_recent_tasks(limit: int = 10) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, desc, agent, status, created FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_failed_tasks() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, desc, agent, result FROM tasks WHERE status='failed' ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def search_decisions(query: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM decisions WHERE context LIKE ? OR decision LIKE ? ORDER BY id DESC LIMIT 20",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
    return [dict(r) for r in rows]
