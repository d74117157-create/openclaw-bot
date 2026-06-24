"""
OpenClaw Elite — Persistent Long-Term Memory
Projects, deployments, goals, preferences, conversations, open tasks.
Supports: store, update, retrieve, summarize. Resumes work across sessions.
"""
import os
import json
import sqlite3
import threading
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger("elite_memory")

DB_PATH = os.environ.get("MEMORY_DB", "openclaw_memory.db")
_lock = threading.Lock()


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_elite_memory():
    """Initialize all elite memory tables."""
    with _lock:
        con = _conn()
        cur = con.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                status TEXT DEFAULT 'active',
                metadata TEXT,
                created TEXT DEFAULT (datetime('now')),
                updated TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                platform TEXT,
                username TEXT,
                preferences TEXT,
                goals TEXT,
                context TEXT,
                created TEXT DEFAULT (datetime('now')),
                updated TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                user_id TEXT,
                platform TEXT,
                message TEXT,
                response TEXT,
                intent TEXT,
                agent TEXT,
                confidence REAL,
                created TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS open_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                agent TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'medium',
                dependencies TEXT,
                context TEXT,
                result TEXT,
                created TEXT DEFAULT (datetime('now')),
                updated TEXT DEFAULT (datetime('now')),
                completed TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS deployment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                platform TEXT,
                status TEXT,
                commit_hash TEXT,
                url TEXT,
                metadata TEXT,
                created TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                due_date TEXT,
                created TEXT DEFAULT (datetime('now')),
                updated TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT,
                snapshot TEXT NOT NULL,
                created TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_thread ON conversations(thread_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON open_tasks(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_snap_session ON memory_snapshots(session_id)")

        con.commit()
        con.close()
        logger.info("Elite memory tables initialized")


class EliteMemory:
    """High-level memory interface for the multi-agent system."""

    def __init__(self):
        init_elite_memory()

    def store_project(self, name: str, description: str, metadata: dict = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO projects (name, description, metadata, updated) VALUES (?, ?, ?, datetime('now'))",
                (name, description, json.dumps(metadata or {}))
            )
            con.commit()
            project_id = cur.lastrowid
            con.close()
            return {"id": project_id, "name": name, "status": "stored"}

    def get_project(self, name: str) -> Optional[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cur.fetchone()
            con.close()
            if row:
                return {
                    "id": row[0], "name": row[1], "description": row[2],
                    "status": row[3], "metadata": json.loads(row[4] or "{}"),
                    "created": row[5], "updated": row[6]
                }
            return None

    def list_projects(self, status: str = None) -> List[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            if status:
                cur.execute("SELECT * FROM projects WHERE status = ? ORDER BY updated DESC", (status,))
            else:
                cur.execute("SELECT * FROM projects ORDER BY updated DESC")
            rows = cur.fetchall()
            con.close()
            return [
                {"id": r[0], "name": r[1], "description": r[2], "status": r[3],
                 "metadata": json.loads(r[4] or "{}"), "created": r[5], "updated": r[6]}
                for r in rows
            ]

    def store_user_profile(self, user_id: str, platform: str, username: str, 
                          preferences: dict = None, goals: list = None, context: dict = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """INSERT OR REPLACE INTO user_profiles 
                   (user_id, platform, username, preferences, goals, context, updated)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (user_id, platform, username, 
                 json.dumps(preferences or {}), 
                 json.dumps(goals or []), 
                 json.dumps(context or {}))
            )
            con.commit()
            con.close()
            return {"user_id": user_id, "status": "profile_stored"}

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            con.close()
            if row:
                return {
                    "user_id": row[1], "platform": row[2], "username": row[3],
                    "preferences": json.loads(row[4] or "{}"),
                    "goals": json.loads(row[5] or "[]"),
                    "context": json.loads(row[6] or "{}"),
                    "created": row[7], "updated": row[8]
                }
            return None

    def update_preferences(self, user_id: str, preferences: dict) -> dict:
        profile = self.get_user_profile(user_id)
        existing = profile.get("preferences", {}) if profile else {}
        existing.update(preferences)
        return self.store_user_profile(
            user_id, 
            profile.get("platform", "unknown") if profile else "unknown",
            profile.get("username", "unknown") if profile else "unknown",
            preferences=existing
        )

    def store_conversation(self, thread_id: str, user_id: str, platform: str,
                          message: str, response: str, intent: str, agent: str, confidence: float) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """INSERT INTO conversations 
                   (thread_id, user_id, platform, message, response, intent, agent, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (thread_id, user_id, platform, message, response, intent, agent, confidence)
            )
            con.commit()
            con.close()
            return {"thread_id": thread_id, "stored": True}

    def get_conversation_thread(self, thread_id: str, limit: int = 50) -> List[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """SELECT * FROM conversations WHERE thread_id = ? 
                   ORDER BY created DESC LIMIT ?""",
                (thread_id, limit)
            )
            rows = cur.fetchall()
            con.close()
            return [
                {"id": r[0], "thread_id": r[1], "user_id": r[2], "platform": r[3],
                 "message": r[4], "response": r[5], "intent": r[6], 
                 "agent": r[7], "confidence": r[8], "created": r[9]}
                for r in reversed(rows)
            ]

    def get_user_conversations(self, user_id: str, limit: int = 20) -> List[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """SELECT * FROM conversations WHERE user_id = ? 
                   ORDER BY created DESC LIMIT ?""",
                (user_id, limit)
            )
            rows = cur.fetchall()
            con.close()
            return [
                {"id": r[0], "thread_id": r[1], "user_id": r[2], "platform": r[3],
                 "message": r[4], "response": r[5], "intent": r[6], 
                 "agent": r[7], "confidence": r[8], "created": r[9]}
                for r in rows
            ]

    def summarize_conversation(self, thread_id: str) -> str:
        messages = self.get_conversation_thread(thread_id)
        if not messages:
            return "No conversation history found."
        topics = set(m["intent"] for m in messages if m["intent"])
        agents_used = set(m["agent"] for m in messages if m["agent"])
        summary = f"Conversation Summary ({len(messages)} messages)\n"
        summary += f"Topics: {', '.join(topics)}\n"
        summary += f"Agents involved: {', '.join(agents_used)}\n"
        summary += f"Started: {messages[0]['created']}\n"
        summary += f"Latest: {messages[-1]['created']}\n"
        key_points = []
        for m in messages:
            if m["intent"] and ("complete" in m["intent"] or "success" in m["intent"]):
                key_points.append(f"- {m['agent']}: {m['message'][:100]}")
        if key_points:
            summary += "\nKey points:\n" + "\n".join(key_points[:5])
        return summary

    def store_task(self, task_id: str, description: str, agent: str = None,
                   priority: str = "medium", dependencies: list = None, context: dict = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """INSERT OR REPLACE INTO open_tasks 
                   (task_id, description, agent, priority, dependencies, context, updated)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (task_id, description, agent, priority, 
                 json.dumps(dependencies or []), json.dumps(context or {}))
            )
            con.commit()
            con.close()
            return {"task_id": task_id, "status": "stored"}

    def update_task(self, task_id: str, status: str = None, result: str = None, 
                    context: dict = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            updates = []
            params = []
            if status:
                updates.append("status = ?")
                params.append(status)
                if status == "completed":
                    updates.append("completed = datetime('now')")
            if result:
                updates.append("result = ?")
                params.append(result)
            if context:
                updates.append("context = ?")
                params.append(json.dumps(context))
            if updates:
                updates.append("updated = datetime('now')")
                query = f"UPDATE open_tasks SET {', '.join(updates)} WHERE task_id = ?"
                params.append(task_id)
                cur.execute(query, params)
                con.commit()
            con.close()
            return {"task_id": task_id, "updated": True}

    def get_open_tasks(self, agent: str = None) -> List[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            if agent:
                cur.execute(
                    "SELECT * FROM open_tasks WHERE status IN ('open', 'in_progress') AND agent = ? ORDER BY created DESC",
                    (agent,)
                )
            else:
                cur.execute(
                    "SELECT * FROM open_tasks WHERE status IN ('open', 'in_progress') ORDER BY created DESC"
                )
            rows = cur.fetchall()
            con.close()
            return [
                {"id": r[0], "task_id": r[1], "description": r[2], "agent": r[3],
                 "status": r[4], "priority": r[5], "dependencies": json.loads(r[6] or "[]"),
                 "context": json.loads(r[7] or "{}"), "result": r[8],
                 "created": r[9], "updated": r[10], "completed": r[11]}
                for r in rows
            ]

    def store_deployment(self, project_name: str, platform: str, status: str,
                         commit_hash: str = None, url: str = None, metadata: dict = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """INSERT INTO deployment_history 
                   (project_name, platform, status, commit_hash, url, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_name, platform, status, commit_hash, url, json.dumps(metadata or {}))
            )
            con.commit()
            con.close()
            return {"project": project_name, "status": "logged"}

    def get_deployments(self, project_name: str = None, limit: int = 10) -> List[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            if project_name:
                cur.execute(
                    "SELECT * FROM deployment_history WHERE project_name = ? ORDER BY created DESC LIMIT ?",
                    (project_name, limit)
                )
            else:
                cur.execute(
                    "SELECT * FROM deployment_history ORDER BY created DESC LIMIT ?", (limit,)
                )
            rows = cur.fetchall()
            con.close()
            return [
                {"id": r[0], "project": r[1], "platform": r[2], "status": r[3],
                 "commit_hash": r[4], "url": r[5], "metadata": json.loads(r[6] or "{}"),
                 "created": r[7]}
                for r in rows
            ]

    def store_goal(self, user_id: str, title: str, description: str = None,
                   due_date: str = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """INSERT INTO goals (user_id, title, description, due_date)
                   VALUES (?, ?, ?, ?)""",
                (user_id, title, description, due_date)
            )
            con.commit()
            goal_id = cur.lastrowid
            con.close()
            return {"goal_id": goal_id, "title": title, "status": "active"}

    def update_goal_progress(self, goal_id: int, progress: float, status: str = None) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            if status:
                cur.execute(
                    "UPDATE goals SET progress = ?, status = ?, updated = datetime('now') WHERE id = ?",
                    (progress, status, goal_id)
                )
            else:
                cur.execute(
                    "UPDATE goals SET progress = ?, updated = datetime('now') WHERE id = ?",
                    (progress, goal_id)
                )
            con.commit()
            con.close()
            return {"goal_id": goal_id, "progress": progress}

    def get_user_goals(self, user_id: str) -> List[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM goals WHERE user_id = ? ORDER BY updated DESC",
                (user_id,)
            )
            rows = cur.fetchall()
            con.close()
            return [
                {"id": r[0], "user_id": r[1], "title": r[2], "description": r[3],
                 "status": r[4], "progress": r[5], "due_date": r[6],
                 "created": r[7], "updated": r[8]}
                for r in rows
            ]

    def save_snapshot(self, session_id: str, user_id: str, snapshot: dict) -> dict:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO memory_snapshots (session_id, user_id, snapshot) VALUES (?, ?, ?)",
                (session_id, user_id, json.dumps(snapshot))
            )
            con.commit()
            con.close()
            return {"session_id": session_id, "saved": True}

    def get_latest_snapshot(self, session_id: str) -> Optional[dict]:
        with _lock:
            con = _conn()
            cur = con.cursor()
            cur.execute(
                """SELECT * FROM memory_snapshots WHERE session_id = ? 
                   ORDER BY created DESC LIMIT 1""",
                (session_id,)
            )
            row = cur.fetchone()
            con.close()
            if row:
                return {
                    "session_id": row[1], "user_id": row[2],
                    "snapshot": json.loads(row[3]), "created": row[4]
                }
            return None

    def get_resume_context(self, user_id: str) -> dict:
        profile = self.get_user_profile(user_id) or {}
        open_tasks = self.get_open_tasks()
        user_goals = self.get_user_goals(user_id)
        recent_conversations = self.get_user_conversations(user_id, limit=5)
        user_tasks = [t for t in open_tasks if t.get("context", {}).get("user_id") == user_id]
        return {
            "user_profile": profile,
            "open_tasks": user_tasks,
            "goals": user_goals,
            "recent_conversations": recent_conversations,
            "has_previous_session": len(recent_conversations) > 0,
            "summary": self._generate_resume_summary(profile, user_tasks, user_goals)
        }

    def _generate_resume_summary(self, profile, tasks, goals) -> str:
        parts = []
        if profile.get("username"):
            parts.append(f"Welcome back, {profile['username']}!")
        if tasks:
            parts.append(f"You have {len(tasks)} open task(s).")
        if goals:
            active_goals = [g for g in goals if g["status"] == "active"]
            if active_goals:
                parts.append(f"Active goals: {len(active_goals)}.")
        return " ".join(parts) if parts else "New session started."

    def search_memories(self, query: str, user_id: str = None, limit: int = 10) -> List[dict]:
        query_lower = query.lower()
        results = []
        with _lock:
            con = _conn()
            cur = con.cursor()
            if user_id:
                cur.execute(
                    "SELECT * FROM conversations WHERE user_id = ? AND (message LIKE ? OR response LIKE ?) ORDER BY created DESC LIMIT ?",
                    (user_id, f"%{query_lower}%", f"%{query_lower}%", limit)
                )
            else:
                cur.execute(
                    "SELECT * FROM conversations WHERE message LIKE ? OR response LIKE ? ORDER BY created DESC LIMIT ?",
                    (f"%{query_lower}%", f"%{query_lower}%", limit)
                )
            rows = cur.fetchall()
            con.close()
            for r in rows:
                results.append({
                    "type": "conversation", "id": r[0], "message": r[4],
                    "response": r[5], "agent": r[7], "created": r[9]
                })
        return results


_memory_instance = None

def get_memory() -> EliteMemory:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = EliteMemory()
    return _memory_instance
