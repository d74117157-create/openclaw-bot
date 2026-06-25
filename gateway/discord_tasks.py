"""
Discord slash commands for OpenClaw task system.
/task <description> — submit a task
/status <task_id> — check task status
/pending — list pending tasks
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from worker.task_dispatcher import (
    submit_task,
    execute_task,
    get_task_status,
    list_pending,
)

logger = logging.getLogger(__name__)


class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="task", description="Submit a task to OpenClaw")
    @app_commands.describe(
        description="What should the bot do?",
        agent="Which agent? (orchestrator, coder, researcher, ops, growth, qa)"
    )
    async def task_submit(
        self,
        interaction: discord.Interaction,
        description: str,
        agent: str = "orchestrator"
    ):
        """Submit a task for execution."""
        await interaction.response.defer(thinking=True)
        
        try:
            # Submit task
            task_id = await submit_task(
                description,
                agent=agent,
                requester=f"discord:{interaction.user.name}",
                channel_id=str(interaction.channel_id)
            )
            
            # Execute immediately
            result = await execute_task(task_id)
            
            # Reply with result
            embed = discord.Embed(
                title="✅ Task Completed",
                description=result[:1024],
                color=discord.Color.green()
            )
            embed.add_field(name="Task ID", value=task_id, inline=False)
            embed.add_field(name="Agent", value=agent, inline=True)
            embed.add_field(name="Requester", value=interaction.user.name, inline=True)
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Discord task {task_id} completed: {result[:100]}")
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Task Failed",
                description=str(e)[:1024],
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            logger.error(f"Discord task error: {e}", exc_info=True)
    
    @app_commands.command(name="status", description="Check task status")
    @app_commands.describe(task_id="The task ID to check")
    async def task_status(self, interaction: discord.Interaction, task_id: str):
        """Get status of a specific task."""
        await interaction.response.defer(thinking=True)
        
        try:
            status = await get_task_status(task_id)
            
            if "error" in status:
                embed = discord.Embed(title="❌ Not Found", description=status["error"], color=discord.Color.red())
            else:
                color_map = {
                    "done": discord.Color.green(),
                    "running": discord.Color.blue(),
                    "failed": discord.Color.red(),
                    "pending": discord.Color.yellow(),
                }
                embed = discord.Embed(
                    title=f"Task {task_id}",
                    color=color_map.get(status.get("status"), discord.Color.gray())
                )
                embed.add_field(name="Status", value=status.get("status"), inline=False)
                if status.get("result"):
                    embed.add_field(name="Result", value=status.get("result")[:512], inline=False)
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="pending", description="List pending tasks")
    async def task_pending(self, interaction: discord.Interaction):
        """List all pending tasks."""
        await interaction.response.defer(thinking=True)
        
        try:
            tasks = await list_pending()
            
            if not tasks:
                embed = discord.Embed(title="📋 Pending Tasks", description="None", color=discord.Color.blurple())
            else:
                task_list = "\n".join([
                    f"• **{t.get('id')}**: {t.get('desc')[:60]} ({t.get('agent')})"
                    for t in tasks[:10]
                ])
                embed = discord.Embed(
                    title="📋 Pending Tasks",
                    description=task_list or "None",
                    color=discord.Color.blurple()
                )
                embed.set_footer(text=f"Total: {len(tasks)}")
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")


async def setup(bot):
    """Load TaskCog into bot."""
    await bot.add_cog(TaskCog(bot))
