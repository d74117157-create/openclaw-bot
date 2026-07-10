"""
OpenClaw - gateway/slack_bot.py
Slack Socket Mode gateway for OpenClaw.
"""
import os
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv
from memory import init_db, save_task, update_task
from worker.ai_worker import process_task

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_CHANNEL   = os.environ.get("SLACK_CHANNEL", "ops")

app = AsyncApp(token=SLACK_BOT_TOKEN)


@app.event("app_mention")
async def handle_mention(event, say):
    text = event.get("text", "")
    user = event.get("user", "unknown")
    tid  = save_task(text, "slack")

    try:
        result = process_task(text, "orchestrator")
        update_task(tid, result, "done")
        await say(f"<@{user}> {result[:1900]}")
    except Exception as exc:
        update_task(tid, str(exc), "failed")
        await say(f"<@{user}> Error: {exc}")


@app.message(".*")
async def handle_message(message, say):
    channel = message.get("channel")
    if channel != SLACK_CHANNEL:
        return

    text = message.get("text", "")
    user = message.get("user", "unknown")
    tid  = save_task(text, "slack")

    try:
        result = process_task(text, "orchestrator")
        update_task(tid, result, "done")
        await say(f"<@{user}> {result[:1900]}")
    except Exception as exc:
        update_task(tid, str(exc), "failed")
        await say(f"<@{user}> Error: {exc}")


async def main():
    init_db()
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
