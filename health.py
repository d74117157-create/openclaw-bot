"""FastAPI health + metrics server for Render."""
import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger("openclaw.health")

# Global state injected at startup
_swarm_state: Dict[str, Any] = {
    "discord": "initializing",
    "slack": "initializing",
    "telegram": "initializing",
    "tasks_total": 0,
    "tasks_done": 0,
    "tasks_failed": 0,
}


def update_state(key: str, value: Any) -> None:
    _swarm_state[key] = value


def create_app() -> FastAPI:
    app = FastAPI(title="OpenClaw Superswarm", version="5.0.0")

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "service": "openclaw",
            "version": "5.0.0",
            "swarm": _swarm_state,
        }

    @app.get("/ready")
    async def ready() -> JSONResponse:
        all_ready = all(
            _swarm_state.get(k) in ("connected", "online", "polling")
            for k in ("discord", "slack", "telegram")
        )
        return JSONResponse(
            content={"status": "ready" if all_ready else "not_ready"},
            status_code=200 if all_ready else 503,
        )

    @app.get("/metrics")
    async def metrics() -> Dict[str, Any]:
        return {"swarm": _swarm_state}

    @app.post("/telegram/webhook/{bot_id}")
    async def telegram_webhook(bot_id: int, payload: Dict[str, Any]) -> Dict[str, str]:
        # Webhook receiver for Telegram bots if using webhook mode
        return {"status": "ok", "bot_id": str(bot_id)}

    return app


class HealthServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.app = create_app()
        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port,
            log_level="warning", access_log=False
        )
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())
        logger.info(f"Health server on http://{self.host}:{self.port}")

    async def stop(self) -> None:
        if self._server:
            self._server.should_exit = True
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        logger.info("Health server stopped")
