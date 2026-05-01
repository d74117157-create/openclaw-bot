"""AI worker - standalone mode with optional OpenAI upgrade.

Works out of the box with no API key required.
Set OPENAI_API_KEY environment variable to enable full AI mode.
"""

import os
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Optional OpenAI support
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RETRIES = 3

_client = None

if OPENAI_API_KEY:
    try:
        from openai import OpenAI, APIError, APITimeoutError, RateLimitError
        _client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
        logger.info("OpenAI client initialised - full AI mode enabled.")
    except ImportError:
        logger.warning("openai package not installed. Running in standalone mode.")
    except Exception as exc:
        logger.warning("Failed to init OpenAI client: %s. Running in standalone mode.", exc)
else:
    logger.info("No OPENAI_API_KEY set - running in standalone mode.")


_BUILTIN_COMMANDS = {
    "hello": "Hey there! OpenClaw is online and ready.",
    "help": "Commands: !task <message>, !auto on/off, !status, !ping",
    "ping": "Pong! OpenClaw is alive.",
    "time": None,
    "about": "OpenClaw - your autonomous AI command center.",
}


def _standalone_response(task):
    task_lower = task.strip().lower()
    for keyword, response in _BUILTIN_COMMANDS.items():
        if keyword in task_lower:
            if keyword == "time":
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                return f"Current time: {now}"
            return response
    return (
        f"Task received and logged: {task[:100]}\n"
        f"Running in standalone mode - add OPENAI_API_KEY for full AI."
    )


def _openai_response(task):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant. Complete the user's task clearly and concisely."},
                    {"role": "user", "content": task},
                ],
                temperature=0.4,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            last_error = exc
            wait = 2 ** attempt
            logger.warning("Attempt %d/%d failed (%s). Retrying in %ds...", attempt, MAX_RETRIES, type(exc).__name__, wait)
            time.sleep(wait)
    return f"AI failed after {MAX_RETRIES} attempts. Last error: {last_error}"


def process_task(task):
    if _client is not None:
        return _openai_response(task)
    return _standalone_response(task)
