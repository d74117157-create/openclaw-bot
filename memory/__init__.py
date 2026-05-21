"""
OpenClaw - memory/__init__.py
SQLite persistent memory: tasks, decisions, deployments tables.
"""
import sqlite3, os, threading
from datetime import datetime

DB_PATH = os.environ.get("MEMORY_DB", "openclaw_memory.db")
_lock = threading.Lock()


def _conn():
        return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
        """Create tables if they do not exist."""
        with _lock:
                    con = _conn()
                    cur = con.cursor()
                    cur.executescript("""
                        CREATE TABLE IF NOT EXISTS tasks (
                            id        INTEGER PRIMARY KEY AUTOINCREMENT,
                            desc      TEXT NOT NULL,
                            agent     TEXT NOT NULL,
                            result    TEXT,
                            status    TEXT DEFAULT 'pending',
                            created   TEXT DEFAULT (datetime('now')),
                            updated   TEXT DEFAULT (datetime('now'))
                        );
                        CREATE TABLE IF NOT EXISTS decisions (
                            id        INTEGER PRIMARY KEY AUTOINCREMENT,
                            context   TEXT NOT NULL,
                            decision  TEXT NOT NULL,
                            created   TEXT DEFAULT (datetime('now'))
                        );
                        CREATE TABLE IF NOT EXISTS deployments (
                            id        INTEGER PRIMARY KEY AUTOINCREMENT,
                            service   TEXT NOT NULL,
                            status    TEXT NOT NULL,
                            notes     TEXT,
                            created   TEXT DEFAULT (datetime('now'))
                        );
                    """)
                    con.commit()
                    con.close()


def save_task(desc: str, agent: str) -> int:
        """Insert a new task and return its id."""
        with _lock:
                    con = _conn()
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO tasks (desc, agent) VALUES (?, ?)",
                        (desc, agent)
                    )
                    tid = cur.lastrowid
                    con.commit()
                    con.close()
                return tid


def update_task(tid: int, result: str, status: str = "done"):
        """Update task result and status."""
    with _lock:
                con = _conn()
                cur = con.cursor()
                cur.execute(
                    "UPDATE tasks SET result=?, status=?, updated=datetime('now') WHERE id=?",
                    (result, status, tid)
                )
                con.commit()
                con.close()


def get_tasks(limit: int = 20) -> list:
        """Return recent tasks."""
    with _lock:
                con = _conn()
                cur = con.cursor()
                cur.execute(
                    "SELECT id, desc, agent, status, created FROM tasks ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                rows = cur.fetchall()
                con.close()
            return rows


def save_decision(context: str, decision: str):
        """Record a decision."""
    with _lock:
                con = _conn()
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO decisions (context, decision) VALUES (?, ?)",
                    (context, decision)
                )
                con.commit()
                con.close()


def save_deployment(service: str, status: str, notes: str = ""):
        """Record a deployment event."""
    with _lock:
                con = _conn()
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO deployments (service, status, notes) VALUES (?, ?, ?)",
                    (service, status, notes)
                )
                con.commit()
                con.close()


def get_stats() -> dict:
        """Return a summary of current memory state."""
    with _lock:
                con = _conn()
                cur = con.cursor()
                cur.execute("SELECT COUNT(*) FROM tasks")
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM tasks WHERE status='done'")
                done = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM tasks WHERE status='failed'")
                failed = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM decisions")
                decisions = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM deployments")
                deploys = cur.fetchone()[0]
                con.close()
            return {
                        "tasks_total": total,
                        "tasks_done": done,
                        "tasks_failed": failed,
                        "decisions": decisions,
                        "deployments": deploys,
            }
