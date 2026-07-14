"""
OpenClaw Memory Core v2.0
Persistent swarm memory with portfolio logging.
Every trade, decision, and agent action is recorded.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import requests

DB_PATH = os.getenv("MEMORY_DB", "./data/swarm_memory.db")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

class SwarmMemory:
    """Central memory for all swarm agents."""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH) if "/" in DB_PATH else ".", exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        """Create all memory tables."""
        c = self.conn.cursor()

        # Agent decisions
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                action TEXT,
                context TEXT,
                result TEXT,
                confidence REAL
            )
        """)

        # Portfolio tracking
        c.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                asset TEXT,
                balance REAL,
                price REAL,
                value_usd REAL,
                source TEXT
            )
        """)

        # Trade history
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exchange TEXT,
                symbol TEXT,
                side TEXT,
                qty REAL,
                price REAL,
                notional REAL,
                pnl REAL,
                status TEXT,
                agent TEXT
            )
        """)

        # Daily P&L
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_pnl (
                date TEXT PRIMARY KEY,
                pnl REAL,
                trades_count INTEGER,
                win_count INTEGER,
                loss_count INTEGER,
                max_drawdown REAL
            )
        """)

        # Swarm events
        c.execute("""
            CREATE TABLE IF NOT EXISTS swarm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                platform TEXT,
                details TEXT
            )
        """)


        # Task execution tracking (v3.1)
        c.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent_name TEXT,
                state_from TEXT,
                state_to TEXT,
                timestamp TEXT,
                reason TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent_name TEXT,
                action TEXT,
                result TEXT,
                success INTEGER,
                timestamp TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS execution_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                agent TEXT,
                receipt_json TEXT,
                verified_by TEXT,
                verification_passed INTEGER,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def log_decision(self, agent: str, action: str, context: str, result: str = "", confidence: float = 0.0):
        """Log any agent decision."""
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO agent_decisions (timestamp, agent_name, action, context, result, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), agent, action, context, result, confidence))
        self.conn.commit()

    def log_portfolio(self, asset: str, balance: float, price: float, source: str = "binance"):
        """Log portfolio snapshot."""
        value = balance * price
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO portfolio (timestamp, asset, balance, price, value_usd, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), asset, balance, price, value, source))
        self.conn.commit()

        # Also sync to Google Sheets if configured
        self._sync_to_sheets("portfolio", {
            "timestamp": datetime.now().isoformat(),
            "asset": asset,
            "balance": balance,
            "price": price,
            "value_usd": value,
            "source": source
        })

    def log_trade(self, exchange: str, symbol: str, side: str, qty: float, price: float, 
                  notional: float, pnl: float = 0.0, status: str = "filled", agent: str = "trader"):
        """Log every trade."""
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO trades (timestamp, exchange, symbol, side, qty, price, notional, pnl, status, agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), exchange, symbol, side, qty, price, notional, pnl, status, agent))
        self.conn.commit()

        self._sync_to_sheets("trades", {
            "timestamp": datetime.now().isoformat(),
            "exchange": exchange,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "notional": notional,
            "pnl": pnl,
            "status": status,
            "agent": agent
        })

    def log_event(self, event_type: str, platform: str, details: str):
        """Log swarm events (bot connects, errors, etc)."""
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO swarm_events (timestamp, event_type, platform, details)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), event_type, platform, details))
        self.conn.commit()

    def get_portfolio_history(self, asset: str = None, limit: int = 100) -> List[Dict]:
        """Get portfolio history for analysis."""
        c = self.conn.cursor()
        if asset:
            c.execute("SELECT * FROM portfolio WHERE asset = ? ORDER BY timestamp DESC LIMIT ?", (asset, limit))
        else:
            c.execute("SELECT * FROM portfolio ORDER BY timestamp DESC LIMIT ?", (limit,))
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get trade history."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,))
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily P&L stats."""
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM daily_pnl 
            WHERE date >= date('now', '-{} days')
            ORDER BY date DESC
        """.format(days))
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def get_swarm_summary(self) -> Dict:
        """Get full swarm summary."""
        c = self.conn.cursor()

        c.execute("SELECT COUNT(*) FROM trades")
        total_trades = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM agent_decisions")
        total_decisions = c.fetchone()[0]

        c.execute("SELECT SUM(pnl) FROM trades")
        total_pnl = c.fetchone()[0] or 0

        c.execute("SELECT asset, SUM(value_usd) as total FROM portfolio GROUP BY asset ORDER BY timestamp DESC")
        latest_portfolio = {row[0]: row[1] for row in c.fetchall()}

        return {
            "total_trades": total_trades,
            "total_decisions": total_decisions,
            "total_pnl": total_pnl,
            "latest_portfolio": latest_portfolio,
            "db_path": DB_PATH,
            "last_update": datetime.now().isoformat()
        }

    def _sync_to_sheets(self, sheet_name: str, row_data: dict):
        """Sync a row to Google Sheets if configured."""
        if not GOOGLE_SHEETS_ID or not GOOGLE_API_KEY:
            return

        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEETS_ID}/values/{sheet_name}!A1:append"
            params = {"valueInputOption": "USER_ENTERED", "key": GOOGLE_API_KEY}
            values = [[str(v) for v in row_data.values()]]
            headers = {"Content-Type": "application/json"}
            requests.post(url, params=params, headers=headers, json={"values": values}, timeout=5)
        except:
            pass  # Don't crash on Sheets sync failure

# Singleton
_memory_instance = None

def get_memory() -> SwarmMemory:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = SwarmMemory()
    return _memory_instance
