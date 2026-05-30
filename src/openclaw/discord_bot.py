import asyncio
import os
import logging
from discord import Intents
from discord.ext import commands
from loguru import logger
from .notion_client import NotionClient
from .deployment_manager import DeploymentManager
from typing import Optional

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('DISCORD_APPLICATION_ID')

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def start_discord_bot(notion_api_key: str, notion_db_id: str, dm: Optional[DeploymentManager]=None):
    notion = NotionClient(notion_api_key, notion_db_id)
    manager = dm or DeploymentManager(notion)
    await manager.start()

    @bot.event
    async def on_ready():
        logger.info(f"Discord bot ready: {bot.user}")

    @bot.command()
    async def status(ctx):
        lines = []
        for d in manager.deployments.values():
            active = ' (ACTIVE)' if manager.active and manager.active.name == d.name else ''
            lines.append(f"{d.name}: {d.status} {d.base_url}{active}")
        await ctx.send('\n'.join(lines)[:2000])

    @bot.command()
    async def switch(ctx, *, name: str):
        ok = await manager.override_active(name)
        if ok:
            await ctx.send(f"Switched active to {name}")
        else:
            await ctx.send(f"Deployment {name} not found")

    @bot.command()
    async def sync_notion(ctx):
        await manager.load_from_notion()
        await ctx.send("Synced from Notion")

    await bot.start(DISCORD_TOKEN)
