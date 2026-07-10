"""
OpenClaw — worker/agents/memory_agent.py
MEMORY AGENT: Tracks architecture, deployments, failures, optimization history.
"""
import json
from worker.ai_worker import process_task, _chat
from memory import (
    save_decision, search_decisions, get_recent_tasks,
    get_failed_tasks, get_stats, save_deployment
)

SYSTEM = (
    "You are the MEMORY AGENT of OpenClaw. You maintain the swarm's institutional knowledge. "
    "You track architecture decisions, deployment history, known failures, and optimization wins. "
    "Rules: never repeat failed solutions. Detect patterns in failures. "
    "Always return:\n"
    "MEMORY ENTRY: <what is being stored>\n"
    "RELATED HISTORY: <similar past decisions>\n"
    "LESSONS LEARNED: <what the swarm should remember>\n"
    "RECOMMENDATIONS: <based on history, what to avoid or do>"
)


def log_decision(context: str, decision: str, outcome: str = "", tags: list = None) -> str:
    """Store a swarm decision in persistent memory."""
    save_decision(context, decision, outcome, tags or [])
    summary = _chat(
        SYSTEM,
        f"Summarize and analyze this decision for the swarm memory:\n"
        f"Context: {context}\nDecision: {decision}\nOutcome: {outcome}"
    )
    return f"\u2705 Memory stored.\n\n{summary}"


def recall(query: str) -> str:
    """Search memory for relevant past decisions."""
    results = search_decisions(query)
    if not results:
        return f"No memory entries found for: `{query}`"
    lines = [
        f"\u2022 [{r['created'][:10]}] **{r['context'][:60]}** \u2192 {r['decision'][:80]}"
        for r in results[:10]
    ]
    ai_analysis = _chat(
        SYSTEM,
        f"Analyze these memory entries for query '{query}':\n{json.dumps(results[:5], indent=2)}"
    )
    return f"**Memory Recall: `{query}`**\n\n" + "\n".join(lines) + f"\n\n**AI Analysis:**\n{ai_analysis}"


def failure_analysis() -> str:
    """Analyze all failed tasks and extract patterns."""
    failures = get_failed_tasks()
    if not failures:
        return "\u2705 No failed tasks in memory."
    failure_summary = json.dumps(failures[:10], indent=2)
    return _chat(
        SYSTEM,
        f"Analyze these swarm failures and identify patterns to avoid:\n{failure_summary}"
    )


def swarm_report() -> str:
    """Generate a full swarm health + memory report."""
    stats = get_stats()
    recent = get_recent_tasks(10)
    failures = get_failed_tasks()
    report_data = {
        "stats": stats,
        "recent_tasks": recent[:5],
        "failures": failures[:3],
    }
    return _chat(
        SYSTEM,
        f"Generate a comprehensive swarm health report from this data:\n{json.dumps(report_data, indent=2)}"
    )


def log_deployment(service: str, version: str, env: str, notes: str = "") -> str:
    """Record a deployment in memory."""
    save_deployment(service, version, env, notes)
    return f"\u2705 Deployment logged: `{service}` v{version} \u2192 {env}"


def run(task: str) -> str:
    return process_task(task, "memory")
