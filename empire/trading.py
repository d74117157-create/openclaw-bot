"""Empire Trading Engine - 24/7 automated trading with hard stops and risk boundaries.

Integrates with:
- freqtrade (crypto strategy execution)
- Binance/Alpaca APIs (direct execution)
- Claude AI (strategy generation & analysis)
- OpenClaw swarm (monitoring & alerts)
"""
import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import anthropic

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

class TradingMode(Enum):
    PAPER = "paper"      # Simulate trades
    LIVE = "live"        # Real money
    DRY = "dry_run"      # freqtrade dry-run

@dataclass
class RiskConfig:
    """Hard boundaries for trading."""
    max_daily_loss_pct: float = 5.0          # Stop all trading if down 5% in a day
    max_position_pct: float = 20.0           # No single position > 20% of portfolio
    max_open_positions: int = 5               # Max concurrent trades
    stop_loss_pct: float = 3.0                # Hard stop on every trade
    take_profit_pct: float = 6.0              # Auto take profit
    trailing_stop_pct: float = 2.0            # Lock in profits
    max_trades_per_hour: int = 3              # Rate limiting
    blacklist: List[str] = None               # Banned pairs

    def __post_init__(self):
        if self.blacklist is None:
            self.blacklist = ["SHIB", "PEPE", "FLOKI", "DOGE"]  # Avoid meme rugs

@dataclass
class TradeSignal:
    """AI-generated or strategy-generated trade signal."""
    pair: str
    direction: str  # "long" or "short"
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float  # 0.0 - 1.0
    strategy: str
    timestamp: str
    reason: str

@dataclass
class Position:
    """Active position tracking."""
    id: str
    pair: str
    direction: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    trailing_stop: Optional[float] = None
    opened_at: str = ""
    pnl_pct: float = 0.0
    status: str = "open"  # open, closed, stopped

# ── Risk Guardian ───────────────────────────────────────────────────────────

class RiskGuardian:
    """Enforces hard stops and boundaries. Runs 24/7."""

    def __init__(self, config: RiskConfig):
        self.config = config
        self.daily_pnl = 0.0
        self.daily_reset = datetime.utcnow().date()
        self.positions: Dict[str, Position] = {}
        self.trade_count_hour = 0
        self.hour_reset = datetime.utcnow().hour
        self.lock = asyncio.Lock()

    async def check_boundaries(self, signal: TradeSignal, portfolio_value: float) -> tuple[bool, str]:
        """Returns (allowed, reason) — hard stops."""
        async with self.lock:
            # Reset daily counter if new day
            today = datetime.utcnow().date()
            if today != self.daily_reset:
                self.daily_pnl = 0.0
                self.daily_reset = today

            # Reset hourly counter if new hour
            hour = datetime.utcnow().hour
            if hour != self.hour_reset:
                self.trade_count_hour = 0
                self.hour_reset = hour

            # 1. Daily loss limit
            if self.daily_pnl <= -self.config.max_daily_loss_pct:
                return False, f"DAILY LOSS LIMIT HIT: {self.daily_pnl:.2f}%"

            # 2. Max positions
            open_count = sum(1 for p in self.positions.values() if p.status == "open")
            if open_count >= self.config.max_open_positions:
                return False, f"MAX POSITIONS: {open_count}/{self.config.max_open_positions}"

            # 3. Position size
            position_value = signal.entry_price * (portfolio_value * 0.1)  # 10% default sizing
            if position_value / portfolio_value * 100 > self.config.max_position_pct:
                return False, f"POSITION SIZE EXCEEDS {self.config.max_position_pct}%"

            # 4. Blacklist
            base = signal.pair.replace("/", "").replace("USDT", "").replace("USD", "")
            if any(b.lower() in base.lower() for b in self.config.blacklist):
                return False, f"BLACKLISTED: {signal.pair}"

            # 5. Rate limit
            if self.trade_count_hour >= self.config.max_trades_per_hour:
                return False, f"RATE LIMIT: {self.trade_count_hour}/hour"

            # 6. Confidence floor
            if signal.confidence < 0.6:
                return False, f"LOW CONFIDENCE: {signal.confidence:.2f}"

            return True, "PASS"

    async def add_position(self, position: Position):
        async with self.lock:
            self.positions[position.id] = position
            self.trade_count_hour += 1

    async def update_pnl(self, position_id: str, current_price: float):
        """Update P&L and check hard stops."""
        async with self.lock:
            pos = self.positions.get(position_id)
            if not pos or pos.status != "open":
                return None

            if pos.direction == "long":
                pnl = (current_price - pos.entry_price) / pos.entry_price * 100
            else:
                pnl = (pos.entry_price - current_price) / pos.entry_price * 100

            pos.pnl_pct = pnl
            self.daily_pnl += pnl * (pos.size / 100)  # Approximate

            # Check hard stop
            if pnl <= -self.config.stop_loss_pct:
                pos.status = "stopped"
                return {"action": "CLOSE", "reason": f"STOP LOSS: {pnl:.2f}%", "position": pos}

            # Check take profit
            if pnl >= self.config.take_profit_pct:
                pos.status = "closed"
                return {"action": "CLOSE", "reason": f"TAKE PROFIT: {pnl:.2f}%", "position": pos}

            # Trailing stop (lock in profits)
            if pnl > 0:
                new_trailing = current_price * (1 - self.config.trailing_stop_pct / 100) if pos.direction == "long" else current_price * (1 + self.config.trailing_stop_pct / 100)
                if pos.trailing_stop is None or (pos.direction == "long" and new_trailing > pos.trailing_stop) or (pos.direction == "short" and new_trailing < pos.trailing_stop):
                    pos.trailing_stop = new_trailing

            if pos.trailing_stop and ((pos.direction == "long" and current_price <= pos.trailing_stop) or (pos.direction == "short" and current_price >= pos.trailing_stop)):
                pos.status = "closed"
                return {"action": "CLOSE", "reason": f"TRAILING STOP: {pnl:.2f}%", "position": pos}

            return {"action": "HOLD", "pnl": pnl}

