"""
OpenClaw - gateway/brain_bot.py
Discord gateway: listens in #brain channel, runs agent swarm via slash commands.
REPAIRED: Fixed indentation, async safety, logging, command defer.
FIXED: process_task_async / orchestrate_task_async → sync wrappers with asyncio
FIXED: Import-time crash - DISCORD_TOKEN check moved to runtime
"""
import os
import asyncio
import traceback
import json
import logging

import discord
from discord import app_commands
from dotenv import load_dotenv

from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS
from shared.logging import setup_logging, get_logger

load_dotenv()
setup_logging("brain_bot")
logger = get_logger(__name__)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
BRAIN_CHANNEL = os.environ.get("BRAIN_CHANNEL", "brain")

if not DISCORD_TOKEN:
    logger.warning("DISCORD_TOKEN not set - brain_bot will not start")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def _embed(title: str, description: str, color: int = 0x00bfff) -> discord.Embed:
    """Create an embed."""
    e = discord.Embed(title=title, description=description, color=color)
    e.set_footer(text="OpenClaw Brain")
    return e

async def _run_agent(agent: str, task_desc: str) -> str:
    """Run an agent on a task with timeout protection."""
    tid = save_task(task_desc, agent)
    try:
        # Run sync process_task in executor to avoid blocking
        loop = asyncio.get_running_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, process_task, task_desc, agent),
            timeout=25.0
        )
        update_task(tid, result, "done")
        logger.info(f"✓ Agent {agent} completed task {tid}")
        return result
    except asyncio.TimeoutError:
        error = f"Agent {agent} timeout after 25s"
        update_task(tid, error, "failed")
        logger.error(f"❌ {error}")
        raise
    except Exception as exc:
        error = str(exc)
        update_task(tid, error, "failed")
        logger.error(f"❌ Agent {agent} failed: {exc}")
        raise

async def _orchestrate(task_desc: str) -> list:
    """Orchestrate a task into subtasks."""
    try:
        loop = asyncio.get_running_loop()
        raw = await asyncio.wait_for(
            loop.run_in_executor(None, orchestrate_task, task_desc),
            timeout=10.0
        )
        plan = json.loads(raw)
        logger.info(f"✓ Orchestrated into {len(plan)} subtasks")
        return plan
    except Exception as e:
        logger.warning(f"Orchestration failed: {e}, using fallback")
        return [{"agent": "orchestrator", "task": task_desc}]

# -- Events -------------------------------------------------------------------

@client.event
async def on_ready():
    """Called when bot is ready."""
    try:
        await tree.sync()
        logger.info(f"✓ Commands synced")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

    try:
        init_db()
        logger.info(f"✓ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")

    logger.info(f"✓ BrainBot online as {client.user}")

@client.event
async def on_message(message: discord.Message):
    """Handle regular messages in brain channel."""
    try:
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
                sub = step.get("task", task)
                try:
                    out = await _run_agent(agent, sub)
                    results.append(f"**[{agent}]**: {out[:400]}")
                except Exception as e:
                    results.append(f"**[{agent}]**: ❌ {str(e)[:200]}")

            combined = "\n\n".join(results) or "No output."
            await thinking.edit(
                embed=_embed("[orch] Done", combined[:3900], color=0x00ff88)
            )
        except Exception as exc:
            tb = traceback.format_exc()[-800:]
            await thinking.edit(
                embed=_embed("[orch] Error", f"```python\n{tb}```", color=0xff4444)
            )
    except Exception as e:
        logger.error(f"❌ on_message error: {e}", exc_info=True)

# -- Slash Commands -----------------------------------------------------------

