"""
OpenClaw — Self-Orchestrating Agent Swarm
/create-task → orchestrator decomposes → agents run → Slack output
"""
import os, asyncio, json
import discord
from discord import app_commands
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from memory import init_db, save_task, update_task, get_stats
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS

load_dotenv()

DISCORD_TOKEN   = os.environ.get("DISCORD_TOKEN", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL   = os.environ.get("SLACK_CHANNEL", "general")

slack = WebClient(token=SLACK_BOT_TOKEN)

# ── Slack helper ───────────────────────────────────────────
def post_slack(agent, task_desc, result):
    try:
        preview = result[:2800]
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=[
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"[{agent.upper()}] Task Complete"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Task:* {task_desc[:120]}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```{preview}```"}
                }
            ]
        )
    except SlackApiError as e:
        print(f"[Slack] {e.response['error']}")

# ── Bot setup ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

class OpenClaw(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("[OpenClaw] Slash commands synced")

    async def on_ready(self):
        init_db()
        print(f"[OpenClaw] {self.user} online")

client = OpenClaw()
tree   = client.tree

# ── Agent runner ───────────────────────────────────────────
async def run_agent(itx: discord.Interaction, agent: str, task_desc: str):
    tid = save_task(task_desc, agent)
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, lambda: process_task(task_desc, agent)
        )
        update_task(tid, result, "done")
        loop.run_in_executor(None, lambda: post_slack(agent, task_desc, result))
        preview = result[:900] + "…" if len(result) > 900 else result
        await itx.followup.send(
            f"✅ **{agent.upper()}** → Slack\n```{preview}```",
            ephemeral=False
        )
    except Exception as e:
        update_task(tid, str(e), "failed")
        await itx.followup.send(f"❌ **{agent}** failed: {e}")

# ── /create-task ───────────────────────────────────────────
@tree.command(name="create-task", description="Swarm agents auto-plan and execute your task → Slack")
@app_commands.describe(task="Describe what you want done (any complexity)")
async def create_task(itx: discord.Interaction, task: str):
    await itx.response.defer(thinking=True)

    try:
        # Orchestrator decomposes task → JSON plan
        plan_raw = await asyncio.get_event_loop().run_in_executor(
            None, lambda: orchestrate_task(task)
        )
        plan = json.loads(plan_raw)   # [{agent, task}, ...]
    except Exception as e:
        # Fallback: run orchestrator directly
        plan = [{"agent": "orchestrator", "task": task}]
        await itx.followup.send(f"⚠️ Planner error ({e}), running orchestrator direct.")

    agent_summary = ", ".join(f"**{p['agent']}**" for p in plan)
    await itx.followup.send(
        f"🧠 **Auto-plan** ({len(plan)} agents): {agent_summary}\n"
        f"📌 Task: _{task[:100]}_\n"
        f"📤 Results → Slack #{SLACK_CHANNEL}"
    )

    await asyncio.gather(*[
        run_agent(itx, step["agent"], step["task"])
        for step in plan
        if step.get("agent") in AGENT_PERSONAS
    ])

    await itx.followup.send("🏁 All agents done. Check Slack.")

# ── /swarm (manual) ────────────────────────────────────────
@tree.command(name="swarm", description="Manually pick agents: script,seo,image → Slack")
@app_commands.describe(
    agents="Comma list: script,seo,image,research,reply,orchestrator",
    task="What to do"
)
async def swarm(itx: discord.Interaction, agents: str, task: str):
    await itx.response.defer(thinking=True)
    agent_list = [a.strip() for a in agents.split(",")]
    bad = [a for a in agent_list if a not in AGENT_PERSONAS]
    if bad:
        await itx.followup.send(f"❓ Unknown: {', '.join(bad)}\nAvailable: {', '.join(AGENT_PERSONAS)}")
        return
    await itx.followup.send(f"🐝 **{len(agent_list)} agents** on: _{task[:80]}_")
    await asyncio.gather(*[run_agent(itx, a, task) for a in agent_list])
    await itx.followup.send("🏁 Swarm done → Slack")

# ── /agents ────────────────────────────────────────────────
@tree.command(name="agents", description="List all Eonix agents")
async def agents_cmd(itx: discord.Interaction):
    lines = [f"• **{k}** — {v[:65]}…" for k, v in AGENT_PERSONAS.items()]
    await itx.response.send_message("🤖 **Eonix Agents:**\n" + "\n".join(lines))

# ── /stats ─────────────────────────────────────────────────
@tree.command(name="stats", description="Task database stats")
async def stats_cmd(itx: discord.Interaction):
    s = get_stats()
    if not s:
        await itx.response.send_message("No tasks yet.")
        return
    lines = [f"**{k}**: {v}" for k, v in s.items()]
    await itx.response.send_message("📊 **Task Stats:**\n" + "\n".join(lines))

# ── run ────────────────────────────────────────────────────
client.run(DISCORD_TOKEN)