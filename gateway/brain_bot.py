"""
OpenClaw - gateway/brain_bot.py
Discord gateway: listens in #brain channel, runs agent swarm via slash commands.
"""
import os, asyncio, traceback, json
import discord
from discord import app_commands
from dotenv import load_dotenv
from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS

load_dotenv()

DISCORD_TOKEN  = os.environ["DISCORD_TOKEN"]
BRAIN_CHANNEL  = os.environ.get("BRAIN_CHANNEL", "brain")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree   = app_commands.CommandTree(client)


# -- Helpers ------------------------------------------------------------------

def _embed(title: str, description: str, color: int = 0x00bfff) -> discord.Embed:
        e = discord.Embed(title=title, description=description, color=color)
        e.set_footer(text="OpenClaw Brain")
        return e


async def _run_agent(agent: str, task_desc: str) -> str:
        loop = asyncio.get_event_loop()
        tid  = save_task(task_desc, agent)
        try:
                    result = await loop.run_in_executor(None, process_task, task_desc, agent)
                    update_task(tid, result, "done")
                    return result
except Exception as exc:
        update_task(tid, str(exc), "failed")
        raise


async def _orchestrate(task_desc: str) -> list:
        loop = asyncio.get_event_loop()
        raw  = await loop.run_in_executor(None, orchestrate_task, task_desc)
        try:
                    return json.loads(raw)
except Exception:
        return [{"agent": "orchestrator", "task": task_desc}]


# -- Events -------------------------------------------------------------------

@client.event
async def on_ready():
        await tree.sync()
        init_db()
        print(f"[BrainBot] Online as {client.user}")


@client.event
async def on_message(message: discord.Message):
        if message.author.bot:
                    return
                if message.channel.name != BRAIN_CHANNEL:
                            return
                        if message.content.startswith("/"):
                                    return

    task = message.content.strip()
    if not task:
                return

    thinking = await message.channel.send(
                embed=_embed("[orch] Thinking...", f"Task: {task[:200]}")
    )

    try:
                plan = await _orchestrate(task)
                results = []
                for step in plan:
                                agent = step.get("agent", "orchestrator")
                                sub   = step.get("task", task)
                                out   = await _run_agent(agent, sub)
                                results.append(f"**[{agent}]**: {out[:400]}")

                combined = "\n\n".join(results) or "No output."
                await thinking.edit(
                    embed=_embed("[orch] Done", combined[:3900], color=0x00ff88)
                )
except Exception as exc:
        tb = traceback.format_exc()[-800:]
        await thinking.edit(
                        embed=_embed("[orch] Error", f"```{tb}```", color=0xff4444)
        )


# -- Slash Commands -----------------------------------------------------------

@tree.command(name="brain", description="Send a task to the OpenClaw brain")
@app_commands.describe(task="What should the swarm do?")
async def cmd_brain(interaction: discord.Interaction, task: str):
        await interaction.response.defer()
    try:
                result = await _run_agent("orchestrator", task)
                await interaction.followup.send(
                    embed=_embed("[brain] Result", result[:3900])
                )
except Exception as exc:
        await interaction.followup.send(
                        embed=_embed("[brain] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="status", description="OpenClaw system status")
async def cmd_status(interaction: discord.Interaction):
        await interaction.response.defer()
        stats = get_stats()
        lines = [
            f"Tasks total  : {stats.get('total', 0)}",
            f"Done         : {stats.get('done', 0)}",
            f"Failed       : {stats.get('failed', 0)}",
            f"Agents       : {len(AGENT_PERSONAS)}",
            f"Model        : {os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant')}",
        ]
        await interaction.followup.send(
            embed=_embed("[status] OpenClaw", "\n".join(lines))
        )


@tree.command(name="agents", description="List all agent personas")
async def cmd_agents(interaction: discord.Interaction):
        await interaction.response.defer()
        lines = [f"**{k}**: {v['role']}" for k, v in AGENT_PERSONAS.items()]
        await interaction.followup.send(
            embed=_embed("[agents] Swarm Roster", "\n".join(lines))
        )


@tree.command(name="swarm", description="Run a multi-agent swarm on a task")
@app_commands.describe(task="Task for the full swarm")
async def cmd_swarm(interaction: discord.Interaction, task: str):
        await interaction.response.defer()
        try:
                    plan    = await _orchestrate(task)
                    results = []
                    for step in plan:
                                    agent = step.get("agent", "orchestrator")
                                    sub   = step.get("task", task)
                                    out   = await _run_agent(agent, sub)
                                    results.append(f"**[{agent}]**: {out[:300]}")
                                combined = "\n\n".join(results) or "No output."
                    await interaction.followup.send(
                        embed=_embed("[swarm] Done", combined[:3900], color=0x00ff88)
                    )
except Exception as exc:
        await interaction.followup.send(
                        embed=_embed("[swarm] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


# -- Entry --------------------------------------------------------------------

if __name__ == "__main__":
        client.run(DISCORD_TOKEN)
    
