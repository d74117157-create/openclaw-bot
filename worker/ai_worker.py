import os
import json
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
#  MULTI‑AGENT MODE
# ============================

AGENT_PERSONAS = {
    "planner": (
        "You are Planner, a strategic reasoning agent. "
        "You MUST output ONLY valid JSON. "
        "Your entire response MUST be a single JSON object. "
        "Format EXACTLY like this: {\"plan\": [\"step 1\", \"step 2\", \"step 3\"]}. "
        "Do NOT add explanations, comments, markdown, apologies, or extra text. "
        "Do NOT wrap the JSON in backticks. "
        "If the user request is unclear, still output a JSON object with a 'plan' array."
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
        # -------------------------
        # 1. PLANNER CREATES JSON
        # -------------------------
        planner_output = run_agent(
            "planner",
            f"Create a plan for this task: {task_text}"
        )

        # -------------------------
        # 2. PARSE JSON SAFELY
        # -------------------------
        try:
            data = json.loads(planner_output)
        except Exception:
            # Attempt auto‑repair
            try:
                cleaned = planner_output.strip()
                cleaned = cleaned.replace("```json", "").replace("```", "")
                cleaned = cleaned.replace("\n", " ").strip()
                data = json.loads(cleaned)
            except Exception as e:
                return (
                    f"Planner error while parsing JSON: {e}\n\n"
                    f"Raw planner output:\n{planner_output}"
                )

        steps = data.get("plan", [])

        # -------------------------
        # 3. FALLBACK PLAN
        # -------------------------
        if not isinstance(steps, list) or len(steps) == 0:
            steps = [
                "Interpret the user's request",
                "Break it into actionable tasks",
                "Produce the final result"
            ]

        # -------------------------
        # 4. WORKER EXECUTES PLAN
        # -------------------------
        worker_prompt = "Execute this plan step by step:\n\n" + "\n".join(steps)
        result = run_agent("worker", worker_prompt)

        return result

    except Exception as e:
        return f"Error in orchestration: {e}"