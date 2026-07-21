"""OpenClaw Empire — Production Main Application"""
import sys
import os
import time

# Ensure parent directory is in path for imports
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logger import logger
from app.database.models import init_database, SessionLocal, Task, AgentLog, SystemEvent
from app.brain.ai_client import AIBrain
from app.agents.orchestrator import OrchestratorAgent
from app.agents.viktor import ViktorAgent
from app.agents.dave import DaveAgent
from app.agents.carla import CarlaAgent
from app.agents.alice import AliceAgent
from app.agents.gbaby import GBabyAgent
from app.agents.security import SecurityAgent
from app.agents.researcher import ResearcherAgent
from app.agents.coder import CoderAgent
from app.agents.qa import QAAgent

# Global state
orchestrator: OrchestratorAgent = None
ai_brain: AIBrain = None
_startup_time = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Production startup and shutdown with error recovery."""
    global orchestrator, ai_brain, _startup_time

    logger.info("=" * 60)
    logger.info("OPENCLAW EMPIRE STARTING")
    logger.info("=" * 60)

    _startup_time = datetime.utcnow()

    # Initialize database with retry
    db_ok = False
    for attempt in range(3):
        try:
            init_database()
            db_ok = True
            logger.info("[STARTUP] Database initialized")
            break
        except Exception as e:
            logger.warning(f"[STARTUP] DB init attempt {attempt+1}/3 failed: {e}")
            await asyncio.sleep(1)
    if not db_ok:
        logger.error("[STARTUP] Database initialization failed after 3 attempts")

    # Initialize AI Brain
    try:
        ai_brain = AIBrain()
        logger.info(f"[STARTUP] AI Brain primary: {ai_brain.primary}")
    except Exception as e:
        logger.error(f"[STARTUP] AI Brain init failed: {e}")
        ai_brain = None

    # Initialize Orchestrator
    try:
        orchestrator = OrchestratorAgent(ai_brain)
    except Exception as e:
        logger.error(f"[STARTUP] Orchestrator init failed: {e}")
        orchestrator = None

    # Register all agents
    if orchestrator:
        agents = [
            ViktorAgent(ai_brain),
            DaveAgent(ai_brain),
            CarlaAgent(ai_brain),
            AliceAgent(ai_brain),
            GBabyAgent(ai_brain),
            SecurityAgent(ai_brain),
            ResearcherAgent(ai_brain),
            CoderAgent(ai_brain),
            QAAgent(ai_brain),
        ]
        for agent in agents:
            try:
                orchestrator.register_agent(agent)
            except Exception as e:
                logger.warning(f"[STARTUP] Failed to register {agent.name}: {e}")

        logger.info(f"[STARTUP] {len(orchestrator.agents)} agents registered")

    # Log startup event
    try:
        db = SessionLocal()
        db.add(SystemEvent(event_type="startup", platform="api", details="OpenClaw Empire initialized"))
        db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"[STARTUP] Could not log startup event: {e}")

    logger.info(f"[STARTUP] Database: {settings.database_url}")
    logger.info("[STARTUP] OpenClaw Empire READY")

    yield

    # Shutdown
    logger.info("[SHUTDOWN] OpenClaw Empire stopping...")
    try:
        db = SessionLocal()
        db.add(SystemEvent(event_type="shutdown", platform="api", details="OpenClaw Empire shutdown"))
        db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"[SHUTDOWN] Could not log shutdown event: {e}")
    logger.info("[SHUTDOWN] OpenClaw Empire stopped")


app = FastAPI(
    title="OpenClaw Empire",
    description="Unified AI Command Center",
    version="3.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint for Render health probe."""
    return {"status": "ok", "service": "openclaw-empire", "version": "3.1.0"}


@app.get("/health")
async def health():
    """Production health check for Render/Railway."""
    healthy = True
    checks = {
        "status": "healthy" if healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.1.0",
        "uptime": (datetime.utcnow() - _startup_time).total_seconds() if _startup_time else 0,
    }
    return checks


@app.get("/ready")
async def ready():
    """Readiness check with dependency status."""
    if not orchestrator or not ai_brain:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "initialization incomplete",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    try:
        config_check = settings.validate()
    except Exception as e:
        config_check = {"error": str(e)}

    return {
        "status": "ready",
        "ai_brain": {
            "primary": ai_brain.primary if ai_brain else "none",
            "configured": ai_brain.is_configured() if ai_brain else False,
            "providers": list(ai_brain.providers.keys()) if ai_brain else []
        },
        "agents": {
            "registered": list(orchestrator.agents.keys()) if orchestrator else [],
            "count": len(orchestrator.agents) if orchestrator else 0
        },
        "config": config_check,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def status():
    """Full system status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")

    try:
        orch_status = orchestrator.get_status()
    except Exception as e:
        orch_status = {"error": str(e)}

    try:
        brain_stats = ai_brain.get_stats() if ai_brain else {}
    except Exception as e:
        brain_stats = {"error": str(e)}

    return {
        "orchestrator": orch_status,
        "ai_brain": brain_stats,
        "config": settings.validate(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/goal")
async def submit_goal(goal: str, source: str = "api"):
    """Submit a goal for execution."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    logger.info(f"[API] Goal received from {source}: {goal[:80]}")

    # Log to database
    try:
        db = SessionLocal()
        task = Task(
            task_id=f"api_{int(datetime.utcnow().timestamp())}",
            goal=goal,
            agent="orchestrator",
            source=source
        )
        db.add(task)
        db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"[API] Could not log task to DB: {e}")

    # Execute with error recovery
    try:
        result = await orchestrator.execute(goal)
    except Exception as e:
        logger.error(f"[API] Task execution failed: {e}")
        result = {
            "status": "failed",
            "error": str(e),
            "task_id": f"api_{int(datetime.utcnow().timestamp())}"
        }

    return {
        "status": result.get("status", "unknown"),
        "goal": goal,
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")

    try:
        agents = [
            agent.get_status()
            for agent in orchestrator.agents.values()
        ]
    except Exception as e:
        logger.error(f"[API] Failed to list agents: {e}")
        agents = []

    return {"agents": agents}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.health_port))
    uvicorn.run(app, host="0.0.0.0", port=port)