# ── Exchange Connectors ─────────────────────────────────────────────────────

class ExchangeConnector:
    """Abstract exchange connector. Implement for Binance, Alpaca, etc."""

    async def get_price(self, pair: str) -> float:
        raise NotImplementedError

    async def place_order(self, pair: str, side: str, size: float, order_type: str = "market") -> dict:
        raise NotImplementedError

    async def close_position(self, pair: str) -> dict:
        raise NotImplementedError

    async def get_balance(self) -> dict:
        raise NotImplementedError

class BinanceConnector(ExchangeConnector):
    """Binance spot/futures connector."""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def get_price(self, pair: str) -> float:
        url = f"{self.base_url}/api/v3/ticker/price?symbol={pair.replace('/', '')}"
        async with self.session.get(url) as resp:
            data = await resp.json()
            return float(data["price"])

    async def get_balance(self) -> dict:
        # Simplified — real implementation needs signed request
        return {"USDT": 10000.0, "BTC": 0.5}

    async def place_order(self, pair: str, side: str, size: float, order_type: str = "market") -> dict:
        logger.info(f"[BINANCE] {side.upper()} {size} {pair}")
        return {"status": "filled", "order_id": f"sim_{datetime.utcnow().timestamp()}", "price": 0.0}

    async def close_position(self, pair: str) -> dict:
        logger.info(f"[BINANCE] CLOSE {pair}")
        return {"status": "closed"}

# ── Freqtrade Integration ───────────────────────────────────────────────────

