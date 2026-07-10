#!/usr/bin/env python3
"""OpenClaw Superswarm — Multi-Agent Bot Swarm v2.0"""
import os, sys, asyncio, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.config import settings
from core.swarm_orchestrator import SwarmOrchestrator
from core.health import health_router
import uvicorn

# Create dirs BEFORE logging setup — try multiple locations
for log_dir in ["/app/logs", "./logs", "/tmp/openclaw_logs"]:
    try:
        os.makedirs(log_dir, exist_ok=True)
        os.environ["OPENCLAW_LOG_DIR"] = log_dir
        break
    except OSError:
        continue
else:
    os.environ["OPENCLAW_LOG_DIR"] = "/tmp"

log_path = os.path.join(os.environ["OPENCLAW_LOG_DIR"], "openclaw.log")
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("openclaw")

swarm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global swarm
    logger.info("🚀 OpenClaw Superswarm v2.0 initializing...")
    swarm = SwarmOrchestrator()
    await swarm.start()
    logger.info("✅ Swarm online. All agents reporting for duty.")
    yield
    logger.info("🛑 Swarm shutting down...")
    await swarm.stop()
    logger.info("✅ Swarm offline.")

app = FastAPI(title="OpenClaw Superswarm", description="Multi-agent bot swarm with Discord, Telegram, Slack, and AI orchestration", version="2.0.0", lifespan=lifespan)
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {
        "name": "OpenClaw Superswarm",
        "version": "2.0.0",
        "status": "online",
        "swarm_active": swarm.is_running if swarm else False,
        "agents": swarm.agent_count if swarm else 0,
        "platforms": list(swarm._bots.keys()) if swarm else [],
    }

@app.get("/swarm/status")
async def swarm_status():
    if not swarm: return JSONResponse({"error": "Swarm not initialized"}, status_code=503)
    return await swarm.status()

@app.post("/swarm/reload")
async def swarm_reload():
    if not swarm: return JSONResponse({"error": "Swarm not initialized"}, status_code=503)
    await swarm.reload()
    return {"message": "Swarm reloaded successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.ENVIRONMENT == "development")
