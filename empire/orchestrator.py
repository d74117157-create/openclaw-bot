"""
OpenClaw Empire Orchestrator v2.0
Coordinates ALL monetization: trading, content, affiliates, products.
Runs on schedule. Logs everything to memory + Google Sheets.
"""
import os
import asyncio
from datetime import datetime, timedelta

class EmpireOrchestrator:
    def __init__(self):
        self.agents = {}
        self.revenue_streams = []
        self.daily_schedule = None

    async def init_all(self):
        """Initialize ALL monetization agents."""
        from automation.payhip_agent import get_payhip_agent
        from automation.wix_agent import get_wix_agent
        from automation.tiktok_agent import get_tiktok_agent
        from automation.youtube_monetize import get_youtube_monetize_agent
        from automation.affiliate_engine import get_affiliate_engine
        from automation.content_scheduler import get_scheduler
        from worker.agents.trader_binance import BinanceTrader
        from memory.core import get_memory

        self.agents["payhip"] = get_payhip_agent()
        self.agents["wix"] = get_wix_agent()
        self.agents["tiktok"] = get_tiktok_agent()
        self.agents["youtube"] = get_youtube_monetize_agent()
        self.agents["affiliate"] = get_affiliate_engine()
        self.agents["scheduler"] = get_scheduler()
        self.agents["trading"] = BinanceTrader()
        self.agents["memory"] = get_memory()

        print("[EMPIRE] 🏰 ALL monetization agents initialized")

    async def daily_run(self):
        """DAILY EMPIRE AUTOMATION CYCLE — runs every morning."""
        now = datetime.now()
        print(f"\n[EMPIRE] 🌅 DAILY CYCLE: {now.isoformat()}")

        # 1. CONTENT — Generate today's content
        print("[EMPIRE] 🎬 Generating content...")
        today_content = self.agents["scheduler"].get_today_content()
        for platform, items in today_content.items():
            if items:
                print(f"  📌 {platform}: {len(items)} items scheduled")
                for item in items:
                    self.agents["memory"].log_event("content_scheduled", platform, item.get("topic", "unknown"))

        # 2. YOUTUBE — Check stats, plan uploads
        print("[EMPIRE] 📺 YouTube check...")
        try:
            stats = self.agents["youtube"].get_channel_stats()
            subs = stats.get("subscribers", 0)
            views = stats.get("views", 0)
            print(f"  📊 {subs} subs | {views} views")
            self.agents["memory"].log_event("youtube_stats", "youtube", f"subs:{subs} views:{views}")

            # Estimate revenue
            revenue = self.agents["youtube"].estimate_revenue(int(views))
            print(f"  💰 Est. revenue: ${revenue['estimated_revenue']:.2f}")
        except Exception as e:
            print(f"  ⚠️ YouTube check failed: {e}")

        # 3. AFFILIATE — Generate descriptions with links
        print("[EMPIRE] 🔗 Affiliate engine...")
        try:
            desc = self.agents["affiliate"].generate_youtube_description("Daily AI Build")
            print(f"  ✅ Description generated ({len(desc)} chars)")
        except Exception as e:
            print(f"  ⚠️ Affiliate gen failed: {e}")

        # 4. TRADING — Check positions, scan signals
        print("[EMPIRE] 📈 Trading check...")
        try:
            bal = self.agents["trading"].get_balance()
            print(f"  💵 Balance: ${bal.get('total', 0):,.2f} {bal.get('asset', 'USDT')}")

            positions = self.agents["trading"].get_positions()
            print(f"  📊 Positions: {len(positions)}")
        except Exception as e:
            print(f"  ⚠️ Trading check failed: {e}")

        # 5. PRODUCTS — Check Payhip/Wix
        print("[EMPIRE] 🛒 Product check...")
        try:
            report = self.agents["payhip"].get_sales_report()
            print(f"  📦 Payhip: {report.get('products', 0)} products")
        except Exception as e:
            print(f"  ⚠️ Product check failed: {e}")

        # 6. MEMORY — Log daily summary
        summary = self.agents["memory"].get_swarm_summary()
        print(f"[EMPIRE] 🧠 Memory: {summary.get('total_trades', 0)} trades | {summary.get('total_decisions', 0)} decisions")

        print(f"[EMPIRE] ✅ DAILY CYCLE COMPLETE\n")

    async def weekly_run(self):
        """WEEKLY deep analysis — runs Sundays."""
        print("\n[EMPIRE] 📅 WEEKLY ANALYSIS")

        # Generate 30-day content plan
        plan = self.agents["scheduler"].generate_content_plan(days=30)
        total_items = sum(len(v) for v in plan.values())
        print(f"  📋 {total_items} content items planned for next 30 days")

        # Portfolio analysis
        try:
            history = self.agents["memory"].get_portfolio_history(limit=100)
            if history:
                latest = history[0]
                print(f"  📊 Latest portfolio: ${latest.get('value_usd', 0):,.2f}")
        except:
            pass

        print("[EMPIRE] ✅ WEEKLY ANALYSIS COMPLETE\n")

    def get_status(self):
        return {
            "agents": list(self.agents.keys()),
            "revenue_streams": [
                "youtube_adsense",
                "youtube_sponsors",
                "affiliate_commissions",
                "payhip_sales",
                "wix_sales",
                "trading_profits",
                "patreon_subs"
            ],
            "timestamp": datetime.now().isoformat(),
            "mode": "passive_income",
            "next_daily": (datetime.now() + timedelta(days=1)).replace(hour=6, minute=0).isoformat()
        }

def get_empire_orchestrator():
    return EmpireOrchestrator()
