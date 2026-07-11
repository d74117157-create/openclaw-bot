"""OpenClaw Superswarm — SQLite persistent memory."""
import sqlite3
import threading
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("MEMORY_DB", "openclaw_memory.db")
_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    with _lock:
        c = _conn().cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                agent TEXT DEFAULT 'orchestrator',
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                context TEXT,
                decision TEXT,
                outcome TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                status TEXT DEFAULT 'pending',
                log TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bot_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                role TEXT,
                platform TEXT,
                token_env TEXT,
                status TEXT DEFAULT 'active',
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.connection.commit()
        c.connection.close()


def save_task(description: str, agent: str = "orchestrator") -> int:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("INSERT INTO tasks (description, agent) VALUES (?, ?)", (description, agent))
        tid = c.lastrowid
        conn.commit()
        conn.close()
        return tid


def update_task(tid: int, result: str, status: str = "done") -> None:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            "UPDATE tasks SET result = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (result, status, tid),
        )
        conn.commit()
        conn.close()


def get_stats() -> Dict[str, int]:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM tasks")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
        done = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'failed'")
        failed = c.fetchone()[0]
        conn.close()
        return {"total": total, "done": done, "failed": failed}


def get_tasks(limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            "SELECT id, description, agent, status, created_at FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {"id": r[0], "description": r[1], "agent": r[2], "status": r[3], "created_at": r[4]}
            for r in rows
        ]


def get_failed_tasks(limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            "SELECT id, description, agent, status, created_at FROM tasks WHERE status = 'failed' ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {"id": r[0], "description": r[1], "agent": r[2], "status": r[3], "created_at": r[4]}
            for r in rows
        ]


def save_decision(context: str, decision: str, outcome: str = "", tags: List[str] = None) -> None:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO decisions (context, decision, outcome, tags) VALUES (?, ?, ?, ?)",
            (context, decision, outcome, json.dumps(tags or [])),
        )
        conn.commit()
        conn.close()


def search_decisions(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            "SELECT id, context, decision, outcome, tags, created_at FROM decisions WHERE context LIKE ? OR decision LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": r[0], "context": r[1], "decision": r[2],
                "outcome": r[3], "tags": json.loads(r[4] or "[]"), "created_at": r[5],
            }
            for r in rows
        ]


def save_deployment(target: str, status: str = "pending", log: str = "") -> None:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO deployments (target, status, log) VALUES (?, ?, ?)",
            (target, status, log),
        )
        conn.commit()
        conn.close()


def register_bot(name: str, role: str, platform: str, token_env: str, status: str = "active") -> None:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute(
            """INSERT INTO bot_registry (name, role, platform, token_env, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                role=excluded.role, platform=excluded.platform, token_env=excluded.token_env, status=excluded.status""",
            (name, role, platform, token_env, status),
        )
        conn.commit()
        conn.close()


def get_active_bots() -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT name, role, platform, token_env, status FROM bot_registry WHERE status = 'active'")
        rows = c.fetchall()
        conn.close()
        return [
            {"name": r[0], "role": r[1], "platform": r[2], "token_env": r[3], "status": r[4]}
            for r in rows
        ]
