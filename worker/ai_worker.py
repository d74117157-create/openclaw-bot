import os, anthropic

PERSONAS = {
    "orchestrator": "You are the Orchestrator. Break complex tasks into subtasks and coordinate agents.",
    "coder": "You are the Coder. Write clean production-ready Python. Be concise.",
    "reviewer": "You are the Reviewer. Audit code for security, performance, and best practices.",
    "qa": "You are the QA Agent. Write comprehensive test plans and edge cases.",
    "researcher": "You are the Researcher. Deep dive into topics and provide context.",
    "ops": "You are the Ops Agent. Plan infrastructure, deployments, and monitoring.",
    "growth": "You are the Growth Agent. Plan marketing and scaling strategies.",
    "memory_agent": "You are the Memory Agent. Maintain context and recall important decisions.",
}

MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

_C = [None]

def get_client():
    _C[0] = _C[0] or anthropic.Anthropic(api_key=API_KEY)
    return _C[0]

def chat(system: str, user: str, max_tokens: int = 2048) -> str:
    """Chat with Claude using the given system prompt and user message."""
    try:
        r = get_client().messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return r.content[0].text
    except Exception as e:
        return f"[ERROR] {str(e)}"

def _chat(system: str, user: str, max_tokens: int = 2048) -> str:
    """Alias for chat()"""
    return chat(system, user, max_tokens)

def process_task(task: str, agent: str = "orchestrator") -> str:
    """Process a task using a specific agent persona."""
    persona = PERSONAS.get(agent, PERSONAS["orchestrator"])
    return chat(persona, task)

def orchestrate_task(task: str) -> str:
    """Use the orchestrator to decompose and coordinate a task."""
    return process_task(task, "orchestrator")

def multi_agent_pipeline(task: str) -> dict:
    """Run a full multi-agent pipeline: orchestrate → code → review → test."""
    plan = process_task(task, "orchestrator")
    code = process_task(task, "coder")
    review = process_task(code, "reviewer")
    tests = process_task(code, "qa")
    return {
        "plan": plan,
        "code": code,
        "review": review,
        "tests": tests,
    }

def agent_personas() -> dict:
    """Return all available agent personas."""
    return PERSONAS

AGENT_PERSONAS = PERSONAS
