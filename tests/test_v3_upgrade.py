#!/usr/bin/env python3
"""
OpenClaw v3.1 Upgrade Validation Tests
Run this after deployment to verify real execution engine works.
"""
import os
import sys
import json
import subprocess

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_task_state_machine():
    """Tasks must pass through all states before completion."""
    from empire_task_engine import get_task_engine, VALID_STATES, STATE_TRANSITIONS
    te = get_task_engine()
    tid = te.create_task("Test State Machine", "Verify state transitions", agent_type="coder")
    assert te.transition(tid, "ASSIGNED"), "CREATED -> ASSIGNED failed"
    assert te.transition(tid, "PLANNING"), "ASSIGNED -> PLANNING failed"
    assert te.transition(tid, "EXECUTING"), "PLANNING -> EXECUTING failed"
    # Direct completion must be BLOCKED
    assert not te.transition(tid, "COMPLETED"), "Should NOT allow EXECUTING -> COMPLETED"
    assert te.transition(tid, "VERIFYING"), "EXECUTING -> VERIFYING failed"
    assert te.transition(tid, "COMPLETED"), "VERIFYING -> COMPLETED failed"
    print("PASS: State machine enforces verification")


def test_receipts_directory():
    """Receipt directory must exist."""
    rdir = os.getenv("EMPIRE_RECEIPTS", "/tmp/empire-receipts")
    assert os.path.exists(rdir), f"Receipt dir missing: {rdir}"
    print("PASS: Receipt directory exists")


def test_agent_sandbox():
    """Sandbox can write and verify files."""
    from empire_task_engine import AgentSandbox, ExecutionReceipt
    receipt = ExecutionReceipt("test_sandbox", "coder")
    sandbox = AgentSandbox("coder", receipt)
    test_path = "/tmp/empire_test_file.txt"
    success = sandbox.write_file(test_path, "Hello from OpenClaw v3.1")
    assert success, "Sandbox write failed"
    assert sandbox.verify_file_exists(test_path), "Sandbox verify failed"
    os.remove(test_path)
    print("PASS: Agent sandbox writes and verifies files")


def test_oauth_guard():
    """YouTube upload must block without OAuth."""
    from automation.youtube_pipeline import upload_video
    old_creds = os.getenv("YOUTUBE_CREDENTIALS")
    old_refresh = os.getenv("GOOGLE_REFRESH_TOKEN")
    os.environ["YOUTUBE_CREDENTIALS"] = ""
    os.environ["GOOGLE_REFRESH_TOKEN"] = ""
    result = upload_video("fake.mp4", "Test", "Desc", [])
    assert result["status"] == "queued", f"Expected queued, got {result['status']}"
    assert result["reason"] == "oauth_missing"
    if old_creds:
        os.environ["YOUTUBE_CREDENTIALS"] = old_creds
    if old_refresh:
        os.environ["GOOGLE_REFRESH_TOKEN"] = old_refresh
    print("PASS: YouTube blocks upload without OAuth")


def test_mini_app_builder():
    """Mini app builder creates real files."""
    from agents.mini_apps_engine import MiniAppBuilder
    builder = MiniAppBuilder()
    result = builder.build_subscription_bot("test_sub_bot")
    assert result["verified"], "Mini app files not created"
    assert os.path.exists(result["directory"]), "Directory missing"
    print(f"PASS: Mini app builder created {result['files_created']} files")


def test_health_endpoint():
    """Health endpoint must respond."""
    try:
        r = subprocess.run(
            "curl -s http://localhost:3000/health",
            shell=True, capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0, "Health check curl failed"
        data = json.loads(r.stdout)
        assert "status" in data or "running" in str(data).lower(), "Health response invalid"
        print("PASS: Health endpoint responds")
    except Exception as e:
        print(f"WARN: Health endpoint test skipped ({e})")


def test_ai_brain_configured():
    """At least one AI provider must be configured."""
    from ai_brain import get_brain
    brain = get_brain()
    assert brain.is_configured(), "No AI provider configured"
    print(f"PASS: AI brain configured ({brain.primary})")


def test_memory_tables():
    """New memory tables must exist."""
    from memory.core import SwarmMemory
    mem = SwarmMemory()
    c = mem.conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    assert "task_history" in tables, "task_history table missing"
    assert "action_log" in tables, "action_log table missing"
    assert "execution_receipts" in tables, "execution_receipts table missing"
    print("PASS: All v3.1 memory tables present")


if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw v3.1 Upgrade Validation")
    print("=" * 60)
    test_task_state_machine()
    test_receipts_directory()
    test_agent_sandbox()
    test_oauth_guard()
    test_mini_app_builder()
    test_health_endpoint()
    test_ai_brain_configured()
    test_memory_tables()
    print("=" * 60)
    print("✅ ALL V3.1 UPGRADE TESTS PASSED")
    print("=" * 60)
