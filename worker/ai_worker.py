import os
from groq import Groq

# System prompt for your assistant
SYSTEM_PROMPT = (
    "You are OpenClaw, a powerful AI assistant living inside Discord. "
    "You were built by Devin. You are confident, helpful, and capable. "
    "You can answer questions, write code, brainstorm ideas, tell jokes, "
    "and help with virtually anything. Keep replies concise but thorough. "
    "Use Discord-friendly formatting (markdown, code blocks, etc)."
)

client = None

def _get_client():
    global client
    if client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        client = Groq(api_key=api_key)
    return client


def process_task(task_text):
    c = _get_client()
    if c is None:
        return "Groq API key is not configured."

    try:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT +
                " The user has given you a task. Complete it thoroughly."
            },
            {"role": "user", "content": task_text},
        ]

        response = c.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=800,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {e}"
# -----------------------------
# MULTI‑AGENT ORCHESTRATION
# -----------------------------

# Define your agent personas
AGENT_PERSONAS = {
    "planner": (
        "You are Planner, a strategic reasoning agent. "
        "Your job is to break the user's request into clear steps, "
        "identify what needs to be done, and delegate tasks to the Worker agent."
    ),
    "worker": (
        "You are Worker, a hands‑on execution agent. "
        "You complete tasks exactly as requested by Planner, "
        "producing final outputs, code, writing, or analysis."
    ),
}

def run_agent(role, content):
    """Runs a single agent with a specific persona."""
    c = _get_client()
    if c is None:
        return "Groq API key is not configured."

    messages = [
        {"role": "system", "content": AGENT_PERSONAS[role]},
        {"role": "user", "content": content},
    ]

    response = c.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        max_tokens=800,
    )

    return response.choices[0].message.content


def orchestrate_task(task_text):
    """Planner → Worker → Final Output"""
    try:
        # Step 1: Planner breaks down the task
        plan = run_agent("planner", f"Create a plan for this task: {task_text}")

        # Step 2: Worker executes the plan
        result = run_agent("worker", f"Execute this plan:\n\n{plan}")

        # Step 3: Return final result
        return result

    except Exception as e:
        return f"Error in orchestration: {e}"