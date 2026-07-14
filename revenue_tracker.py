import json
import os
from datetime import datetime
from typing import Dict, List

REVENUE_STATE_PATH = os.getenv("REVENUE_STATE_PATH", "/data/revenue-state.json")

class RevenueTracker:
    """Tracks REAL revenue from Digital Empire operations."""

    REVENUE_STREAMS = {
        "telegram_saas": "Monthly subscriptions to Telegram bots",
        "digital_products": "Ebooks, templates, code, courses sold",
        "youtube_adsense": "YouTube AdSense revenue",
        "affiliate_commissions": "Affiliate marketing commissions",
        "discord_premium": "Paid Discord community memberships",
        "ai_services": "Custom AI content/code generation",
        "sponsorships": "Brand sponsorships and partnerships",
        "consulting": "One-on-one consulting sessions",
    }

    def __init__(self):
        self.data = self._load()
        if not self.data:
            self.data = {
                "total_revenue": 0.0,
                "transactions": [],
                "streams": {k: {"total": 0.0, "count": 0, "description": v} 
                           for k, v in self.REVENUE_STREAMS.items()},
                "pending_payments": [],
                "clients": {},
                "monthly_targets": {
                    "month_1": 500.0,
                    "month_3": 2000.0,
                    "month_6": 10000.0,
                    "month_12": 20000.0,
                },
                "created_at": datetime.utcnow().isoformat(),
            }
            self._save()

    def _load(self):
        if os.path.exists(REVENUE_STATE_PATH):
            try:
                with open(REVENUE_STATE_PATH, "r") as f:
                    return json.load(f)
            except:
                return None
        return None

    def _save(self):
        os.makedirs(os.path.dirname(REVENUE_STATE_PATH), exist_ok=True)
        with open(REVENUE_STATE_PATH, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def record_sale(self, stream: str, amount: float, client: str, description: str):
        """Record a REAL sale."""
        tx = {
            "timestamp": datetime.utcnow().isoformat(),
            "stream": stream,
            "amount": amount,
            "client": client,
            "description": description,
        }
        self.data["transactions"].append(tx)
        self.data["transactions"] = self.data["transactions"][-500:]

        self.data["total_revenue"] += amount
        if stream in self.data["streams"]:
            self.data["streams"][stream]["total"] += amount
            self.data["streams"][stream]["count"] += 1

        if client not in self.data["clients"]:
            self.data["clients"][client] = {"total": 0.0, "transactions": 0}
        self.data["clients"][client]["total"] += amount
        self.data["clients"][client]["transactions"] += 1

        self._save()
        print(f"[REVENUE] +${amount:.2f} | {stream} | Client: {client}")

    def get_report(self) -> Dict:
        return {
            "total_revenue": self.data["total_revenue"],
            "streams": self.data["streams"],
            "client_count": len(self.data["clients"]),
            "transaction_count": len(self.data["transactions"]),
            "monthly_progress": self.data["monthly_targets"],
        }

    def boot(self):
        print("[REVENUE] Digital Empire Tracker Ready")
        print(f"  Total Revenue: ${self.data['total_revenue']:.2f}")
        for stream, data in self.data["streams"].items():
            if data["count"] > 0:
                print(f"  {stream}: ${data['total']:.2f} ({data['count']} sales)")
