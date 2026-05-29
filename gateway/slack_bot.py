"""
OpenClaw - gateway/slack_bot.py
Slack gateway: listens for @mentions + slash commands, routes to agent swarm.
FIXED: Complete indentation, async safety, proper error handling.
"""
import os
import json
import threading
import time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS
from worker.slack_reporter import task_started, agent_complete, task_complete

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "openclaw-ops")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("❌ SLACK_BOT_TOKEN and SLACK_APP_TOKEN required in .env")

app = App(token=SLACK_BOT_TOKEN)


# ── Helpers ────────────────────────────────────────────────────────────

def _run_agent_sync(agent: str, task_desc: str, say, thread_ts=None) -> str:
    """Run a single agent on a task synchronously."""
    tid = save_task(task_desc, agent)
    try:
        result = process_task(task_desc, agent)
        update_task(tid, result, "done")
        preview = result[:2800]
        
        # Post result to Slack
        agent_complete(agent, task_desc, result, success=True)
        
        return result
    except Exception as e:
        error_msg = str(e)
        update_task(tid, error_msg, "failed")
        agent_complete(agent, task_desc, error_msg, success=False)
        say(f"❌ **[{agent.upper()}]** failed: {error_msg[:200]}", thread_ts=thread_ts)
        return ""


def _quick_reply(say, message: str, thread_ts=None):
    """Send a quick reply to Slack."""
    say(text=message, thread_ts=thread_ts)


# ── @mention handler ───────────────────────────────────────────────────

@app.event("app_mention")
def handle_mention(event, say):
    """Handle @mentions in Slack."""
    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    
    # Remove @mentions from task
    task = " ".join(w for w in text.split() if not w.startswith("<@")).strip()

    if not task:
        say("🧠 **MAIN BRAIN** ready. Tell me what to do.", thread_ts=thread_ts)
        return

    say(f"🧠 **MAIN BRAIN** received:\n```{task[:100]}```\n⏳ Orchestrating swarm...", thread_ts=thread_ts)

    # Orchestrate task into subtasks
    try:
        plan_raw = orchestrate_task(task)
        plan = json.loads(plan_raw)
    except Exception as e:
        plan = [{"agent": "orchestrator", "task": task}]
        say(f"⚠️ Planner fallback: {str(e)[:100]}", thread_ts=thread_ts)

    # Filter valid agents
    valid_plan = [p for p in plan if p.get("agent") in AGENT_PERSONAS]
    
    if not valid_plan:
        valid_plan = [{"agent": "orchestrator", "task": task}]

    agent_names = " → ".join(f"`{p['agent']}`" for p in valid_plan)
    say(f"📋 **Plan:** {agent_names}", thread_ts=thread_ts)
    save_decision(task, f"Slack orchestrated: {agent_names}")

    # Notify task start
    task_started(task, valid_plan, needs_browser=False)

    # Run agents in parallel threads
    threads = []
    for step in valid_plan:
        agent = step.get("agent")
        subtask = step.get("task", task)
        if agent in AGENT_PERSONAS:
            t = threading.Thread(
                target=_run_agent_sync,
                args=(agent, subtask, say, thread_ts),
                daemon=False
            )
            t.start()
            threads.append(t)

    # Wait for all agents to complete
    for t in threads:
        t.join(timeout=60)

    say(f"✅ **All agents complete.** Results posted above.", thread_ts=thread_ts)


# ── /swarm command ─────────────────────────────────────────────────────

