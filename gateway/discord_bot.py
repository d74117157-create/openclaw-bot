"""
Discord Gateway — OpenClaw Master Brain
"""
import discord
from discord.ext import commands
import logging
import asyncio
from shared.config import Config

logger = logging.getLogger("discord_gateway")

class DiscordGateway(commands.Bot):
    """Discord interface for the OpenClaw swarm."""

    def __init__(self, swarm):
        self.swarm = swarm
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix="!", intents=intents)
        self._register_commands()

    def _register_commands(self):
        @self.tree.command(name="ask", description="Ask the swarm anything")
        async def ask(interaction: discord.Interaction, question: str):
            await interaction.response.defer(thinking=True)
            task_id = await self.swarm.route_message(
                platform="discord",
                user_id=str(interaction.user.id),
                username=interaction.user.name,
                message=question,
                channel_id=str(interaction.channel_id)
            )
            await interaction.followup.send(f"🧠 Task queued: `{task_id}`. I'll reply when done.")

        @self.tree.command(name="status", description="Check swarm status")
        async def status(interaction: discord.Interaction):
            stats = self.swarm.get_stats()
            embed = discord.Embed(title="OpenClaw Status", color=0x00ff88)
            embed.add_field(name="Uptime", value=f"{int(stats['uptime_seconds'])}s", inline=True)
            embed.add_field(name="Tasks", value=str(stats['tasks_total']), inline=True)
            embed.add_field(name="Gateways", value=", ".join(stats['gateways']), inline=False)
            await interaction.response.send_message(embed=embed)

    async def start(self):
        """Start the Discord bot."""
        if not Config.DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN not set")
            return
        await super().start(Config.DISCORD_TOKEN)

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Send message to Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                channel = await self.fetch_channel(int(channel_id))
            
            if channel:
                prefix = f"✅ **Task `{task_id}` complete:**\n\n" if task_id else ""
                # Discord 2000 char limit
                if len(prefix + content) > 1900:
                    content = content[:1800] + "\n\n... (truncated)"
                await channel.send(f"{prefix}{content}")
        except Exception as e:
            logger.error(f"Discord send failed: {e}")

    async def on_ready(self):
        logger.info(f"Discord gateway logged in as {self.user}")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
            
        # Handle mentions or DMs
        if isinstance(message.channel, discord.DMChannel) or self.user.mentioned_in(message):
            clean_content = message.content.replace(f'<@!{self.user.id}>', '').replace(f'<@{self.user.id}>', '').strip()
            await self.swarm.route_message(
                platform="discord",
                user_id=str(message.author.id),
                username=message.author.name,
                message=clean_content,
                channel_id=str(message.channel.id)
            )
        
        await self.process_commands(message)
