from fastapi import FastAPI
import os

app = FastAPI()


@app.get("/health")
async def health():
    """Basic health check used by load balancers and Render.
    Returns 200 quickly so Render knows the service is up.
    """
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """Readiness check. Can be extended to probe DB/LLM connectivity.
    For now returns ready if the process is running.
    """
    # Future: check DB file, LLM endpoint, etc.
    return {"status": "ready"}
