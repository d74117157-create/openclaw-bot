"""
OpenClaw - gateway/bot.py
Extended Discord bot with task management and deployment slash commands.
FIXED: Complete indentation, async safety, proper error handling, sys.path fix.
"""
import sys
import os

# Fix: Add parent directory to path so 'memory' and 'worker' packages are found
# when running from /app/gateway/bot.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import asyncio
import traceback
import json
import discord
from discord import app_commands
from dotenv import load_dotenv

from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS
from worker.slack_reporter import task_started, agent_complete, task_complete

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "openclaw-ops")

if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN not set in environment")

intents = discord.Intents.default()
intents.message_content = True


class OpenClawBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        init_db()
        print("[OpenClawBot] Commands synced, database ready")

    async def on_ready(self):
        print(f"[OpenClawBot] Online as {self.user}")


bot = OpenClawBot()
tree = bot.tree


# ── Helpers ────────────────────────────────────────────────────────────
def _embed(title: str, desc: str, color: int = 0x00bfff) -> discord.Embed:
    """Create a nice Discord embed."""
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text="OpenClaw")
    return e


async def _run_agent(agent: str, task_desc: str) -> str:
    """Run a single agent on a task."""
    tid = save_task(task_desc, agent)
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, lambda: process_task(task_desc, agent)
        )
        update_task(tid, result, "done")
        # Post to Slack
        agent_complete(agent, task_desc, result, success=True)
        return result
    except Exception as exc:
        error_msg = str(exc)
        update_task(tid, error_msg, "failed")
        agent_complete(agent, task_desc, error_msg, success=False)
        raise


# ── Slash Commands ─────────────────────────────────────────────────────

@tree.command(name="create-task", description="Create and execute a task with agent swarm")
@app_commands.describe(
    task="Describe what you want done (any complexity)"
)
async def cmd_create_task(interaction: discord.Interaction, task: str):
    """Main /create-task command - orchestrates agents."""
    await interaction.response.defer(thinking=True)

    try:
        # Notify Slack that task started
        task_started(task, [], needs_browser=False)

        # Orchestrate the task
        loop = asyncio.get_event_loop()
        plan_raw = await loop.run_in_executor(None, lambda: orchestrate_task(task))

        try:
            plan = json.loads(plan_raw)
        except json.JSONDecodeError:
            plan = [{"agent": "orchestrator", "task": task}]
            await interaction.followup.send(
                embed=_embed("⚠️ Orchestration", "Using fallback agent plan")
            )

        # Show plan
        agent_summary = ", ".join(f"**{p['agent']}**" for p in plan if p.get('agent') in AGENT_PERSONAS)
        await interaction.followup.send(
            embed=_embed(
                "🧠 Auto-Plan",
                f"**Agents:** {agent_summary}\n"
                f"**Task:** {task[:100]}\n"
                f"**Results → Slack** #{SLACK_CHANNEL}",
                color=0xffaa00
            )
        )

        # Execute all agents in parallel
        tasks = []
        for step in plan:
            agent = step.get("agent", "orchestrator")
            subtask = step.get("task", task)
            if agent in AGENT_PERSONAS:
                tasks.append(_run_agent(agent, subtask))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        await interaction.followup.send(
            embed=_embed("🏁 Complete", "All agents done. Check Slack for details.", color=0x00ff88)
        )

    except Exception as e:
        error_trace = traceback.format_exc()[-800:]
        await interaction.followup.send(
            embed=_embed("❌ Error", f"```{error_trace}```", color=0xff4444)
        )
        print(f"[create-task] Error: {e}")


@tree.command(name="swarm", description="Manually pick agents and run them")
@app_commands.describe(
    agents="Comma-separated agent names: coder,ops,qa,reviewer,research,growth,memory,github,orchestrator",
    task="Task description"
)
async def cmd_swarm(interaction: discord.Interaction, agents: str, task: str):
    """Manual swarm command - pick specific agents."""
    await interaction.response.defer(thinking=True)

    try:
        agent_list = [a.strip() for a in agents.split(",")]
        bad = [a for a in agent_list if a not in AGENT_PERSONAS]

        if bad:
            await interaction.followup.send(
                embed=_embed(
                    "❓ Unknown Agents",
                    f"Bad: {', '.join(bad)}\nAvailable: {', '.join(AGENT_PERSONAS.keys())}",
                    color=0xff6600
                )
            )
            return

        # Notify Slack
        task_started(task, [{"agent": a, "task": task} for a in agent_list], needs_browser=False)

        await interaction.followup.send(
            embed=_embed("🐝 Swarm Running", f"**Agents:** {len(agent_list)}\n**Task:** {task[:100]}")
        )

        # Run agents in parallel
        tasks = [_run_agent(a, task) for a in agent_list]
        await asyncio.gather(*tasks, return_exceptions=True)

        await interaction.followup.send(
            embed=_embed("🏁 Swarm Done", "All agents completed. Results in Slack.", color=0x00ff88)
        )

    except Exception as e:
        error_trace = traceback.format_exc()[-800:]
        await interaction.followup.send(
            embed=_embed("❌ Error", f"```{error_trace}```", color=0xff4444)
        )
        print(f"[swarm] Error: {e}")


