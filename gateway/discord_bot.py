"""
OpenClaw Discord Command Center
Slash command interface for the OpenClaw swarm system.
"""
import asyncio
import json
from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from shared.config import Config
from shared.logging import setup_logging, get_logger
from gateway.brain_bot import get_brain
from memory import save_task, get_stats
from worker.ai_worker import AGENT_PERSONAS

logger = get_logger(__name__)


class DiscordBot(commands.Cog):
    """Discord bot commands for OpenClaw."""

    def __init__(self, bot: commands.Bot):
        """Initialize Discord bot cog."""
        self.bot = bot
        self.brain = None
        logger.info("DiscordBot cog initialized")

    async def cog_load(self) -> None:
        """Called when cog is loaded."""
        self.brain = await get_brain()
        logger.info("Brain bot reference loaded in Discord cog")

    @app_commands.command(name="ping", description="Ping the bot")
    async def ping(self, interaction: Interaction) -> None:
        """Respond to ping command."""
        try:
            latency = round(self.bot.latency * 1000)
            await interaction.response.send_message(
                f"🏓 Pong! Latency: {latency}ms",
                ephemeral=True
            )
            logger.info(f"Ping command from {interaction.user}: {latency}ms")
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )

    @app_commands.command(
        name="status",
        description="Get OpenClaw system status"
    )
    async def status(self, interaction: Interaction) -> None:
        """Get bot and system status."""
        try:
            await interaction.response.defer(thinking=True)

            if not self.brain:
                await interaction.followup.send("⚠️ Brain bot not initialized")
                return

            health = await self.brain.health_check()
            stats = health.get("stats", {})

            embed = discord.Embed(
                title="🤖 OpenClaw Status",
                color=discord.Color.green(),
                description=f"System Status: **{health.get('status', 'unknown')}**"
            )
            embed.add_field(name="Queue Size", value=str(health.get("queue_size", 0)), inline=True)
            embed.add_field(name="Cache Size", value=str(health.get("cache_size", 0)), inline=True)
            embed.add_field(name="Total Tasks", value=str(stats.get("total", 0)), inline=True)
            embed.add_field(name="Completed", value=str(stats.get("done", 0)), inline=True)
            embed.add_field(name="Failed", value=str(stats.get("failed", 0)), inline=True)
            embed.add_field(name="Pending", value=str(stats.get("pending", 0)), inline=True)

            await interaction.followup.send(embed=embed)
            logger.info(f"Status command from {interaction.user}")
        except Exception as e:
            logger.error(f"Error in status command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")

    @app_commands.command(
        name="task",
        description="Submit a task to OpenClaw agents"
    )
    @app_commands.describe(
        text="Task description",
        agent="Agent to use (default: orchestrator)"
    )
    async def task(
        self,
        interaction: Interaction,
        text: str,
        agent: Optional[str] = None
    ) -> None:
        """Submit a task to the OpenClaw system."""
        try:
            await interaction.response.defer(thinking=True)

            agent = agent or "orchestrator"
            if agent not in AGENT_PERSONAS:
                await interaction.followup.send(
                    f"❌ Unknown agent: {agent}\n"
                    f"Available: {', '.join(AGENT_PERSONAS.keys())}",
                    ephemeral=True
                )
                return

            # Save task to database
            task_id = save_task(text, agent)
            logger.info(f"Task created: {task_id} (agent: {agent})")

            # Submit to brain bot
            if self.brain:
                await self.brain.submit_task({
                    "task": text,
                    "agent": agent,
                    "discord_user": str(interaction.user),
                    "discord_channel": interaction.channel_id,
                })

            await interaction.followup.send(
                f"✅ Task submitted: `{task_id}`\n"
                f"🤖 Agent: **{agent.upper()}**\n"
                f"📝 Task: {text[:100]}{'...' if len(text) > 100 else ''}\n"
                f"📤 Results will be posted to Slack #ops",
                ephemeral=False
            )

        except Exception as e:
            logger.error(f"Error in task command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")

    @app_commands.command(
        name="agents",
        description="List all available agents"
    )
    async def agents(self, interaction: Interaction) -> None:
        """List available agents."""
        try:
            await interaction.response.defer(thinking=True)

            embed = discord.Embed(
                title="🤖 OpenClaw Agents",
                color=discord.Color.blue(),
                description="Available agent personas for task execution"
            )

            for agent_name, description in AGENT_PERSONAS.items():
                embed.add_field(
                    name=f"**{agent_name.upper()}**",
                    value=description[:100] + "..." if len(description) > 100 else description,
                    inline=False
                )

            await interaction.followup.send(embed=embed)
            logger.info(f"Agents command from {interaction.user}")
        except Exception as e:
            logger.error(f"Error in agents command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")

    @app_commands.command(
        name="stats",
        description="View task database statistics"
    )
    async def stats(self, interaction: Interaction) -> None:
        """View task statistics."""
        try:
            await interaction.response.defer(thinking=True)

            stats = get_stats()

            embed = discord.Embed(
                title="📊 OpenClaw Task Statistics",
                color=discord.Color.purple(),
                description="Overall task database statistics"
            )

            embed.add_field(name="Total Tasks", value=str(stats.get("total", 0)), inline=True)
            embed.add_field(name="✅ Completed", value=str(stats.get("done", 0)), inline=True)
            embed.add_field(name="❌ Failed", value=str(stats.get("failed", 0)), inline=True)
            embed.add_field(name="⏳ Pending", value=str(stats.get("pending", 0)), inline=True)

            await interaction.followup.send(embed=embed)
            logger.info(f"Stats command from {interaction.user}")
        except Exception as e:
            logger.error(f"Error in stats command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")


async def main() -> None:
    """Run Discord bot."""
    logger.info("=" * 60)
    logger.info("OpenClaw Discord Bot Starting")
    logger.info("=" * 60)

    if not Config.DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not configured")
        return

    Config.log_config()

    # Create bot
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready() -> None:
        """Called when bot is ready."""
        logger.info(f"✓ Discord bot logged in as {bot.user}")
        logger.info(f"✓ Syncing {len(bot.tree._get_all_commands())} commands")
        try:
            synced = await bot.tree.sync()
            logger.info(f"✓ Synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    # Add cog
    await bot.add_cog(DiscordBot(bot))

    # Start bot
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Discord bot shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    setup_logging("discord_bot")
    asyncio.run(main())