@app.command("/swarm")
def slack_swarm(ack, body, say):
    """Slack /swarm command: manually pick agents."""
    ack()
    
    text = body.get("text", "").strip()
    if not text or " " not in text:
        say("📝 Usage: `/swarm coder,ops,qa task description here`")
        return

    parts = text.split(" ", 1)
    agents = [a.strip() for a in parts[0].split(",")]
    task_desc = parts[1]

    bad = [a for a in agents if a not in AGENT_PERSONAS]
    if bad:
        available = ", ".join(AGENT_PERSONAS.keys())
        say(f"❌ Unknown agents: `{', '.join(bad)}`\n✅ Available: `{available}`")
        return

    say(f"🐝 **Swarm starting:** `{', '.join(agents)}`\n📌 Task: _{task_desc[:80]}_")
    
    # Notify task start
    task_started(task_desc, [{"agent": a, "task": task_desc} for a in agents], needs_browser=False)

    # Run agents in parallel
    threads = []
    for agent in agents:
        t = threading.Thread(
            target=_run_agent_sync,
            args=(agent, task_desc, say),
            daemon=False
        )
        t.start()
        threads.append(t)

    # Wait for all to complete
    for t in threads:
        t.join(timeout=60)

    say("✅ **Swarm complete.**")


# ── /deploy command ───────────────────────────────────────────────────

@app.command("/deploy")
def slack_deploy(ack, body, say):
    """Slack /deploy command: trigger deployment."""
    ack()
    
    service = body.get("text", "").strip() or "openclaw-bot"
    say(f"🚀 **Deploying:** `{service}`\n⏳ OPS agent running...")
    
    task_desc = f"Create Railway deployment plan for {service}: Dockerfile, env vars, health check, rollback strategy."
    _run_agent_sync("ops", task_desc, say)


# ── /ocstatus command ──────────────────────────────────────────────────

@app.command("/ocstatus")
def slack_status(ack, body, say):
    """Slack /ocstatus command: show system stats."""
    ack()
    
    s = get_stats()
    lines = [
        f"*Total Tasks*: {s.get('tasks_total', 0)}",
        f"*Completed*: {s.get('tasks_done', 0)}",
        f"*Failed*: {s.get('tasks_failed', 0)}",
        f"*Decisions Logged*: {s.get('decisions', 0)}",
        f"*Deployments*: {s.get('deployments', 0)}",
    ]
    say("📊 *OpenClaw Swarm Status*\n" + "\n".join(lines))


# ── /fix command ───────────────────────────────────────────────────────

@app.command("/fix")
def slack_fix(ack, body, say):
    """Slack /fix command: diagnose and fix a problem."""
    ack()
    
    problem = body.get("text", "").strip()
    if not problem:
        say("📝 Usage: `/fix describe the problem here`")
        return

    say(f"🔧 **Diagnosing:** _{problem[:80]}_\n⏳ Running Research → Coder → QA...")
    
    # Run diagnostic pipeline
    for agent in ["research", "coder", "qa"]:
        _run_agent_sync(agent, f"Diagnose and fix: {problem}", say)

    say("✅ **Fix analysis complete.**")


# ── /github command ───────────────────────────────────────────────────

@app.command("/github")
def slack_github(ack, body, say):
    """Slack /github command: GitHub automation."""
    ack()
    
    action = body.get("text", "").strip()
    if not action:
        say("📝 Usage: `/github create PR for feature/auth` or `/github create issue: bug in login`")
        return

    say(f"🐙 **GitHub Agent running:**\n_{action[:80]}_")
    _run_agent_sync("github", action, say)


# ── /agents command ────────────────────────────────────────────────────

@app.command("/agents")
def slack_agents(ack, body, say):
    """Slack /agents command: list all agents."""
    ack()
    
    lines = [f"• *{k.upper()}* - {v[:70]}" for k, v in AGENT_PERSONAS.items()]
    say("🤖 *OpenClaw Agents:*\n" + "\n".join(lines))


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("OpenClaw Slack Bot Starting")
    print("=" * 60)
    print("[Slack] Initializing Socket Mode handler...")
    
    try:
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
        print("[Slack] ✅ Socket Mode connected and listening")
    except KeyboardInterrupt:
        print("\n[Slack] Shutting down...")
    except Exception as e:
        print(f"[Slack] ❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
