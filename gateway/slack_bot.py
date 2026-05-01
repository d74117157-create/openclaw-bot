import os, asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from groq import Groq
app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN", ""))
ai = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
M = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
def reply(t):
    r = ai.chat.completions.create(model=M, messages=[{"role": "system", "content": "You are OpenClaw, a helpful AI."}, {"role": "user", "content": t}], max_tokens=800)
    return r.choices[0].message.content
@app.event("app_mention")
async def h1(event, say):
    t = event.get("text", "").split(">", 1)[-1].strip() or "hi"
    await say(await asyncio.get_event_loop().run_in_executor(None, reply, t))
@app.event("message")
async def h2(event, say):
    if event.get("channel_type") == "im" and event.get("text") and not event.get("bot_id"):
        await say(await asyncio.get_event_loop().run_in_executor(None, reply, event["text"]))
async def start_slack_bot():
    await AsyncSocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN", "")).start_async()
if __name__ == "__main__":
    asyncio.run(start_slack_bot())
