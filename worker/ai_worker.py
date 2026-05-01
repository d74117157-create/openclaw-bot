import os
from openai import OpenAI

client = None

def _get_client():
    global client
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        client = OpenAI(api_key=api_key)
    return client

SYSTEM_PROMPT = (
    "You are OpenClaw, a powerful AI assistant living inside Discord. "
    "You were built by Devin. You are confident, helpful, and capable. "
    "You can answer questions, write code, brainstorm ideas, tell jokes, "
    "and help with virtually anything. Keep replies concise but thorough. "
    "Use Discord-friendly formatting (markdown, code blocks, etc)."
)

def chat_reply(history):
    c = _get_client()
    if c is None:
        return "OpenAI API key is not configured."
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        response = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def process_task(task_text):
    c = _get_client()
    if c is None:
        return "OpenAI API key is not configured."
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + " The user has given you a task. Complete it thoroughly."},
            {"role": "user", "content": task_text},
        ]
        response = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"
