"""
OpenClaw Trading Agent — Base Class
Wires into the swarm via the Orchestrator.
"""
import os
import json
import hmac
import hashlib
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import requests


class BaseTrader(ABC):
    def __init__(self, name: str):
        self.name = name
        self.api_key = os.getenv(f"{name.upper()}_API_KEY", "")
        self.api_secret = os.getenv(f"{name.upper()}_API_SECRET", "")
        self.paper = os.getenv(f"{name.upper()}_PAPER", "true").lower() == "true"
        self.risk_pct = float(os.getenv("TRADE_RISK_PCT", "1.0"))  # % of balance per trade
        self.max_positions = int(os.getenv("TRADE_MAX_POSITIONS", "3"))
        self.active_positions: List[Dict] = []

    def log(self, msg: str):
        print(f"[{self.name}] {'[PAPER]' if self.paper else '[LIVE]'} {msg}")

    @abstractmethod
    def get_balance(self) -> Dict:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, qty: float, order_type: str = "market", price: Optional[float] = None) -> Dict:
        """
        side: 'buy' | 'sell'
        order_type: 'market' | 'limit' | 'stop_loss'
        """
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        pass

    def risk_check(self, symbol: str, qty: float, price: float) -> bool:
        """Swarm safety gate — prevents reckless trades."""
        notional = qty * price
        balance = self.get_balance().get("total", 0)

        if balance == 0:
            self.log("⚠️ ZERO BALANCE — trade blocked")
            return False

        risk = (notional / balance) * 100
        if risk > self.risk_pct:
            self.log(f"🚫 RISK EXCEEDED: {risk:.2f}% > {self.risk_pct}% max")
            return False

        if len(self.active_positions) >= self.max_positions:
            self.log(f"🚫 MAX POSITIONS: {len(self.active_positions)}/{self.max_positions}")
            return False

        self.log(f"✅ Risk OK: {risk:.2f}% of balance")
        return True


# Swarm integration hook
def get_trader(exchange: str) -> BaseTrader:
    exchange = exchange.lower()
    if exchange == "binance":
        from .trader_binance import BinanceTrader
        return BinanceTrader()
    raise ValueError(f"Unknown exchange: {exchange}")
