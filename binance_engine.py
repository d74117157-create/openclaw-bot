"""
Binance Paper Trading Engine
"""
import os, random
from datetime import datetime

TRADING_MODE = os.getenv("TRADING_MODE", "paper")

class BinancePaperTrader:
    SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

    def __init__(self):
        self.mode = TRADING_MODE
        self.balance = 10000.0
        self.positions = []
        self.trades = []
        self.pnl = 0.0

    def boot(self):
        print(f"[BINANCE] Paper trader ready. Balance: ${self.balance:.2f}")

    def get_status(self):
        return {
            "mode": self.mode, "balance": self.balance,
            "positions": self.positions, "pnl": self.pnl,
            "total_trades": len(self.trades)
        }

    def run_strategy(self):
        if self.mode != "paper":
            print("[BINANCE] Live mode not enabled for safety.")
            return

        symbol = random.choice(self.SYMBOLS)
        action = random.choice(["BUY", "SELL"])
        qty = round(random.uniform(0.01, 0.1), 4)
        price = round(random.uniform(100, 50000), 2)
        value = qty * price

        trade = {
            "symbol": symbol, "side": action, "quantity": qty,
            "price": price, "timestamp": datetime.utcnow().isoformat(), "value": value
        }

        if action == "BUY":
            if self.balance >= value:
                self.balance -= value
                self.positions.append(trade)
                print(f"[BINANCE] PAPER BUY {qty} {symbol} @ ${price}")
            else:
                return
        else:
            matching = [p for p in self.positions if p["symbol"] == symbol]
            if matching:
                pos = matching[0]
                self.positions.remove(pos)
                pnl = (price - pos["price"]) * qty
                self.pnl += pnl
                self.balance += value
                print(f"[BINANCE] PAPER SELL {qty} {symbol} @ ${price} | P&L: ${pnl:.2f}")

        self.trades.append(trade)
        if len(self.positions) > 10:
            self.positions = self.positions[-10:]
