from .db_models import Deployment
from .notion_client import NotionClient
from .utils.retry import exponential_backoff
import aiohttp
import asyncio
from typing import Callable, Awaitable, Optional, List, Dict
from loguru import logger

CHECK_INTERVAL = 60
HEALTH_TIMEOUT = 5

class DeploymentManager:
    def __init__(self, notion: NotionClient):
        self.notion = notion
        self.deployments: Dict[str, Deployment] = {}
        self.active: Optional[Deployment] = None
        self._callbacks: List[Callable[[Optional[Deployment]], Awaitable[None]]] = []
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        await self.load_from_notion()
        self._task = asyncio.create_task(self._loop())
        logger.info("DeploymentManager started")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _loop(self) -> None:
        while True:
            try:
                await self.health_check_all()
            except Exception as e:
                logger.exception("Error in deployment manager loop: {}", e)
            await asyncio.sleep(CHECK_INTERVAL)

    async def load_from_notion(self) -> None:
        pages = await self.notion.list_deployments()
        new_deployments = {p.name: p for p in pages}
        async with self._lock:
            self.deployments = new_deployments
        await self.health_check_all()

    async def health_check_all(self) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, dep in list(self.deployments.items()):
                tasks.append(self._check_and_update(session, dep))
            results = await asyncio.gather(*tasks, return_exceptions=True)
        await self._select_active()

    async def _check_and_update(self, session: aiohttp.ClientSession, dep: Deployment) -> None:
        url = dep.base_url.rstrip('/') + '/health'
        status = 'offline'
        try:
            async with session.get(url, timeout=HEALTH_TIMEOUT) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    status = 'online'
                else:
                    status = 'degraded'
        except asyncio.TimeoutError:
            status = 'offline'
        except Exception:
            status = 'offline'
        if dep.status != status:
            logger.info(f"Deployment {dep.name} status change {dep.status} -> {status}")
            dep.status = status
            await self.notion.update_deployment_status(dep)
        dep.last_checked = asyncio.get_event_loop().time()

    async def _select_active(self) -> None:
        # sort by status (online>degraded>offline) and priority asc
        status_rank = {'online': 0, 'degraded': 1, 'offline': 2}
        candidates = sorted(self.deployments.values(), key=lambda d: (status_rank.get(d.status, 2), d.priority))
        chosen = candidates[0] if candidates else None
        if chosen and (self.active is None or chosen.name != self.active.name):
            self.active = chosen
            logger.info(f"Active deployment set to {chosen.name} ({chosen.base_url})")
            await self._emit_change(self.active)

    async def _emit_change(self, dep: Optional[Deployment]) -> None:
        for cb in self._callbacks:
            try:
                await cb(dep)
            except Exception:
                logger.exception("Callback error")

    def register_callback(self, cb: Callable[[Optional[Deployment]], Awaitable[None]]) -> None:
        self._callbacks.append(cb)

    def get_active_base_url(self) -> Optional[str]:
        return self.active.base_url if self.active else None

    async def override_active(self, name: str) -> bool:
        async with self._lock:
            dep = self.deployments.get(name)
            if not dep:
                return False
            self.active = dep
            await self._emit_change(dep)
            return True
