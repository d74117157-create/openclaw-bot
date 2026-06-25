"""
OpenClaw - gateway/discord_bot.py
Discord gateway with full slash commands, task dispatcher integration,
and multi-agent routing.
"""
import os
import asyncio
import logging
import discord
from discord import app_commands
from dotenv import load_dotenv

from worker.task_dispatcher import submit_task, execute_task, get_task_status, list_pending
from shared.logging import setup_logging, get_logger

load_dotenv()
setup_logging("discord_bot")
logger = get_logger(__name__)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")

class DiscordGateway:
    """Discord interface for OpenClaw swarm with slash commands."""

    def __init__(self, swarm=None):
        self.swarm = swarm
        self.token = DISCORD_TOKEN
        self.guild_id = DISCORD_GUILD_ID

        intents = discord.Intents.default()
        intents.message_content = True

        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)

        # Register events
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        # Register slash commands
        self._register_commands()

    def _register_commands(self):
        """Register all slash commands."""

        @self.tree.command(name="task", description="Submit a task to the OpenClaw swarm")
        @app_commands.describe(description="What should the agents do?")
        async def cmd_task(interaction: discord.Interaction, description: str):
            """Handle /task command."""
            await interaction.response.defer(thinking=True)

            agent = "orchestrator"
            desc_lower = description.lower()
            if any(w in desc_lower for w in ["code", "debug", "fix", "script", "function"]):
                agent = "coder"
            elif any(w in desc_lower for w in ["research", "find", "search", "analyze"]):
                agent = "research"
            elif any(w in desc_lower for w in ["business", "opportunity", "niche", "revenue"]):
                agent = "business"
            elif any(w in desc_lower for w in ["content", "video", "post", "blog"]):
                agent = "growth"

            try:
                task_id = await submit_task(
                    description,
                    agent=agent,
                    requester=f"discord:{interaction.user.name}",
                    channel_id=str(interaction.channel_id)
                )

                result = await execute_task(task_id)

                embed = discord.Embed(
                    title="✅ Task Complete",
                    description=f"**ID:** `{task_id}`\n**Agent:** {agent}\n\n{result[:1500]}",
                    color=0x00ff88
                )
                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"Task error: {e}", exc_info=True)
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to process task: {str(e)[:500]}",
                    color=0xff4444
                )
                await interaction.followup.send(embed=embed)

        @self.tree.command(name="status", description="Check task status")
        @app_commands.describe(task_id="The task ID to check")
        async def cmd_status(interaction: discord.Interaction, task_id: str):
            """Handle /status command."""
            await interaction.response.defer(thinking=True)

            try:
                status = await get_task_status(task_id)

                if "error" in status:
                    embed = discord.Embed(
                        title="❌ Task Not Found",
                        description=f"Task `{task_id}` not found.",
                        color=0xff4444
                    )
                else:
                    embed = discord.Embed(
                        title="📋 Task Status",
                        description=(
                            f"**ID:** `{task_id}`\n"
                            f"**Status:** {status.get('status', 'unknown')}\n"
                            f"**Result:** {status.get('result', 'N/A')[:1000]}"
                        ),
                        color=0x00bfff
                    )
                await interaction.followup.send(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=str(e)[:500],
                    color=0xff4444
                )
                await interaction.followup.send(embed=embed)

        @self.tree.command(name="pending", description="List pending tasks")
        async def cmd_pending(interaction: discord.Interaction):
            """Handle /pending command."""
            await interaction.response.defer(thinking=True)

            try:
                tasks = await list_pending()

                if not tasks:
                    embed = discord.Embed(
                        title="📋 Pending Tasks",
                        description="No pending tasks.",
                        color=0x00bfff
                    )
                else:
                    task_list = "\n".join([
                        f"• `{t.get('id', 'N/A')}`: {t.get('desc', 'N/A')[:40]}..."
                        for t in tasks[:10]
                    ])
                    embed = discord.Embed(
                        title=f"📋 Pending Tasks ({len(tasks)})",
                        description=task_list,
                        color=0x00bfff
                    )
                await interaction.followup.send(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=str(e)[:500],
                    color=0xff4444
                )
                await interaction.followup.send(embed=embed)

        @self.tree.command(name="agents", description="List available agents")
        async def cmd_agents(interaction: discord.Interaction):
            """Handle /agents command."""
            await interaction.response.defer(thinking=True)

            from worker.agents import AGENT_DISPATCH

            agents = "\n".join([f"• **{k}**" for k in AGENT_DISPATCH.keys()])
            embed = discord.Embed(
                title="🤖 Available Agents",
                description=(
                    f"{agents}\n\n"
                    f"Use `/task <description>` to submit a task. "
                    f"The right agent will be selected automatically."
                ),
                color=0x00bfff
            )
            await interaction.followup.send(embed=embed)

        @self.tree.command(name="help", description="Show help information")
        async def cmd_help(interaction: discord.Interaction):
            """Handle /help command."""
            embed = discord.Embed(
                title="🧠 OpenClaw Elite Help",
                description=(
                    "**Commands:**\n"
                    "/task <description> — Submit a task to the swarm\n"
                    "/status <task_id> — Check task status\n"
                    "/pending — List pending tasks\n"
                    "/agents — List available agents\n"
                    "/help — Show this help\n\n"
                    "**How it works:**\n"
                    "1. Submit any task with `/task`\n"
                    "2. The system routes it to the best agent\n"
                    "3. Results are returned in this channel"
                ),
                color=0x00bfff
            )
            await interaction.response.send_message(embed=embed)

    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Discord Gateway ready as {self.client.user}")

        # Sync commands
        try:
            if self.guild_id:
                guild = discord.Object(id=int(self.guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Commands synced to guild {self.guild_id}")
            else:
                await self.tree.sync()
                logger.info("Commands synced globally")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_message(self, message):
        """Handle regular messages."""
        if message.author == self.client.user:
            return

        # Only respond to mentions or DMs
        if not (self.client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
            return

        text = message.content.replace(f"<@{self.client.user.id}>", "").strip()
        if not text:
            return

        logger.info(f"[Discord] {message.author}: {text[:80]}")

        try:
            task_id = await submit_task(
                text,
                agent="orchestrator",
                requester=f"discord:{message.author.name}",
                channel_id=str(message.channel.id)
            )

            result = await execute_task(task_id)

            embed = discord.Embed(
                title="✅ Task Complete",
                description=f"**ID:** `{task_id}`\n\n{result[:1500]}",
                color=0x00ff88
            )
            await message.reply(embed=embed)

        except Exception as e:
            logger.error(f"Message error: {e}", exc_info=True)
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to process: {str(e)[:500]}",
                color=0xff4444
            )
            await message.reply(embed=embed)

    async def start(self):
        """Start the Discord gateway."""
        if not self.token:
            logger.error("No Discord token configured")
            return

        logger.info("Starting Discord gateway...")
        await self.client.start(self.token)

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Discord channel."""
        try:
            channel = self.client.get_channel(int(channel_id))
            if channel:
                prefix = f"✅ **Task `{task_id}` complete**\n\n" if task_id else ""
                embed = discord.Embed(
                    description=f"{prefix}{content[:4000]}",
                    color=0x00ff88
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")

# Standalone runner
if __name__ == "__main__":
    gateway = DiscordGateway()
    asyncio.run(gateway.start())
