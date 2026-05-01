import os
import asyncio
import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openclaw-slack")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

ai = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

SYSTEM_PROMPT = (
      "You are OpenClaw, an AI assistant built by Devin. "
      "You live inside a Slack workspace and help with any task. "
      "Be concise, useful, and friendly."
)

app = AsyncApp(token=SLACK_BOT_TOKEN)


def chat_reply(prompt):
      if not ai:
                return "No GROQ_API_KEY configured."
            try:
                      response = ai.chat.completions.create(
                                    model=MODEL,
                                    messages=[
                                                      {"role": "system", "content": SYSTEM_PROMPT},
                                                      {"role": "user", "content": prompt},
                                    ],
                                    max_tokens=800,
                      )
                      return response.choices[0].message.content.strip()
except Exception as exc:
        log.error("Groq error: %s", exc)
        return "AI error: " + str(exc)


@app.event("app_mention")
async def handle_mention(event, say):
      text = event.get("text", "")
    parts = text.split(">", 1)
    prompt = parts[1].strip() if len(parts) > 1 else text
    if not prompt:
              await say("Hey! How can I help?")
              return
          loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, chat_reply, prompt)
    await say(reply)


@app.event("message")
async def handle_dm(event, say):
      if event.get("channel_type") != "im":
                return
            text = event.get("text", "")
    if not text:
              return
          loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, chat_reply, text)
    await say(reply)


async def main():
      handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    log.info("OpenClaw Slack bot starting via Socket Mode...")
    await handler.start_async()


if __name__ == "__main__":
      asyncio.run(main())
