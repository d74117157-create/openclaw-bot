"""
BUSINESS AUTOMATION ENGINE
Digital Empire — Operations & Revenue Management
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("openclaw.business")

BUSINESS_STATE_PATH = os.getenv("BUSINESS_STATE_PATH", "/data/business-state.json")

class BusinessAutomation:
    """
    Automates business operations:
    - Product research
    - Marketing workflows
    - Customer support
    - Revenue tracking
    - Financial reporting
    """

    def __init__(self, ai_client=None):
        self.ai = ai_client
        self.state = self._load_state()
        if not self.state:
            self.state = {
                "version": "1.0",
                "products": [],
                "clients": {},
                "campaigns": [],
                "transactions": [],
                "monthly_targets": {
                    "month_1": 500.0,
                    "month_3": 2000.0,
                    "month_6": 10000.0,
                    "month_12": 50000.0,
                },
                "automations": {
                    "product_research": {"enabled": True, "frequency_hours": 24},
                    "marketing_campaigns": {"enabled": True, "frequency_hours": 72},
                    "customer_followup": {"enabled": True, "frequency_hours": 48},
                    "revenue_reporting": {"enabled": True, "frequency_hours": 168},
                },
                "created_at": datetime.utcnow().isoformat(),
            }
            self._save_state()

    def _load_state(self):
        if os.path.exists(BUSINESS_STATE_PATH):
            try:
                with open(BUSINESS_STATE_PATH, "r") as f:
                    return json.load(f)
            except:
                return None
        return None

    def _save_state(self):
        os.makedirs(os.path.dirname(BUSINESS_STATE_PATH), exist_ok=True)
        with open(BUSINESS_STATE_PATH, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    # ─── PRODUCT RESEARCH ────────────────────────────────────────

    def research_products(self, niche: str = "digital products") -> List[Dict]:
        """Research profitable products in a niche."""
        if not self.ai:
            return [{"error": "AI client not available"}]

        # In production: Call AI for real research
        products = [
            {
                "name": f"{niche.title()} Starter Kit",
                "type": "digital",
                "price": 27.0,
                "cost": 0.0,
                "margin": 1.0,
                "demand_score": 8,
                "competition_score": 6,
                "recommendation": "high",
            },
            {
                "name": f"{niche.title()} Pro Template",
                "type": "template",
                "price": 47.0,
                "cost": 0.0,
                "margin": 1.0,
                "demand_score": 7,
                "competition_score": 5,
                "recommendation": "high",
            },
            {
                "name": f"{niche.title()} Masterclass",
                "type": "course",
                "price": 97.0,
                "cost": 0.0,
                "margin": 1.0,
                "demand_score": 9,
                "competition_score": 7,
                "recommendation": "medium",
            },
        ]

        self.state["products"].extend(products)
        self._save_state()
        return products

    # ─── MARKETING WORKFLOWS ───────────────────────────────────

    def create_campaign(self, name: str, channel: str, budget: float, target: str) -> Dict:
        """Create a marketing campaign."""
        campaign = {
            "id": f"camp_{len(self.state['campaigns'])}",
            "name": name,
            "channel": channel,  # telegram, discord, youtube, email
            "budget": budget,
            "target_audience": target,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "launched_at": None,
            "metrics": {"impressions": 0, "clicks": 0, "conversions": 0, "revenue": 0.0},
        }
        self.state["campaigns"].append(campaign)
        self._save_state()
        return campaign

    def launch_campaign(self, campaign_id: str):
        """Launch a marketing campaign."""
        for camp in self.state["campaigns"]:
            if camp["id"] == campaign_id:
                camp["status"] = "live"
                camp["launched_at"] = datetime.utcnow().isoformat()
                self._save_state()
                print(f"[BUSINESS] Launched campaign: {camp['name']}")
                return camp
        return {"error": "Campaign not found"}

    # ─── CUSTOMER SUPPORT ──────────────────────────────────────

    def add_client(self, client_id: str, name: str, email: str, tier: str = "free"):
        """Add a new client."""
        self.state["clients"][client_id] = {
            "name": name,
            "email": email,
            "tier": tier,  # free, basic, pro, enterprise
            "joined_at": datetime.utcnow().isoformat(),
            "lifetime_value": 0.0,
            "transactions": [],
            "last_contact": None,
        }
        self._save_state()

    def record_transaction(self, client_id: str, amount: float, product: str, channel: str):
        """Record a customer transaction."""
        tx = {
            "timestamp": datetime.utcnow().isoformat(),
            "amount": amount,
            "product": product,
            "channel": channel,
        }
        self.state["transactions"].append(tx)
        self.state["transactions"] = self.state["transactions"][-500:]

        if client_id in self.state["clients"]:
            self.state["clients"][client_id]["transactions"].append(tx)
            self.state["clients"][client_id]["lifetime_value"] += amount
            self.state["clients"][client_id]["last_contact"] = datetime.utcnow().isoformat()

        self._save_state()
        print(f"[BUSINESS] +${amount:.2f} | {product} | Client: {client_id}")

    # ─── FINANCIAL REPORTING ───────────────────────────────────

    def generate_monthly_report(self) -> Dict:
        """Generate monthly business report."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_tx = [t for t in self.state["transactions"]
                      if datetime.fromisoformat(t["timestamp"]) >= month_start]

        revenue = sum(t["amount"] for t in monthly_tx)

        # Check targets
        month_num = (now - datetime.fromisoformat(self.state["created_at"])).days // 30
        target_key = f"month_{min(month_num, 12)}"
        target = self.state["monthly_targets"].get(target_key, 50000.0)

        return {
            "period": month_start.strftime("%Y-%m"),
            "revenue": revenue,
            "target": target,
            "progress_pct": (revenue / target * 100) if target > 0 else 0,
            "transactions": len(monthly_tx),
            "active_clients": len(self.state["clients"]),
            "live_campaigns": len([c for c in self.state["campaigns"] if c["status"] == "live"]),
            "status": "on_track" if revenue >= target else "behind",
        }

    def boot(self):
        print("💼 Business Automation Engine Ready")
        print(f"   Products researched: {len(self.state['products'])}")
        print(f"   Clients: {len(self.state['clients'])}")
        print(f"   Campaigns: {len(self.state['campaigns'])}")
        print(f"   Transactions: {len(self.state['transactions'])}")
