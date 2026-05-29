"""
OpenClaw - worker/ai_worker.py
Groq LLM engine: 9 agent personas, task processing, orchestration.
FIXED: Complete indentation, proper function structure.
"""
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Agent personas
AGENT_PERSONAS = {
    "orchestrator": "You are the Orchestrator. Decompose tasks into subtasks and assign agents. Return JSON: [{agent, task}].",
    "coder":        "You are the Coder. Write clean, production-ready Python code. Explain briefly.",
    "reviewer":     "You are the Reviewer. Review code for bugs, style, security. Give actionable feedback.",
    "qa":           "You are the QA Engineer. Write pytest tests, find edge cases, validate logic.",
    "ops":          "You are the Ops Engineer. Handle deployment, Docker, Railway, CI/CD, env vars.",
    "research":     "You are the Researcher. Find facts, summarize docs, explain concepts clearly.",
    "growth":       "You are the Growth Hacker. Suggest marketing, user acquisition, and engagement ideas.",
    "memory":       "You are the Memory Agent. Summarize and store key decisions and task outcomes.",
    "github":       "You are the GitHub Agent. Handle PRs, commits, issues, and repo management.",
}

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

client = None


def _get_client() -> Groq:
    """Get or create Groq client."""
    global client
    if client is None:
        if not GROQ_API_KEY:
            raise ValueError("❌ GROQ_API_KEY not set in .env")
        client = Groq(api_key=GROQ_API_KEY)
    return client


def _chat(system: str, user: str, max_tokens: int = 2048) -> str:
    """Send a chat completion request to Groq."""
    c = _get_client()
    resp = c.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def process_task(task: str, agent: str = "orchestrator") -> str:
    """Process a task with a specific agent persona."""
    system = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["orchestrator"])
    return _chat(system, task)


def orchestrate_task(task: str) -> str:
    """Use orchestrator to decompose a task into a JSON plan."""
    system = AGENT_PERSONAS["orchestrator"]
    prompt = (
        f"Decompose this task into subtasks for specialist agents.\n"
        f"Return ONLY valid JSON array: [{{\"agent\": \"name\", \"task\": \"description\"}}]\n"
        f"Available agents: {', '.join(AGENT_PERSONAS.keys())}\n"
        f"Task: {task}"
    )
    result = _chat(system, prompt, max_tokens=1024)
    
    # Strip markdown code fences if present
    result = result.strip()
    if result.startswith("```"):
        lines = result.split("```")
        if len(lines) >= 2:
            result = lines[1]
            if result.startswith("json"):
                result = result[4:].lstrip()
        result = result.rstrip()
    
    return result


def multi_agent_pipeline(task: str) -> dict:
    """Run orchestrator then execute each subtask with the assigned agent."""
    try:
        plan_raw = orchestrate_task(task)
        plan = json.loads(plan_raw)
    except Exception as e:
        print(f"[orchestrate] Fallback: {e}")
        plan = [{"agent": "orchestrator", "task": task}]

    results = {}
    for step in plan:
        agent = step.get("agent", "orchestrator")
        subtask = step.get("task", task)
        if agent in AGENT_PERSONAS:
            results[agent] = process_task(subtask, agent)
    
    return results
