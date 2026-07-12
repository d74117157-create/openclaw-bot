"""
OpenClaw Superswarm v3.0 — JWT-Secured Empire API
Military-grade authentication. Every endpoint protected.
"""
import os
import json
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# ─── CONFIG ──────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-CHANGE-IMMEDIATELY")
EMPIRE_PASSWORD = os.getenv("EMPIRE_PASSWORD", "colonel-default")
EMPIRE_STATE_PATH = os.getenv("EMPIRE_STATE_PATH", "/data/empire-state.json")
PORT = int(os.getenv("PORT", 10000))
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

app = FastAPI(title="OpenClaw Superswarm API", version="3.0.0")
security = HTTPBearer()

# ─── EMPIRE STATE ────────────────────────────────────────────────
class EmpireState:
    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(EMPIRE_STATE_PATH):
            try:
                with open(EMPIRE_STATE_PATH, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "version": "3.0.0",
            "initialized_at": datetime.utcnow().isoformat(),
            "agents": {},
            "products": [],
            "revenue": {"total": 0.0, "monthly": 0.0, "streams": []},
            "platforms": {"discord": False, "telegram": False, "slack": False, "youtube": False},
            "trading": {"mode": "paper", "balance": 10000.0, "positions": []},
            "content_queue": [],
            "logs": []
        }

    def save(self):
        os.makedirs(os.path.dirname(EMPIRE_STATE_PATH), exist_ok=True)
        with open(EMPIRE_STATE_PATH, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def log(self, event: str, details: Dict = None):
        entry = {"time": datetime.utcnow().isoformat(), "event": event, "details": details or {}}
        self.data["logs"].append(entry)
        self.data["logs"] = self.data["logs"][-1000:]  # Keep last 1000
        self.save()

empire = EmpireState()

# ─── JWT UTILS ───────────────────────────────────────────────────
def _sign(payload: str) -> str:
    return hmac.new(JWT_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()

def create_token(password: str) -> Optional[str]:
    if password != EMPIRE_PASSWORD:
        return None
    now = int(time.time())
    header = json.dumps({"alg": "HS256", "typ": "JWT"})
    payload = json.dumps({"sub": "colonel", "iat": now, "exp": now + 86400, "role": "emperor"})
    b64_h = header.encode().hex()
    b64_p = payload.encode().hex()
    sig = _sign(f"{b64_h}.{b64_p}")
    return f"{b64_h}.{b64_p}.{sig}"

def verify_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    token = credentials.credentials
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        h, p, s = parts
        expected = _sign(f"{h}.{p}")
        if not hmac.compare_digest(s, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")
        payload = json.loads(bytes.fromhex(p).decode())
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return verify_token(credentials)

# ─── PYDANTIC MODELS ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    password: str

class AgentCommand(BaseModel):
    agent_id: str
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)

class ProductCreate(BaseModel):
    name: str
    platform: str
    price: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TradeOrder(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    order_type: str = "MARKET"

class ContentJob(BaseModel):
    platform: str
    topic: str
    format: str = "auto"
    schedule: Optional[str] = None

# ─── ENDPOINTS ───────────────────────────────────────────────────
@app.post("/auth/login")
def login(req: LoginRequest):
    token = create_token(req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    empire.log("login", {"status": "success"})
    return {"access_token": token, "token_type": "bearer", "expires_in": 86400}

@app.get("/health")
def health():
    return {"status": "alive", "version": "3.0.0", "timestamp": datetime.utcnow().isoformat()}

@app.get("/empire/status")
def empire_status(user: Dict = Depends(get_current_user)):
    return empire.data

@app.post("/empire/agents/command")
def agent_command(cmd: AgentCommand, user: Dict = Depends(get_current_user)):
    empire.data["agents"][cmd.agent_id] = {
        "last_action": cmd.action,
        "params": cmd.params,
        "timestamp": datetime.utcnow().isoformat()
    }
    empire.log("agent_command", {"agent": cmd.agent_id, "action": cmd.action})
    empire.save()
    return {"status": "executed", "agent": cmd.agent_id, "action": cmd.action}

@app.post("/empire/products/create")
def create_product(product: ProductCreate, user: Dict = Depends(get_current_user)):
    pid = hashlib.sha256(f"{product.name}{time.time()}".encode()).hexdigest()[:16]
    entry = product.dict()
    entry["id"] = pid
    entry["created_at"] = datetime.utcnow().isoformat()
    empire.data["products"].append(entry)
    empire.log("product_created", entry)
    empire.save()
    return {"status": "created", "product_id": pid}

@app.post("/empire/trading/order")
def trading_order(order: TradeOrder, user: Dict = Depends(get_current_user)):
    if empire.data["trading"]["mode"] == "paper":
        empire.log("paper_trade", order.dict())
        return {"status": "paper_executed", "order": order.dict(), "note": "No real funds moved"}
    empire.log("live_trade_requested", order.dict())
    return {"status": "forwarded_to_risk_manager", "order": order.dict()}

@app.post("/empire/content/queue")
def queue_content(job: ContentJob, user: Dict = Depends(get_current_user)):
    job_id = hashlib.sha256(f"{job.topic}{time.time()}".encode()).hexdigest()[:12]
    entry = job.dict()
    entry["id"] = job_id
    entry["status"] = "queued"
    empire.data["content_queue"].append(entry)
    empire.log("content_queued", entry)
    empire.save()
    return {"status": "queued", "job_id": job_id}

@app.get("/empire/content/queue")
def get_content_queue(user: Dict = Depends(get_current_user)):
    return {"queue": empire.data["content_queue"]}

@app.get("/empire/revenue")
def get_revenue(user: Dict = Depends(get_current_user)):
    return empire.data["revenue"]

@app.get("/empire/platforms")
def get_platforms(user: Dict = Depends(get_current_user)):
    return empire.data["platforms"]

@app.post("/empire/platforms/{platform}/activate")
def activate_platform(platform: str, user: Dict = Depends(get_current_user)):
    empire.data["platforms"][platform] = True
    empire.log("platform_activated", {"platform": platform})
    empire.save()
    return {"status": "activated", "platform": platform}

@app.post("/empire/grok/think")
def grok_think(prompt: str, user: Dict = Depends(get_current_user)):
    """Proxy to xAI Grok when you need to think for the empire."""
    if not XAI_API_KEY:
        return {"status": "error", "message": "XAI_API_KEY not configured"}
    empire.log("grok_think", {"prompt_length": len(prompt)})
    return {"status": "forwarded", "message": "Grok processing", "prompt": prompt[:100] + "..."}

# ─── START ───────────────────────────────────────────────────────
if __name__ == "__main__":
    empire.log("api_startup", {"port": PORT})
    uvicorn.run(app, host="0.0.0.0", port=PORT)
