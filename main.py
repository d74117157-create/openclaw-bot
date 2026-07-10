#!/usr/bin/env python3
"""OpenClaw Superswarm — Multi-Agent Bot Swarm"""
import os, asyncio, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.config import settings
from core.swarm_orchestrator import SwarmOrchestrator
from core.health import health_router
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("logs/openclaw.log"), logging.StreamHandler()])
logger = logging.getLogger("openclaw")
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

swarm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global swarm
    logger.info("🚀 OpenClaw Superswarm initializing...")
    swarm = SwarmOrchestrator()
    await swarm.start()
    logger.info("✅ Swarm online.")
    yield
    logger.info("🛑 Swarm shutting down...")
    await swarm.stop()

app = FastAPI(title="OpenClaw Superswarm", version="2.0.0", lifespan=lifespan)
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {"name": "OpenClaw Superswarm", "version": "2.0.0", "status": "online",
            "swarm_active": swarm.is_running if swarm else False, "agents": swarm.agent_count if swarm else 0}

@app.get("/swarm/status")
async def swarm_status():
    if not swarm: return JSONResponse({"error": "Swarm not initialized"}, status_code=503)
    return await swarm.status()

@app.post("/swarm/reload")
async def swarm_reload():
    if not swarm: return JSONResponse({"error": "Swarm not initialized"}, status_code=503)
    await swarm.reload()
    return {"message": "Swarm reloaded"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.ENVIRONMENT == "development")
