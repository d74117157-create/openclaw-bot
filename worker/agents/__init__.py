"""OpenClaw agent dispatch."""
from worker.ai_worker import process_task, AGENT_PERSONAS

AGENT_DISPATCH = {
    "coder": lambda t: process_task(t, "coder"),
    "reviewer": lambda t: process_task(t, "reviewer"),
    "qa": lambda t: process_task(t, "qa"),
    "ops": lambda t: process_task(t, "ops"),
    "research": lambda t: process_task(t, "research"),
    "growth": lambda t: process_task(t, "growth"),
    "memory": lambda t: process_task(t, "memory"),
    "github": lambda t: process_task(t, "github"),
    "browser": lambda t: process_task(t, "browser"),
    "orchestrator": lambda t: process_task(t, "orchestrator"),
}

__all__ = ["AGENT_DISPATCH", "AGENT_PERSONAS"]

# Trading agents
from .trader import BaseTrader, get_trader
from .trader_binance import BinanceTrader
from .risk_manager import RiskManager
