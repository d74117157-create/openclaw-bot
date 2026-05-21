"""
OpenClaw - gateway/bot.py
Extended Discord bot with task management and deployment slash commands.
"""
import os, asyncio, traceback, json
import discord
from discord import app_commands
from dotenv import load_dotenv
from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS
from worker.github_agent import push_file, list_repo_files

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
BRAIN_CHANNEL = os.environ.get("BRAIN_CHANNEL", "brain")

intents = discord.Intents.default()
intents.message_content = True


class OpenClawBot(discord.Client):
        def __init__(self):
                    super().__init__(intents=intents)
                    self.tree = app_commands.CommandTree(self)

        async def setup_hook(self):
                    await self.tree.sync()
                    init_db()

        async def on_ready(self):
                    print(f"[OpenClawBot] Online as {self.user}")


bot  = OpenClawBot()
tree = bot.tree


# -- Helpers ------------------------------------------------------------------

def _embed(title: str, desc: str, color: int = 0x00bfff) -> discord.Embed:
        e = discord.Embed(title=title, description=desc, color=color)
        e.set_footer(text="OpenClaw")
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


# -- Slash Commands -----------------------------------------------------------

@tree.command(name="create-task", description="Create and assign a task to an agent")
@app_commands.describe(agent="Agent name (coder, reviewer, qa, ops, research, growth)",
                                              task="Task description")
async def cmd_create_task(interaction: discord.Interaction, agent: str, task: str):
        await interaction.response.defer()
        try:
                    result = await _run_agent(agent, task)
                    await interaction.followup.send(
                        embed=_embed(f"[{agent}] Task Complete", result[:3900])
                    )
except Exception:
        await interaction.followup.send(
                        embed=_embed("Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="swarm", description="Run full swarm on a task")
@app_commands.describe(task="Task for the swarm")
async def cmd_swarm(interaction: discord.Interaction, task: str):
        await interaction.response.defer()
        try:
                    loop    = asyncio.get_event_loop()
                    raw     = await loop.run_in_executor(None, orchestrate_task, task)
                    plan    = json.loads(raw)
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
except Exception:
        await interaction.followup.send(
                        embed=_embed("[swarm] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="deploy", description="Trigger a deployment via ops agent")
@app_commands.describe(target="What to deploy")
async def cmd_deploy(interaction: discord.Interaction, target: str = "main"):
        await interaction.response.defer()
        try:
                    result = await _run_agent("ops", f"Deploy {target} to production")
                    await interaction.followup.send(
                        embed=_embed("[deploy] Result", result[:3900], color=0xffaa00)
                    )
except Exception:
        await interaction.followup.send(
                        embed=_embed("[deploy] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="github", description="GitHub agent actions")
@app_commands.describe(action="list or push", path="File path", content="Content for push")
async def cmd_github(interaction: discord.Interaction,
                                          action: str,
                                          path: str = "",
                                          content: str = ""):
                                                  await interaction.response.defer()
                                                  try:
                                                              if action == "list":
                                                                              files = list_repo_files()
                                                                              await interaction.followup.send(
                                                                                  embed=_embed("[github] Files", "\n".join(files[:50])[:3900])
                                                                              )
elif action == "push" and path and content:
            push_file(path, content, f"Update {path} via Discord")
            await interaction.followup.se
