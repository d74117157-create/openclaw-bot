"""
OpenClaw - memory/__init__.py
SQLite persistent memory for tasks, decisions, and deployments.
"""
import sqlite3, threading, json, os
from datetime import datetime

DB_PATH = os.environ.get("MEMORY_DB", "openclaw_memory.db")
_lock   = threading.Lock()


def init_db():
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                agent TEXT,
                status TEXT DEFAULT "pending",
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                decision TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                status TEXT DEFAULT "pending",
                log TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()


def save_task(description: str, agent: str = "orchestrator") -> int:
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (description, agent) VALUES (?, ?)", (description, agent))
        tid = c.lastrowid
        conn.commit()
        conn.close()
        return tid


def update_task(tid: int, result: str, status: str = "done"):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE tasks SET result = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (result, status, tid)
        )
        conn.commit()
        conn.close()


def get_stats() -> dict:
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM tasks")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
        done = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'failed'")
        failed = c.fetchone()[0]
        conn.close()
        return {"total": total, "done": done, "failed": failed}


def get_tasks(limit: int = 20) -> list:
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT id, description, agent, status, created_at FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = c.fetchall()
        conn.close()
        return [
            {"id": r[0], "description": r[1], "agent": r[2], "status": r[3], "created_at": r[4]}
            for r in rows
        ]


def save_decision(task_id: int, decision: str, confidence: float):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO decisions (task_id, decision, confidence) VALUES (?, ?, ?)",
            (task_id, decision, confidence)
        )
        conn.commit()
        conn.close()


def save_deployment(target: str, status: str = "pending", log: str = ""):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO deployments (target, status, log) VALUES (?, ?, ?)",
            (target, status, log)
        )
        conn.commit()
        conn.close()
