"""
OpenClaw Master Brain — Persistent Memory
Tasks, decisions, cross-platform sessions
FIXED: Added write queue, data directory creation, better concurrency handling.
"""
import sqlite3
import os
import threading
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from queue import Queue

DB_PATH = os.environ.get("MEMORY_DB", "/app/data/openclaw_memory.db")
_lock = threading.Lock()
_write_queue = Queue()

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Create all tables."""
    # FIXED: Ensure directory exists for persistent storage
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            desc TEXT NOT NULL,
            agent TEXT NOT NULL,
            platform TEXT DEFAULT 'unknown',
            user_id TEXT,
            result TEXT,
            status TEXT DEFAULT 'pending',
            created TEXT DEFAULT (datetime('now')),
            updated TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context TEXT NOT NULL,
            decision TEXT NOT NULL,
            platform TEXT,
            status TEXT DEFAULT 'success',
            created TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo TEXT NOT NULL,
            branch TEXT,
            status TEXT,
            created TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cross_platform_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unified_user_id TEXT NOT NULL,
            telegram_id TEXT,
            discord_id TEXT,
            slack_id TEXT,
            last_active TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unified_user_id TEXT,
            platform TEXT NOT NULL,
            platform_user_id TEXT,
            message TEXT,
            response TEXT,
            created TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_sessions_unified ON cross_platform_sessions(unified_user_id);
        """)
        con.commit()
        con.close()

def save_task(desc: str, agent: str = "unknown", platform: str = "unknown", user_id: str = None) -> str:
    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO tasks (desc, agent, platform, user_id) VALUES (?, ?, ?, ?)",
            (desc, agent, platform, user_id)
        )
        tid = cur.lastrowid
        con.commit()
        con.close()
        return f"task_{tid}"

def update_task(task_id: str, result: str, status: str = "done"):
    try:
        tid = int(task_id.replace("task_", ""))
    except ValueError:
        return

    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute(
            "UPDATE tasks SET result=?, status=?, updated=datetime('now') WHERE id=?",
            (result, status, tid)
        )
        con.commit()
        con.close()

def get_task(task_id: str) -> Optional[dict]:
    try:
        tid = int(task_id.replace("task_", ""))
    except ValueError:
        return None

    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute("SELECT * FROM tasks WHERE id=?", (tid,))
        row = cur.fetchone()
        con.close()
        if row:
            return {
                "id": f"task_{row[0]}", "description": row[1], "agent": row[2],
                "platform": row[3], "user_id": row[4],
                "result": row[5], "status": row[6],
                "created_at": row[7], "updated_at": row[8]
            }
        return None

def get_pending_tasks() -> List[dict]:
    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute("SELECT * FROM tasks WHERE status='pending'")
        rows = cur.fetchall()
        con.close()
        return [{
            "id": f"task_{row[0]}", "description": row[1], "agent": row[2],
            "platform": row[3], "user_id": row[4],
            "status": row[6]
        } for row in rows]

def get_stats() -> dict:
    with _lock:
        con = _conn()
        cur = con.cursor()
        stats = {}
        for key, query in [
            ("tasks_total", "SELECT COUNT(*) FROM tasks"),
            ("tasks_done", "SELECT COUNT(*) FROM tasks WHERE status='done'"),
            ("tasks_failed", "SELECT COUNT(*) FROM tasks WHERE status='failed'"),
            ("tasks_pending", "SELECT COUNT(*) FROM tasks WHERE status='pending'"),
            ("decisions", "SELECT COUNT(*) FROM decisions"),
            ("sessions", "SELECT COUNT(*) FROM cross_platform_sessions"),
            ("deployments", "SELECT COUNT(*) FROM deployments"),
        ]:
            try:
                cur.execute(query)
                stats[key] = cur.fetchone()[0]
            except:
                stats[key] = 0
        con.close()
        return stats

def save_decision(action: str, context: str, outcome: str = "success"):
    """Compatibility wrapper for save_decision(action, context, outcome)"""
    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO decisions (context, decision, platform, status) VALUES (?, ?, ?, ?)",
            (context, action, "system", outcome)
        )
        con.commit()
        con.close()

def save_deployment(repo: str, branch: str, status: str = "triggered"):
    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO deployments (repo, branch, status) VALUES (?, ?, ?)",
            (repo, branch, status)
        )
        con.commit()
        con.close()

def get_or_create_unified_user(telegram_id: str = None, discord_id: str = None, slack_id: str = None) -> str:
    """Get or create a unified cross-platform user ID."""
    with _lock:
        con = _conn()
        cur = con.cursor()

        unified_id = None
        if telegram_id:
            cur.execute("SELECT unified_user_id FROM cross_platform_sessions WHERE telegram_id=?", (telegram_id,))
            row = cur.fetchone()
            if row: unified_id = row[0]
        elif discord_id:
            cur.execute("SELECT unified_user_id FROM cross_platform_sessions WHERE discord_id=?", (discord_id,))
            row = cur.fetchone()
            if row: unified_id = row[0]
        elif slack_id:
            cur.execute("SELECT unified_user_id FROM cross_platform_sessions WHERE slack_id=?", (slack_id,))
            row = cur.fetchone()
            if row: unified_id = row[0]

        if not unified_id:
            unified_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO cross_platform_sessions (unified_user_id, telegram_id, discord_id, slack_id) VALUES (?, ?, ?, ?)",
                (unified_id, telegram_id, discord_id, slack_id)
            )
            con.commit()

        con.close()
        return unified_id

def search_decisions(query: str, limit: int = 10) -> list:
    """Search decisions by keyword in context or decision text."""
    with _lock:
        con = _conn()
        cur = con.cursor()
        like = f"%{query}%"
        cur.execute(
            "SELECT context, decision, platform, status, created FROM decisions "
            "WHERE context LIKE ? OR decision LIKE ? ORDER BY created DESC LIMIT ?",
            (like, like, limit)
        )
        rows = cur.fetchall()
        con.close()
        return [{"context": r[0], "decision": r[1], "platform": r[2], "status": r[3], "created": r[4]} for r in rows]

def get_recent_tasks(limit: int = 10) -> list:
    """Return most recently updated tasks."""
    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute(
            "SELECT id, desc, agent, platform, status, result, updated FROM tasks ORDER BY updated DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        con.close()
        return [{"id": f"task_{r[0]}", "description": r[1], "agent": r[2],
                "platform": r[3], "status": r[4], "result": r[5], "updated": r[6]} for r in rows]

def get_failed_tasks(limit: int = 20) -> list:
    """Return recent failed tasks."""
    with _lock:
        con = _conn()
        cur = con.cursor()
        cur.execute(
            "SELECT id, desc, agent, platform, result, updated FROM tasks WHERE status='failed' ORDER BY updated DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        con.close()
        return [{"id": f"task_{r[0]}", "description": r[1], "agent": r[2],
                "platform": r[3], "result": r[4], "updated": r[5]} for r in rows]
