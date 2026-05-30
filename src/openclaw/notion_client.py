from notion_client import Client
from typing import List, Dict, Optional
from .db_models import Deployment
from loguru import logger
import os

class NotionClient:
    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id

    async def _page_to_deployment(self, page: Dict) -> Deployment:
        # Convert Notion page object to Deployment model
        props = page['properties']
        name = props['Name']['title'][0]['plain_text'] if props.get('Name') and props['Name']['title'] else page['id']
        provider = props.get('provider', {}).get('select', {}).get('name', 'custom')
        status = props.get('status', {}).get('select', {}).get('name', 'offline')
        base_url = props.get('base_url', {}).get('url', '')
        priority = props.get('priority', {}).get('number', 100)
        last_checked = None
        return Deployment(name=name, provider=provider, status=status, base_url=base_url, priority=priority, notion_page_id=page['id'])

    async def list_deployments(self) -> List[Deployment]:
        results = []
        # Notion client is sync; call in thread if necessary. For simplicity use sync calls.
        query = self.client.databases.query(database_id=self.database_id)
        for page in query.get('results', []):
            dep = await self._page_to_deployment(page)
            results.append(dep)
        logger.info(f"Loaded {len(results)} deployments from Notion")
        return results

    async def update_deployment_status(self, dep: Deployment) -> None:
        try:
            self.client.pages.update(page_id=dep.notion_page_id, properties={
                'status': {'select': {'name': dep.status}},
                'last_checked': {'date': {'start': None}},
            })
        except Exception:
            logger.exception("Failed updating Notion page")
