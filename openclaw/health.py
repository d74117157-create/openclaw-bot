"""FastAPI health server for OpenClaw."""

import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger("openclaw.health")


def create_health_app() -> FastAPI:
    """Create health check FastAPI application."""
    app = FastAPI(title="OpenClaw Health", version="4.0.0")

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {"status": "healthy", "service": "openclaw", "version": "4.0.0"}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        return JSONResponse(content={"status": "ready"}, status_code=200)

    @app.get("/metrics")
    async def metrics() -> Dict[str, Any]:
        return {"service": "openclaw", "version": "4.0.0"}

    return app


class HealthServer:
    """Managed health server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.app = create_health_app()
        self._server = None
        self._task = None

    async def start(self) -> None:
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())
        logger.info(f"Health server on {self.host}:{self.port}")

    async def stop(self) -> None:
        if self._server:
            self._server.should_exit = True
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
