"""
OpenClaw — tests/test_memory.py
Unit tests for the memory/SQLite layer.
"""
import os, pytest

os.environ["MEMORY_DB"] = ":memory:"

from memory import init_db, save_task, update_task, get_stats, get_recent_tasks, get_failed_tasks, save_decision, search_decisions


@pytest.fixture(autouse=True)
def setup():
    init_db()
    yield


def test_save_and_update_task():
    tid = save_task("Build a Discord bot", "coder")
    assert isinstance(tid, int)
    assert tid > 0
    update_task(tid, "Bot built successfully", "done")
    recent = get_recent_tasks(5)
    assert any(t["id"] == tid for t in recent)


def test_stats_accumulate():
    save_task("Task A", "coder")
    save_task("Task B", "ops")
    stats = get_stats()
    assert stats.get("total_tasks", 0) >= 2


def test_failed_tasks():
    tid = save_task("Failing task", "qa")
    update_task(tid, "RuntimeError: crash", "failed")
    failures = get_failed_tasks()
    assert any(t["id"] == tid for t in failures)


def test_save_and_search_decision():
    save_decision("Should we use Groq?", "Yes, llama3-70b", "success", ["ai", "groq"])
    results = search_decisions("Groq")
    assert len(results) > 0
    assert "Groq" in results[0]["context"] or "Groq" in results[0]["decision"]


def test_get_recent_tasks_limit():
    for i in range(15):
        save_task(f"Task {i}", "research")
    recent = get_recent_tasks(10)
    assert len(recent) <= 10