class FreqtradeIntegration:
    """Bridge to freqtrade REST API for strategy execution."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def get_status(self) -> dict:
        async with self.session.get(f"{self.base_url}/api/v1/status") as resp:
            return await resp.json()

    async def start_bot(self):
        async with self.session.post(f"{self.base_url}/api/v1/start") as resp:
            return await resp.json()

    async def stop_bot(self):
        async with self.session.post(f"{self.base_url}/api/v1/stop") as resp:
            return await resp.json()

    async def get_profit(self) -> dict:
        async with self.session.get(f"{self.base_url}/api/v1/profit") as resp:
            return await resp.json()

    async def force_exit(self, trade_id: str):
        async with self.session.post(f"{self.base_url}/api/v1/trades/{trade_id}/force_exit") as resp:
            return await resp.json()

# ── Claude Strategy Generator ───────────────────────────────────────────────

class ClaudeStrategyEngine:
    """Uses Claude to generate and analyze trading strategies."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        )

    async def generate_signal(self, market_data: dict, strategy_type: str = "momentum") -> TradeSignal:
        """Ask Claude to analyze market data and generate a trade signal."""
        prompt = f"""Analyze this market data and generate a trading signal.

Market Data:
{json.dumps(market_data, indent=2)}

Strategy Type: {strategy_type}

Rules:
- Only suggest trades with clear technical rationale
- Always specify exact stop loss and take profit levels
- Confidence must be 0.0-1.0 based on signal strength
- Avoid meme coins and low-liquidity pairs
- Consider trend direction, volume, support/resistance

Respond in this exact JSON format:
{{
  "pair": "BTC/USDT",
  "direction": "long",
  "entry_price": 45000.00,
  "stop_loss": 43650.00,
  "take_profit": 47700.00,
  "confidence": 0.82,
  "reason": "Bullish breakout above resistance with volume confirmation"
}}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system="You are an elite quantitative trading analyst. You only output valid JSON.",
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            text = response.content[0].text
            # Extract JSON from markdown if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())
            return TradeSignal(
                pair=data["pair"],
                direction=data["direction"],
                entry_price=data["entry_price"],
                stop_loss=data["stop_loss"],
                take_profit=data["take_profit"],
                confidence=data["confidence"],
                strategy=strategy_type,
                timestamp=datetime.utcnow().isoformat(),
                reason=data["reason"]
            )
        except Exception as e:
            logger.error(f"Claude signal parse error: {e}")
            return None

    async def analyze_portfolio(self, positions: List[Position], balance: dict) -> str:
        """Get Claude's portfolio analysis and recommendations."""
        prompt = f"""Analyze this portfolio and provide actionable recommendations.

Positions:
{json.dumps([asdict(p) for p in positions], indent=2)}

Balance:
{json.dumps(balance, indent=2)}

Provide:
1. Risk assessment
2. Position sizing recommendations
3. Market outlook
4. Specific actions to take (hold/close/hedge)
"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system="You are a portfolio risk manager. Be concise and actionable.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

# ── Empire Trading Orchestrator ─────────────────────────────────────────────

class EmpireTradingOrchestrator:
    """24/7 trading engine integrated with OpenClaw swarm."""

    def __init__(self):
        self.risk = RiskGuardian(RiskConfig())
        self.claude = ClaudeStrategyEngine()
        self.exchange: Optional[ExchangeConnector] = None
        self.freqtrade: Optional[FreqtradeIntegration] = None
        self.mode = TradingMode(os.environ.get("TRADING_MODE", "paper"))
        self.running = False
        self.positions: Dict[str, Position] = {}
        self.watchlist = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT"]

    async def initialize(self):
        """Start connectors based on mode."""
        if self.mode == TradingMode.LIVE:
            binance_key = os.environ.get("BINANCE_API_KEY", "")
            binance_secret = os.environ.get("BINANCE_API_SECRET", "")
            if not binance_key or not binance_secret:
                logger.warning("Binance keys missing — falling back to paper mode")
                self.mode = TradingMode.PAPER
            else:
                self.exchange = BinanceConnector(binance_key, binance_secret, testnet=False)
                await self.exchange.__aenter__()
        elif self.mode == TradingMode.PAPER:
            self.exchange = BinanceConnector("test", "test", testnet=True)
            await self.exchange.__aenter__()

        # freqtrade optional integration
        freqtrade_url = os.environ.get("FREQTRADE_URL", "")
        if freqtrade_url:
            self.freqtrade = FreqtradeIntegration(freqtrade_url)
            await self.freqtrade.__aenter__()

        self.running = True
        logger.info(f"[EMPIRE TRADING] Initialized in {self.mode.value} mode")

    async def shutdown(self):
        self.running = False
        if self.exchange:
            await self.exchange.__aexit__()
        if self.freqtrade:
            await self.freqtrade.__aexit__()

    async def scan_and_trade(self):
        """Main loop: scan markets, generate signals, execute with hard stops."""
        while self.running:
            try:
                for pair in self.watchlist:
                    await self._evaluate_pair(pair)
                    await asyncio.sleep(2)  # Rate limit between pairs

                # Check existing positions for hard stops
                await self._check_positions()

                # Portfolio analysis every hour
                if datetime.utcnow().minute == 0:
                    await self._portfolio_report()

                await asyncio.sleep(30)  # Scan every 30 seconds

            except Exception as e:
                logger.error(f"[TRADING LOOP] {e}")
                await asyncio.sleep(60)

    async def _evaluate_pair(self, pair: str):
        """Evaluate a single pair for trade signals."""
        if not self.exchange:
            return

        try:
            price = await self.exchange.get_price(pair)

            # Simple market data for Claude
            market_data = {
                "pair": pair,
                "price": price,
                "timestamp": datetime.utcnow().isoformat(),
                "mode": self.mode.value
            }

            signal = await self.claude.generate_signal(market_data, "momentum")
            if not signal:
                return

            # Risk check
            balance = await self.exchange.get_balance()
            portfolio_value = sum(balance.values())
            allowed, reason = await self.risk.check_boundaries(signal, portfolio_value)

            if not allowed:
                logger.info(f"[RISK BLOCK] {pair}: {reason}")
                return

            # Execute
            if self.mode != TradingMode.PAPER:
                logger.info(f"[EXECUTE] {signal.direction.upper()} {pair} @ {signal.entry_price} (conf: {signal.confidence})")
                # Real order would go here
            else:
                logger.info(f"[PAPER] {signal.direction.upper()} {pair} @ {signal.entry_price} (conf: {signal.confidence})")

            # Track position
            pos = Position(
                id=f"{pair}_{datetime.utcnow().timestamp()}",
                pair=pair,
                direction=signal.direction,
                entry_price=signal.entry_price,
                size=portfolio_value * 0.1,  # 10% sizing
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                opened_at=datetime.utcnow().isoformat()
            )
            await self.risk.add_position(pos)
            self.positions[pos.id] = pos

        except Exception as e:
            logger.error(f"[EVALUATE] {pair}: {e}")

    async def _check_positions(self):
        """Monitor all positions and enforce hard stops."""
        for pos_id, pos in list(self.positions.items()):
            if pos.status != "open":
                continue

            try:
                current_price = await self.exchange.get_price(pos.pair)
                result = await self.risk.update_pnl(pos_id, current_price)

                if result and result["action"] == "CLOSE":
                    logger.warning(f"[HARD STOP] {pos.pair}: {result['reason']}")

                    if self.mode != TradingMode.PAPER:
                        await self.exchange.close_position(pos.pair)

                    # Notify swarm
                    await self._notify_swarm(f"🛑 HARD STOP: {pos.pair} — {result['reason']}")

                elif result:
                    logger.debug(f"[POSITION] {pos.pair}: {result['pnl']:.2f}%")

            except Exception as e:
                logger.error(f"[CHECK] {pos.pair}: {e}")

    async def _portfolio_report(self):
        """Generate hourly portfolio report via Claude."""
        try:
            balance = await self.exchange.get_balance()
            open_positions = [p for p in self.positions.values() if p.status == "open"]

            analysis = await self.claude.analyze_portfolio(open_positions, balance)
            logger.info(f"[PORTFOLIO REPORT]\n{analysis}")
            await self._notify_swarm(f"📊 Portfolio Report:\n{analysis[:1000]}")

        except Exception as e:
            logger.error(f"[REPORT] {e}")

    async def _notify_swarm(self, message: str):
        """Send alert to OpenClaw swarm (Discord/Slack/Telegram)."""
        # This will be wired into the main OpenClaw bot dispatch
        logger.info(f"[SWARM ALERT] {message}")

    def get_status(self) -> dict:
        """Return current trading status for API/health checks."""
        open_count = sum(1 for p in self.positions.values() if p.status == "open")
        total_pnl = sum(p.pnl_pct for p in self.positions.values())

        return {
            "mode": self.mode.value,
            "running": self.running,
            "open_positions": open_count,
            "total_positions": len(self.positions),
            "daily_pnl": self.risk.daily_pnl,
            "total_pnl": total_pnl,
            "watchlist": self.watchlist,
            "risk_limits": {
                "max_daily_loss": self.risk.config.max_daily_loss_pct,
                "max_position": self.risk.config.max_position_pct,
                "stop_loss": self.risk.config.stop_loss_pct
            }
        }