@tree.command(name="agents", description="List all available agents")
async def cmd_agents(interaction: discord.Interaction):
    """List all agent personas."""
    try:
        await interaction.response.defer(thinking=True)
        lines = [f"**{k}** — {v[:65]}…" for k, v in AGENT_PERSONAS.items()]
        await interaction.followup.send(
            embed=_embed("🤖 OpenClaw Agents", "\n".join(lines))
        )
    except Exception as e:
        print(f"[agents] Error: {e}")


@tree.command(name="status", description="Show system status and stats")
async def cmd_status(interaction: discord.Interaction):
    """Show OpenClaw status."""
    try:
        await interaction.response.defer(thinking=True)
        stats = get_stats()
        lines = [
            f"**Tasks Total:** {stats.get('tasks_total', 0)}",
            f"**Done:** {stats.get('tasks_done', 0)}",
            f"**Failed:** {stats.get('tasks_failed', 0)}",
            f"**Decisions:** {stats.get('decisions', 0)}",
            f"**Deployments:** {stats.get('deployments', 0)}",
        ]
        await interaction.followup.send(
            embed=_embed("📊 OpenClaw Status", "\n".join(lines))
        )
    except Exception as e:
        print(f"[status] Error: {e}")


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw Discord Bot Starting")
    print("Python path:", sys.path)
    print("=" * 60)
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()


# ── Task System Commands ────────────────────────────────────────────────
from worker.task_dispatcher import submit_task, execute_task, get_task_status, list_pending as list_pending_tasks

@tree.command(name="task", description="Submit a task to OpenClaw")
@app_commands.describe(
    description="What should the bot do?",
    agent="Which agent? (orchestrator, coder, researcher, ops, growth, qa)"
)
async def task_command(
    interaction: discord.Interaction,
    description: str,
    agent: str = "orchestrator"
):
    """Submit and execute a task."""
    await interaction.response.defer(thinking=True)
    
    try:
        task_id = await submit_task(description, agent, f"discord:{interaction.user.name}", str(interaction.channel_id))
        result = await execute_task(task_id)
        
        embed = _embed(f"✅ Task {task_id}", result[:1000])
        embed.add_field(name="Agent", value=agent, inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = _embed(f"❌ Error", str(e)[:500], color=0xff0000)
        await interaction.followup.send(embed=embed)


@tree.command(name="status", description="Check task status")
@app_commands.describe(task_id="Task ID to check")
async def status_command(interaction: discord.Interaction, task_id: str):
    """Check status of a task."""
    await interaction.response.defer(thinking=True)
    
    try:
        status = await get_task_status(task_id)
        if "error" in status:
            embed = _embed("❌ Not Found", status["error"], color=0xff0000)
        else:
            desc = f"**Status**: {status.get('status')}\n**Result**: {status.get('result', 'N/A')[:500]}"
            embed = _embed(f"Task {task_id}", desc)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = _embed("❌ Error", str(e)[:500], color=0xff0000)
        await interaction.followup.send(embed=embed)


@tree.command(name="pending", description="List pending tasks")
async def pending_command(interaction: discord.Interaction):
    """List all pending tasks."""
    await interaction.response.defer(thinking=True)
    
    try:
        tasks = await list_pending_tasks()
        if not tasks:
            desc = "No pending tasks"
        else:
            desc = "\n".join([f"• {t.get('id')}: {t.get('desc')[:60]}" for t in tasks[:10]])
        embed = _embed("📋 Pending Tasks", desc)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = _embed("❌ Error", str(e)[:500], color=0xff0000)
        await interaction.followup.send(embed=embed)


print("[OpenClaw] Task commands registered: /task, /status, /pending")
