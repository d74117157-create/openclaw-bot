#!/usr/bin/env python3
"""
OpenClaw Trading Signal Bot
Analyzes crypto markets and posts signals to Telegram/Discord.
"""
import os
import json
import requests
from datetime import datetime

BINANCE_API = "https://api.binance.com/api/v3"

def get_price(symbol="BTCUSDT"):
    """Get current price for a symbol"""
    try:
        resp = requests.get(f"{BINANCE_API}/ticker/price?symbol={symbol}", timeout=10)
        return float(resp.json()["price"])
    except Exception as e:
        print(f"[ERROR] Price fetch failed: {e}")
        return None

def get_24h_stats(symbol="BTCUSDT"):
    """Get 24h change statistics"""
    try:
        resp = requests.get(f"{BINANCE_API}/ticker/24hr?symbol={symbol}", timeout=10)
        data = resp.json()
        return {
            "price_change_percent": float(data["priceChangePercent"]),
            "volume": float(data["volume"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
            "quote_volume": float(data["quoteVolume"])
        }
    except Exception as e:
        print(f"[ERROR] 24h stats failed: {e}")
        return None

def analyze_signal(symbol="BTCUSDT"):
    """Generate a trading signal"""
    stats = get_24h_stats(symbol)
    price = get_price(symbol)

    if not stats or not price:
        return None

    change = stats["price_change_percent"]
    volume = stats["quote_volume"]

    # Simple momentum logic
    signal = None
    confidence = 0

    if change > 5 and volume > 1000000000:  # >$1B volume
        signal = "STRONG_BUY"
        confidence = min(95, 70 + abs(change))
    elif change > 2:
        signal = "BUY"
        confidence = min(85, 60 + abs(change))
    elif change < -5 and volume > 1000000000:
        signal = "STRONG_SELL"
        confidence = min(95, 70 + abs(change))
    elif change < -2:
        signal = "SELL"
        confidence = min(85, 60 + abs(change))
    else:
        signal = "HOLD"
        confidence = 50

    return {
        "symbol": symbol,
        "price": price,
        "signal": signal,
        "confidence": confidence,
        "change_24h": change,
        "volume_24h": volume,
        "timestamp": datetime.now().isoformat(),
        "analysis": f"{symbol} at ${price:,.2f}. 24h change: {change:+.2f}%. Volume: ${volume/1e9:.2f}B. Signal: {signal} ({confidence}% confidence)"
    }

def scan_market(symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT"]):
    """Scan multiple symbols and return all signals"""
    print("=" * 50)
    print("OPENCLAW TRADING SIGNAL SCAN")
    print("=" * 50)

    results = []
    for sym in symbols:
        sig = analyze_signal(sym)
        if sig:
            results.append(sig)
            print(f"[{sig['signal']}] {sym}: ${sig['price']:,.2f} ({sig['change_24h']:+.2f}%)")

    # Save to file for tracking
    os.makedirs("data/trading", exist_ok=True)
    with open(f"data/trading/signals_{datetime.now().strftime('%Y%m%d')}.json", "a") as f:
        f.write(json.dumps(results) + "\n")

    print(f"[OK] Scanned {len(results)} symbols. Signals saved.")
    return results

def get_top_opportunity(symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT", "XRPUSDT", "DOTUSDT"]):
    """Get the highest confidence signal"""
    signals = scan_market(symbols)
    if not signals:
        return None

    # Sort by absolute confidence, prioritize non-HOLD
    non_hold = [s for s in signals if s["signal"] != "HOLD"]
    if non_hold:
        return max(non_hold, key=lambda x: x["confidence"])
    return signals[0]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--top":
        opp = get_top_opportunity()
        if opp:
            print(f"\nTOP OPPORTUNITY: {opp['analysis']}")
    else:
        scan_market()
