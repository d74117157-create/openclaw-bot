"""
Binance Spot & Futures Trader
Docs: https://binance-docs.github.io/apidocs/
"""
import hmac
import hashlib
import time
import requests
from .trader import BaseTrader


class BinanceTrader(BaseTrader):
    def __init__(self):
        super().__init__("binance")
        self.base_url = "https://testnet.binance.vision" if self.paper else "https://api.binance.com"
        # For futures: https://fapi.binance.com
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params: dict) -> str:
        query = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode(),
            query.encode(),
            hashlib.sha256
        ).hexdigest()

    def get_balance(self) -> dict:
        if not self.api_key:
            return {"total": 10000.0, "free": 10000.0, "asset": "USDT"}  # Paper default

        params = {"timestamp": int(time.time() * 1000)}
        params["signature"] = self._sign(params)
        r = self.session.get(f"{self.base_url}/api/v3/account", params=params)
        if r.status_code == 200:
            balances = {b["asset"]: float(b["free"]) for b in r.json()["balances"]}
            return {"total": balances.get("USDT", 0), "free": balances.get("USDT", 0), "asset": "USDT"}
        return {"total": 0, "free": 0, "error": r.text}

    def get_price(self, symbol: str) -> float:
        symbol = symbol.upper().replace("/", "")
        r = requests.get(f"{self.base_url}/api/v3/ticker/price", params={"symbol": symbol})
        if r.status_code == 200:
            return float(r.json()["price"])
        # Fallback for paper
        return 50000.0 if "BTC" in symbol else 2500.0

    def place_order(self, symbol, side, qty, order_type="market", price=None):
        symbol = symbol.upper().replace("/", "")
        current_price = self.get_price(symbol)

        if not self.risk_check(symbol, qty, current_price):
            return {"status": "rejected", "reason": "risk_check_failed"}

        if self.paper:
            self.log(f"📊 PAPER ORDER: {side.upper()} {qty} {symbol} @ {current_price}")
            trade = {
                "symbol": symbol, "side": side, "qty": qty,
                "price": current_price, "notional": qty * current_price,
                "status": "paper_filled"
            }
            self.active_positions.append(trade)
            return trade

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": qty,
            "timestamp": int(time.time() * 1000)
        }
        if order_type == "limit" and price:
            params["price"] = price
            params["timeInForce"] = "GTC"

        params["signature"] = self._sign(params)
        r = self.session.post(f"{self.base_url}/api/v3/order", params=params)
        self.log(f"Order response: {r.status_code}")
        return r.json()

    def get_positions(self):
        return self.active_positions
