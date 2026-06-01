# =============================================================
# OPENCLAW AI WORKER  Powered by Claude claude-3-5-sonnet
# =============================================================
import os
import anthropic

AGENT_PERSONAS = {
            "orchestrator": "You are the Orchestrator. Decompose tasks into subtasks and assign agents. Return JSON: [{agent, task}].",
            "coder": "You are the Coder. Write clean, production-ready Python code. Explain briefly.",
            "reviewer": "You are the Reviewer. Review code for bugs, style, security. Give actionable feedback.",
            "qa": "You are the QA Engineer. Write pytest tests, find edge cases, validate logic.",
            "ops": "You are the Ops Engineer. Handle deployment, Docker, Render, CI/CD, env vars.",
            "research": "You are the Researcher. Find facts, summarize docs, explain concepts clearly.",
            "growth": "You are the Growth Hacker. Suggest marketing, user acquisition, and engagement ideas.",
            "memory": "You are the Memory Agent. Summarize and store key decisions and task outcomes.",
            "github": "You are the GitHub Agent. Handle PRs, commits, issues, and repo management.",
}

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

_client = None


def _get_client():
            """Get or create Anthropic client."""
            global _client
            if _client is None:
                            if not ANTHROPIC_API_KEY:
                                                raise ValueError("ANTHROPIC_API_KEY not set")
                                            _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                        return _client


def _chat(system, user, max_tokens=2048):
            """Send a chat completion request to Claude."""
    c = _get_client()
    resp = c.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def process_task(task, agent="orchestrator"):
            """Process a task with a specific agent persona."""
    system = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["orchestrator"])
    return _chat(system, task)


def orchestrate_task(task):
            """Orchestrate a complex task across multiple agents."""
    plan_json = process_task(task, "orchestrator")
    return plan_json


def multi_agent_pipeline(task):
            """Run task through full multi-agent pipeline."""
    results = {}
    results["plan"] = process_task(task, "orchestrator")
    results["code"] = process_task(task, "coder")
    results["review"] = process_task(results["code"], "reviewer")
    results["tests"] = process_task(results["code"], "qa")
    return results
