import os
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
import asyncio
from loguru import logger
from .deployment_manager import DeploymentManager
from .notion_client import NotionClient
from .utils.retry import retry_with_backoff

SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

app = AsyncApp(token=SLACK_BOT_TOKEN)

async def start_slack(notion_api_key: str, notion_db_id: str, manager: DeploymentManager=None):
    notion = NotionClient(notion_api_key, notion_db_id)
    if manager is None:
        manager = DeploymentManager(notion)
        await manager.start()

    @app.command('/openclaw-status')
    async def status_command(ack, respond):
        await ack()
        lines = []
        for d in manager.deployments.values():
            active = ' (ACTIVE)' if manager.active and manager.active.name == d.name else ''
            lines.append(f"{d.name}: {d.status} {d.base_url}{active}")
        await respond('\n'.join(lines)[:3000])

    @app.command('/openclaw-build')
    async def build_command(ack, body, respond):
        await ack()
        user = body.get('user_id')
        active = manager.get_active_base_url()
        if not active:
            await respond('No active deployment available')
            return
        # Example: send a request to active deployment to trigger an autonomous task
        url = active.rstrip('/') + '/tasks'
        async with manager.notion.client._client._session.get_adapter('https://'):
            pass
        await respond(f'Triggered build at {url} (simulated)')

    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()
