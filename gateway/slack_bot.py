"""
OpenClaw - gateway/slack_bot.py
Slack gateway: listens for @mentions + slash commands, routes to agent swarm.
"""
import os, json, threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS

load_dotenv()

SLACK_BOT_TOKEN   = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN   = os.environ["SLACK_APP_TOKEN"]   # xapp-... (Socket Mode)
SLACK_CHANNEL     = os.environ.get("SLACK_CHANNEL", "openclaw-ops")

app = App(token=SLACK_BOT_TOKEN)


# -- Helpers ------------------------------------------------------------------
def _run_agent_sync(agent: str, task_desc: str, say, thread_ts=None) -> str:
        tid = save_task(task_desc, agent)
        try:
                    result = process_task(task_desc, agent)
                    update_task(tid, result, "done")
                    preview = result[:2800]
                    say(
                        blocks=[
                            {"type": "header",
                             "text": {"type": "plain_text", "text": f"[{agent.upper()}] Done"}},
                            {"type": "section",
                             "text": {"type": "mrkdwn", "text": f"*Task:* {task_desc[:100]}"}},
                            {"type": "section",
                             "text": {"type": "mrkdwn", "text": f"```{preview}```"}},
                        ],
                        thread_ts=thread_ts
                    )
                    return result
except Exception as e:
        update_task(tid, str(e), "failed")
        say(f"[{agent.upper()}] failed: {e}", thread_ts=thread_ts)
        return ""


def _quick_reply(say, message: str, thread_ts=None):
        say(text=message, thread_ts=thread_ts)


# -- @mention handler ---------------------------------------------------------
@app.event("app_mention")
def handle_mention(event, say):
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event.get("ts")
        task = " ".join(w for w in text.split() if not w.startswith(">@")).strip()

    if not task:
                say("MAIN BRAIN ready. Tell me what to do.", thread_ts=thread_ts)
                return

    say(f"MAIN BRAIN received: {task[:100]}\nOrchestrating swarm...", thread_ts=thread_ts)

    try:
                plan_raw = orchestrate_task(task)
                plan = json.loads(plan_raw)
except Exception as e:
            plan = [{"agent": "orchestrator", "task": task}]
            say(f"Planner fallback: {e}", thread_ts=thread_ts)

    agent_names = " -> ".join(f"`{p['agent']}`" for p in plan if p.get("agent") in AGENT_PERSONAS)
    say(f"Plan: {agent_names}", thread_ts=thread_ts)
    save_decision(task, f"Slack plan: {agent_names}")

    threads = []
    for step in plan:
                if step.get("agent") in AGENT_PERSONAS:
                                t = threading.Thread(
                                                    target=_run_agent_sync,
                                                    args=(step["agent"], step["task"], say, thread_ts)
                                )
                                t.start()
                                threads.append(t)
                        for t in threads:
                                    t.join()

    say("All agents complete.", thread_ts=thread_ts)


# -- /swarm -------------------------------------------------------------------
@app.command("/swarm")
def slack_swarm(ack, body, say):
        ack()
    text = body.get("text", "").strip()
    if not text or " " not in text:
                say("Usage: `/swarm coder,ops >task description>`")
        return
    parts     = text.split(" ", 1)
    agents    = [a.strip() for a in parts[0].split(",")]
    task_desc = parts[1]
    bad = [a for a in agents if a not in AGENT_PERSONAS]
    if bad:
                say(f"Unknown: `{', '.join(bad)}` | Available: `{', '.join(AGENT_PERSONAS)}`")
        return
    say(f"Swarm: `{', '.join(agents)}` -> _{task_desc[:80]}_")
    threads = []
    for agent in agents:
                t = threading.Thread(target=_run_agent_sync, args=(agent, task_desc, say))
        t.start()
        threads.append(t)
    for t in threads:
                t.join()
    say("Swarm done.")


# -- /deploy ------------------------------------------------------------------
@app.command("/deploy")
def slack_deploy(ack, body, say):
        ack()
    service = body.get("text", "").strip() or "openclaw-bot"
    say(f"Deploying `{service}`... OPS agent running.")
    task_desc = f"Create Railway deployment plan for {service}: Dockerfile, env vars, health check, rollback."
    _run_agent_sync("ops", task_desc, say)


# -- /ocstatus ----------------------------------------------------------------
@app.command("/ocstatus")
def slack_status(ack, body, say):
        ack()
    s = get_stats()
    lines = [f"*{k}*: {v}" for k, v in s.items()]
    say("*OpenClaw Swarm Status*\n" + "\n".join(lines))


# -- /fix ---------------------------------------------------------------------
@app.command("/fix")
def slack_fix(ack, body, say):
        ack()
    problem = body.get("text", "").strip()
    if not problem:
                say("Usage: `/fix >describe the problem>`")
        return
    say(f"Diagnosing: _{problem[:80]}_")
    for agent in ["research", "coder", "qa"]:
                _run_agent_sync(agent, f"Diagnose and fix: {problem}", say)
    say("Fix analysis complete.")


# -- /github ------------------------------------------------------------------
@app.command("/github")
def slack_github(ack, body, say):
        ack()
    action = body.get("text", "").strip()
    if not action:
                say("Usage: `/github >action>` e.g. `/github create PR for feature/auth`")
        return
    say(f"GITHUB AGENT running: _{action[:80]}_")
    _run_agent_sync("github", action, say)


# -- /agents ------------------------------------------------------------------
@app.command("/agents")
def slack_agents(ack, body, say):
        ack()
    lines = [f"- *{k.upper()}* - {v[:80]}" for k, v in AGENT_PERSONAS.items()]
    say("*OpenClaw Agents:*\n" + "\n".join(lines))


# -- Main ---------------------------------------------------------------------
if __name__ == "__main__":
        init_db()
    print("[OpenClaw Slack] Starting Socket Mode handler...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
