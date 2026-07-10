"""Health check endpoints."""
from fastapi import APIRouter
from datetime import datetime
import platform, psutil
health_router = APIRouter()

@health_router.get("/")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "platform": platform.system(),
            "cpu_percent": psutil.cpu_percent(interval=0.1), "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent}

@health_router.get("/ready")
async def ready(): return {"status": "ready"}

@health_router.get("/live")
async def live(): return {"status": "alive"}
