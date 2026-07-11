"""OpenClaw Discord MAIN BRAIN — slash commands + swarm orchestration."""
import os
import asyncio
import json
import traceback
import logging
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

from memory import init_db, save_task, update_task, get_stats
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS
from worker.task_router import TaskRouter
from worker.executor import ExecutorEngine
from worker.slack_reporter import task_started, agent_complete, task_complete, error_alert
from worker.self_test import run_self_test
from health import update_state

load_dotenv()
logger = logging.getLogger("openclaw.discord")

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
BRAIN_CHANNEL = os.environ.get("BRAIN_CHANNEL", "brain")

intents = discord.Intents.default()
intents.message_content = True


class OpenClawBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.executor = ExecutorEngine()
        self.router = TaskRouter()

    async def setup_hook(self):
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=int(DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Slash commands synced to guild {DISCORD_GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally")
        init_db()

    async def on_ready(self):
        logger.info(f"[Discord] Online as {self.user}")
        update_state("discord", "connected")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        if message.channel.name != BRAIN_CHANNEL:
            return
        content = message.content.strip()
        if not content.startswith("!"):
            return
        tid = save_task(content, "brain")
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, process_task, content, "orchestrator")
            update_task(tid, result, "done")
            await message.channel.send(f"**[Brain]** {result[:1900]}")
        except Exception as exc:
            update_task(tid, str(exc), "failed")
            await message.channel.send(f"**[Brain Error]** {exc}")


def _embed(title: str, desc: str, color: int = 0x00bfff) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text="OpenClaw Superswarm")
    return e


async def _run_agent(bot: OpenClawBot, agent: str, task_desc: str) -> str:
    loop = asyncio.get_event_loop()
    tid = save_task(task_desc, agent)
    try:
        result = await loop.run_in_executor(None, process_task, task_desc, agent)
        update_task(tid, result, "done")
        agent_complete(agent, task_desc, result, success=True)
        return result
    except Exception as exc:
        update_task(tid, str(exc), "failed")
        agent_complete(agent, task_desc, str(exc), success=False)
        raise


bot = OpenClawBot()
tree = bot.tree


@tree.command(name="create-task", description="Auto-plan and execute with full swarm")
@app_commands.describe(agent="Agent name (coder, reviewer, qa, ops, research, growth, github)", task="Task description")
async def cmd_create_task(interaction: discord.Interaction, agent: str, task: str):
    await interaction.response.defer()
    try:
        result = await _run_agent(bot, agent, task)
        await interaction.followup.send(embed=_embed(f"[{agent}] Task Complete", result[:3900]))
    except Exception:
        await interaction.followup.send(embed=_embed("Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444))


@tree.command(name="swarm", description="Run full swarm on a task")
@app_commands.describe(task="Task for the swarm")
async def cmd_swarm(interaction: discord.Interaction, task: str):
    await interaction.response.defer()
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, orchestrate_task, task)
        plan = json.loads(raw)
        results = []
        task_started(task, plan)
        for step in plan:
            agent = step.get("agent", "orchestrator")
            sub = step.get("task", task)
            out = await _run_agent(bot, agent, sub)
            results.append(f"**[{agent}]**: {out[:300]}")
        combined = "\n\n".join(results) or "No output."
        qa = run_self_test(task, {step.get("agent", "orchestrator"): r for step, r in zip(plan, results)})
        task_complete(task, qa)
        await interaction.followup.send(embed=_embed("[swarm] Done", combined[:3900], color=0x00ff88))
    except Exception:
        error_alert("swarm", traceback.format_exc()[-500:])
        await interaction.followup.send(embed=_embed("[swarm] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444))


@tree.command(name="deploy", description="Trigger deployment via ops agent")
@app_commands.describe(target="What to deploy")
async def cmd_deploy(interaction: discord.Interaction, target: str = "main"):
    await interaction.response.defer()
    try:
        result = await _run_agent(bot, "ops", f"Deploy {target} to production")
        await interaction.followup.send(embed=_embed("[deploy] Result", result[:3900], color=0xffaa00))
    except Exception:
        await interaction.followup.send(embed=_embed("[deploy] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444))


@tree.command(name="github", description="GitHub agent actions")
@app_commands.describe(action="list, push, branch, issue, pr", path="File path", content="Content for push")
async def cmd_github(interaction: discord.Interaction, action: str, path: str = "", content: str = ""):
    await interaction.response.defer()
    try:
        from worker.github_agent import GitHubAgent
        agent = GitHubAgent()
        if action == "summary":
            result = agent.repo_summary()
        elif action == "branch":
            result = agent.new_feature_branch(path or "auto-feature")
        elif action == "issue":
            result = agent.open_issue(path or "Auto issue", content or "Created by OpenClaw")
        elif action == "pr":
            result = agent.open_pr(path or "Auto PR", content or "", "feature/auto")
        else:
            result = agent.execute(f"{action} {path} {content}")
        await interaction.followup.send(embed=_embed("[github] Result", result[:3900]))
    except Exception:
        await interaction.followup.send(embed=_embed("[github] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444))


@tree.command(name="agents", description="List available agents")
async def cmd_agents(interaction: discord.Interaction):
    lines = [f"**{k}** — {v[:90]}..." for k, v in AGENT_PERSONAS.items()]
    await interaction.response.send_message(embed=_embed("Available Agents", "\n".join(lines)))


@tree.command(name="status", description="Show bot status and recent tasks")
async def cmd_status(interaction: discord.Interaction):
    stats = get_stats()
    embed = _embed("OpenClaw Status", f"Tasks: **{stats['total']}** | Done: **{stats['done']}** | Failed: **{stats['failed']}**")
    await interaction.response.send_message(embed=embed)


@tree.command(name="route", description="AI route a task and show the plan")
@app_commands.describe(task="Task to route")
async def cmd_route(interaction: discord.Interaction, task: str):
    await interaction.response.defer()
    route = bot.router.route(task)
    desc = bot.router.describe(route)
    await interaction.followup.send(embed=_embed("Route Plan", desc, color=0xaa88ff))


def run_discord():
    if not DISCORD_TOKEN:
        logger.warning("DISCORD_TOKEN not set — Discord bot disabled")
        update_state("discord", "disabled")
        return
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Discord bot crashed: {e}")
        update_state("discord", f"error: {e}")
