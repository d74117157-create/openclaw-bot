"""SQLite database layer for task persistence."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "tasks.db"
logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    """Return a new connection with Row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create the tasks table if it doesn't exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                task    TEXT    NOT NULL,
                result  TEXT,
                status  TEXT    NOT NULL DEFAULT 'pending',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    logger.info("Database initialised at %s", DB_PATH)


def save_task(task: str) -> int:
    """Insert a new pending task and return its ID."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (task, status) VALUES (?, 'pending')", (task,)
        )
        conn.commit()
        task_id = cur.lastrowid
    logger.info("Saved task #%d", task_id)
    return task_id


def update_task(task_id: int, result: str, status: str = "done") -> None:
    """Update a task's result and status."""
    with _connect() as conn:
        conn.execute(
            "UPDATE tasks SET result = ?, status = ? WHERE id = ?",
            (result, status, task_id),
        )
        conn.commit()
    logger.info("Updated task #%d -> %s", task_id, status)


def get_pending_tasks(limit: int = 5) -> list:
    """Return up to *limit* oldest pending tasks."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, task FROM tasks WHERE status = 'pending' "
            "ORDER BY id ASC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows


def get_task_by_id(task_id: int) -> Optional[sqlite3.Row]:
    """Fetch a single task by ID."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, task, result, status, created FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return row


def get_stats() -> dict:
    """Return counts by status for the !status command."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
    return {r["status"]: r["cnt"] for r in rows}