@tree.command(name="brain", description="Send a task to the OpenClaw brain")
@app_commands.describe(task="What should the swarm do?")
async def cmd_brain(interaction: discord.Interaction, task: str):
    """Brain command."""
    try:
        await interaction.response.defer(thinking=True)
        logger.info(f"⚙️ /brain command from {interaction.user}: {task[:80]}")

        result = await _run_agent("orchestrator", task)
        await interaction.followup.send(
            embed=_embed("[brain] Result", result[:3900])
        )
    except Exception as exc:
        logger.error(f"❌ /brain error: {exc}", exc_info=True)
        await interaction.followup.send(
            embed=_embed("[brain] Error", f"```python\n{traceback.format_exc()[-800:]}```", color=0xff4444)
        )

@tree.command(name="status", description="OpenClaw system status")
async def cmd_status(interaction: discord.Interaction):
    """Status command."""
    try:
        await interaction.response.defer(thinking=True)
        logger.info(f"⚙️ /status command from {interaction.user}")

        stats = get_stats()
        lines = [
            f"Tasks total : {stats.get('tasks_total', 0)}",
            f"Done : {stats.get('tasks_done', 0)}",
            f"Failed : {stats.get('tasks_failed', 0)}",
            f"Agents : {len(AGENT_PERSONAS)}",
            f"Model : {os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant')}",
        ]
        await interaction.followup.send(
            embed=_embed("[status] OpenClaw", "\n".join(lines))
        )
    except Exception as exc:
        logger.error(f"❌ /status error: {exc}", exc_info=True)
        await interaction.followup.send(
            embed=_embed("[status] Error", str(exc), color=0xff4444)
        )

@tree.command(name="agents", description="List all agent personas")
async def cmd_agents(interaction: discord.Interaction):
    """Agents command."""
    try:
        await interaction.response.defer(thinking=True)
        logger.info(f"⚙️ /agents command from {interaction.user}")

        lines = [f"**{k}**: {v[:60]}..." for k, v in AGENT_PERSONAS.items()]
        await interaction.followup.send(
            embed=_embed("[agents] Swarm Roster", "\n".join(lines))
        )
    except Exception as exc:
        logger.error(f"❌ /agents error: {exc}", exc_info=True)
        await interaction.followup.send(
            embed=_embed("[agents] Error", str(exc), color=0xff4444)
        )

@tree.command(name="swarm", description="Run a multi-agent swarm on a task")
@app_commands.describe(task="Task for the full swarm")
async def cmd_swarm(interaction: discord.Interaction, task: str):
    """Swarm command."""
    try:
        await interaction.response.defer(thinking=True)
        logger.info(f"⚙️ /swarm command from {interaction.user}: {task[:80]}")

        plan = await _orchestrate(task)
        results = []
        for step in plan:
            agent = step.get("agent", "orchestrator")
            sub = step.get("task", task)
            try:
                out = await _run_agent(agent, sub)
                results.append(f"**[{agent}]**: {out[:300]}")
            except Exception as e:
                results.append(f"**[{agent}]**: ❌ {str(e)[:200]}")

        combined = "\n\n".join(results) or "No output."
        await interaction.followup.send(
            embed=_embed("[swarm] Done", combined[:3900], color=0x00ff88)
        )
    except Exception as exc:
        logger.error(f"❌ /swarm error: {exc}", exc_info=True)
        await interaction.followup.send(
            embed=_embed("[swarm] Error", f"```python\n{traceback.format_exc()[-800:]}```", color=0xff4444)
        )

# -- Entry --------------------------------------------------------------------

# ── Brain singleton for Discord cog ────────────────────────────────────────

_brain_instance = None

def get_brain():
    """Return the brain bot instance (for Discord cog integration)."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = client
    return _brain_instance

def run_brain_bot():
    """Entry point - checks token before starting."""
    if not DISCORD_TOKEN:
        logger.error("Cannot start brain_bot: DISCORD_TOKEN not set")
        return
    logger.info("=" * 60)
    logger.info("OpenClaw Brain Bot Starting")
    logger.info("=" * 60)
    try:
        client.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Brain bot shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    run_brain_bot()
