
import os
import json
import requests
from groq import Groq

============================

SYSTEM PROMPT

============================

SYSTEM_PROMPT = (
    "You are OpenClaw, a powerful AI assistant living inside Discord. "
    "You were built by Devin. You are confident, helpful, and capable. "
    "You can answer questions, write code, brainstorm ideas, tell jokes, "
    "and help with virtually anything. Keep replies concise but thorough. "
    "Use Discord-friendly formatting (markdown, code blocks, etc)."
)

client = None

def getclient():
    global client
    if client is None:
        apikey = os.environ.get("GROQAPI_KEY")
        if not api_key:
            return None
        client = Groq(apikey=apikey)
    return client


============================

SINGLE‑AGENT MODE

============================

def processtask(tasktext):
    c = getclient()
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
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=800,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {e}"


============================

SWARM MULTI‑AGENT MODE

============================

AGENT_PERSONAS = {
    "planner": """
You are Planner, the orchestration brain of the Eonix Swarm.

Your ONLY job is to convert the user's request into a JSON task list.

You MUST output ONLY valid JSON.
Your entire response MUST be a single JSON object.

The JSON MUST follow this exact schema:

{
  "tasks": [
    {
      "bot": "writer | researcher | designer | automation",
      "cluster": "string grouping similar tasks",
      "action": "string describing the action",
      "payload": "string with details"
    }
  ]
}

RULES:
- Do NOT add explanations.
- Do NOT add commentary.
- Do NOT add markdown.
- Do NOT wrap JSON in backticks.
- Do NOT output anything except the JSON object.
- If the request is unclear, output: {"tasks": []}
- Always return valid JSON.
"""
}


def run_agent(role, content):
    """Runs a single agent with a specific persona."""
    c = getclient()
    if c is None:
        return "Groq API key is not configured."

    messages = [
        {"role": "system", "content": AGENT_PERSONAS[role]},
        {"role": "user", "content": content},
    ]

    response = c.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=800,
    )

    return response.choices[0].message.content


def dispatchtaskto_bot(task: dict) -> str:
    """
    Dispatch a single task to a worker OpenClaw bot via Discord webhook.

    Expected task format:
    {
        "bot": "writer",
        "cluster": "digital_products",
        "action": "createproductoutline",
        "payload": "Landing page for X..."
    }

    Env var convention:
        WEBHOOKWRITER, WEBHOOKRESEARCHER, WEBHOOK_DESIGNER, etc.
    """
    bot_name = str(task.get("bot", "")).strip()
    action = str(task.get("action", "")).strip()
    payload = str(task.get("payload", "")).strip()

    if not bot_name or not action:
        return f"❌ Invalid task (missing bot or action): {task}"

    envkey = f"WEBHOOK{bot_name.upper()}"
    webhookurl = os.environ.get(envkey)

    if not webhook_url:
        return f"❌ No webhook configured for bot '{botname}' (expected env var {envkey})"

    # Message format the worker bot will receive in its channel
    content = f"/execute {action} {payload}"

    try:
        resp = requests.post(webhook_url, json={"content": content})
        if 200 <= resp.status_code < 300:
            return f"✅ Dispatched '{action}' to {bot_name}"
        else:
            return (
                f"⚠️ Failed to dispatch '{action}' to {bot_name} "
                f"(HTTP {resp.status_code}): {resp.text}"
            )
    except Exception as e:
        return f"⚠️ Error dispatching to {bot_name}: {e}"


============================

PLANNER JSON FIX + SAFETY

============================

def cleanandparseplannerjson(raw_output: str):
    """
    Safely parse Planner JSON.
    Fixes common issues like:
    - backticks
    - `json blocks
    - newlines
    - extra spaces
    Returns either a dict or an error object.
    """
    # 1) Try direct parse
    try:
        return json.loads(raw_output)
    except Exception:
        pass

    # 2) Clean markdown junk
    cleaned = (
        raw_output.replace("`json", "")
                  .replace("`", "")
                  .strip()
    )

    # 3) Remove weird spacing/newlines
    cleaned = " ".join(cleaned.split())

    # 4) Try again
    try:
        return json.loads(cleaned)
    except Exception as e:
        return {
            "error": f"Planner JSON parse failure: {e}",
            "rawoutput": rawoutput
        }


def normalize_tasks(data):
    """
    Ensures we ALWAYS get a list of tasks.
    If Planner fails or returns garbage, we return an empty list.
    """
    if not isinstance(data, dict):
        return []

    tasks = data.get("tasks")

    if not isinstance(tasks, list):
        return []

    return tasks


def orchestratetask(tasktext: str) -> str:
    """
    Swarm orchestrator:
    1) Planner creates a JSON task list
    2) Python dispatches each task to the appropriate worker bot via webhook
    3) Returns a dispatch summary back to Discord
    """
    c = getclient()
    if c is None:
        return "Groq API key is not configured."

    try:
        # 1) Ask Planner for a swarm task plan
        planneroutput = runagent(
            "planner",
            f"Create a swarm execution plan for this request: {task_text}"
        )

        # 2) Parse JSON safely (with cleanup and error reporting)
        data = cleanandparseplannerjson(planner_output)

        if isinstance(data, dict) and "error" in data:
            return (
                f"❌ Planner JSON error: {data['error']}\n\n"
                f"Raw planner output:\n{data['raw_output']}"
            )

        tasks = normalize_tasks(data)

        if not tasks:
            return "Planner returned no tasks. Nothing to dispatch."

        # 3) Dispatch each task to its worker bot
        logs = []
        for t in tasks:
            logs.append(dispatchtaskto_bot(t))

        # 4) Return a summary to Discord
        summary = "Swarm dispatch summary:\n" + "\n".join(logs)
        return summary

    except Exception as e:
        return f"Error in swarm orchestration: {e}"
`