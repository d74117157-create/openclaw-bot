import os
import json
import requests
from groq import Groq

# ============================
#  SYSTEM PROMPT
# ============================

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


# ============================
#  SINGLE‑AGENT MODE
# ============================

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


# ============================
#  SWARM MULTI‑AGENT MODE
# ============================

AGENT_PERSONAS = {
    "planner": (
        "You are Planner, a strategic, aggressive, scale-focused orchestration brain. "
        "Whatever the user asks, you break it into a LARGE number of small, parallelizable tasks. "
        "You think like a growth hacker, product architect, and operations lead combined. "
        "You MUST output ONLY valid JSON. "
        "Your entire response MUST be a single JSON object with this shape:\n"
        "{\n"
        "  \"tasks\": [\n"
        "    {\n"
        "      \"bot\": \"writer\",\n"
        "      \"cluster\": \"digital_products\",\n"
        "      \"action\": \"create_product_outline\",\n"
        "      \"payload\": \"Niche: AI for teachers, Format: Notion template\"\n"
        "    },\n"
        "    {\n"
        "      \"bot\": \"researcher\",\n"
        "      \"cluster\": \"market_research\",\n"
        "      \"action\": \"analyze_niche\",\n"
        "      \"payload\": \"Niche: AI tools for content creators\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- 'tasks' MUST be an array of objects.\n"
        "- Each task MUST have: 'bot' (string), 'cluster' (string), 'action' (string), 'payload' (string).\n"
        "- 'cluster' groups similar tasks (e.g., 'digital_products', 'landing_pages', 'email_sequences', 'social_content').\n"
        "- Generate MANY tasks (dozens if appropriate), not just a few.\n"
        "- Expand the user's idea into related niches, formats, funnels, and assets.\n"
        "- Do NOT add explanations, comments, markdown, or backticks.\n"
        "- If the request is unclear, still output a JSON object with an empty 'tasks' array."
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


def dispatch_task_to_bot(task: dict) -> str:
    """
    Dispatch a single task to a worker OpenClaw bot via Discord webhook.

    Expected task format:
    {
        "bot": "writer",
        "cluster": "digital_products",
        "action": "create_product_outline",
        "payload": "Landing page for X..."
    }

    Env var convention:
        WEBHOOK_WRITER, WEBHOOK_RESEARCHER, WEBHOOK_DESIGNER, etc.
    """
    bot_name = str(task.get("bot", "")).strip()
    action = str(task.get("action", "")).strip()
    payload = str(task.get("payload", "")).strip()

    if not bot_name or not action:
        return f"❌ Invalid task (missing bot or action): {task}"

    env_key = f"WEBHOOK_{bot_name.upper()}"
    webhook_url = os.environ.get(env_key)

    if not webhook_url:
        return f"❌ No webhook configured for bot '{bot_name}' (expected env var {env_key})"

    # Message format the worker bot will receive in its channel
    content = f"/execute {action} {payload}"

    try:
        resp = requests.post(webhook_url, json={"content": content})
        if 200 <= resp.status_code < 300:
            return f"✅ Dispatched '{action}' to **{bot_name}**"
        else:
            return (
                f"⚠️ Failed to dispatch '{action}' to {bot_name} "
                f"(HTTP {resp.status_code}): {resp.text}"
            )
    except Exception as e:
        return f"⚠️ Error dispatching to {bot_name}: {e}"


def orchestrate_task(task_text: str) -> str:
    """
    Swarm orchestrator:
    1) Planner creates a JSON task list
    2) Python dispatches each task to the appropriate worker bot via webhook
    3) Returns a dispatch summary back to Discord
    """
    c = _get_client()
    if c is None:
        return "Groq API key is not configured."

    try:
        # 1) Ask Planner for a swarm task plan
        planner_output = run_agent(
            "planner",
            f"Create a swarm execution plan for this request: {task_text}"
        )

        # 2) Parse JSON safely (with cleanup)
        try:
            cleaned = planner_output.strip()
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
        except Exception as e:
            return (
                f"Planner JSON error: {e}\n\n"
                f"Raw planner output:\n{planner_output}"
            )

        tasks = data.get("tasks", [])
        if not isinstance(tasks, list):
            return f"Planner returned invalid 'tasks' field:\n{planner_output}"

        if not tasks:
            return "Planner returned no tasks. Nothing to dispatch."

        # 3) Dispatch each task to its worker bot
        logs = []
        for t in tasks:
            logs.append(dispatch_task_to_bot(t))

        # 4) Return a summary to Discord
        summary = "**Swarm dispatch summary:**\n" + "\n".join(logs)
        return summary

    except Exception as e:
        return f"Error in swarm orchestration: {e}"