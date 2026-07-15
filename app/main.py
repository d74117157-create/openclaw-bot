"""OpenClaw Empire — Main Application"""
import sys
import os

# Ensure parent directory is in path for imports
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
import os
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global orchestrator, ai_brain

    logger.info("=" * 60)
    logger.info("OPENCLAW EMPIRE STARTING")
    logger.info("=" * 60)

    # Initialize database
    init_database()

    # Initialize AI Brain
    ai_brain = AIBrain()

    # Initialize Orchestrator
    orchestrator = OrchestratorAgent(ai_brain)

    # Register all agents
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
        orchestrator.register_agent(agent)

    # Log startup
    db = SessionLocal()
    db.add(SystemEvent(event_type="startup", platform="api", details="OpenClaw Empire initialized"))
    db.commit()
    db.close()

    logger.info(f"[STARTUP] {len(agents)} agents registered")
    logger.info(f"[STARTUP] AI Brain primary: {ai_brain.primary}")
    logger.info(f"[STARTUP] Database: {settings.database_url}")

    yield

    # Shutdown
    logger.info("[SHUTDOWN] OpenClaw Empire stopping...")


app = FastAPI(
    title="OpenClaw Empire",
    description="Unified AI Command Center",
    version="3.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check for Render/Railway."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.1.0"
    }


@app.get("/ready")
async def ready():
    """Readiness check with dependency status."""
    if not orchestrator or not ai_brain:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "initialization incomplete"}
        )

    config_check = settings.validate()

    return {
        "status": "ready",
        "ai_brain": {
            "primary": ai_brain.primary,
            "configured": ai_brain.is_configured(),
            "providers": list(ai_brain.providers.keys())
        },
        "agents": {
            "registered": list(orchestrator.agents.keys()),
            "count": len(orchestrator.agents)
        },
        "config": config_check,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def status():
    """Full system status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")

    return {
        "orchestrator": orchestrator.get_status(),
        "ai_brain": ai_brain.get_stats() if ai_brain else {},
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

    # Execute
    result = await orchestrator.execute(goal)

    return {
        "status": "completed",
        "goal": goal,
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")

    return {
        "agents": [
            agent.get_status()
            for agent in orchestrator.agents.values()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.health_port))
    uvicorn.run(app, host="0.0.0.0", port=port)
