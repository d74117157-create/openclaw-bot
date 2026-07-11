"""
Swarm Risk Manager — prevents catastrophic losses.
All trades route through here before execution.
"""
import os


class RiskManager:
    def __init__(self):
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS_USD", "100.0"))
        self.max_drawdown_pct = float(os.getenv("MAX_DRAWDOWN_PCT", "5.0"))
        self.daily_pnl = 0.0
        self.peak_balance = 0.0

    def check_trade(self, trader, symbol: str, side: str, qty: float, price: float) -> dict:
        """Returns {'approved': bool, 'reason': str}"""
        notional = qty * price

        # Hard stops
        if notional > 10000 and os.getenv("TRADE_TIER") != "pro":
            return {"approved": False, "reason": "Notional > $10k requires pro tier"}

        if self.daily_pnl <= -self.max_daily_loss:
            return {"approved": False, "reason": f"Daily loss limit hit: ${self.daily_pnl:.2f}"}

        return {"approved": True, "reason": "All checks passed"}

    def update_pnl(self, trade_result: dict):
        pnl = trade_result.get("pnl", 0)
        self.daily_pnl += pnl
