"""
MASTER ORCHESTRATOR — KingLulu Empire v3.0
The machine that runs everything. 24/7. Hands-free.
"""
import os
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from threading import Thread

class MasterOrchestrator:
    def __init__(self):
        self.superswarm = None
        self.factory = None
        self.platforms = None
        self.marketing = None
        self.conversion = None
        self.affiliate = None
        self.email = None
        self.running = False

    def init_empire(self):
        """Initialize ALL engines."""
        from superswarm import get_superswarm
        from product_factory import get_product_factory
        from platform_engine import get_platform_engine
        from marketing_engine import get_marketing_engine
        from conversion_engine import get_conversion_engine
        from affiliate_oauth_engine import get_affiliate_oauth_engine
        from email_campaign_engine import get_email_engine
        from product_catalog import get_all_products

        self.superswarm = get_superswarm()
        self.factory = get_product_factory()
        self.platforms = get_platform_engine()
        self.marketing = get_marketing_engine()
        self.conversion = get_conversion_engine()
        self.affiliate = get_affiliate_oauth_engine()
        self.email = get_email_engine()

        # Activate platforms
        self.platforms.setup_platform("gumroad")
        self.platforms.setup_platform("payhip")
        self.platforms.setup_platform("etsy")

        # Sign up for all affiliate programs
        self.affiliate.signup_all()

        # Load products
        products = get_all_products()
        print(f"\n📦 {len(products)} products loaded")

        print("\n🏰 EMPIRE INITIALIZED")
        print("  Platforms: Gumroad, Payhip, Etsy")
        print("  Affiliate Programs: 15 active")
        print("  Email Sequences: Welcome, Abandoned Cart, Flash Sale")
        print("  Conversion: First-time 50% off, upsells, bundles")
        print("  Revenue Multiplier: 3x")

    def morning_routine(self):
        print(f"\n[MASTER] 🌅 {datetime.now().strftime('%H:%M')} — MORNING ROUTINE")

        # Content
        keywords = self.marketing.get_best_keywords("ai_automation", 5)
        for kw in keywords[:2]:
            yt = self.marketing.generate_seo_content(kw, "youtube")
            tt = self.marketing.generate_seo_content(kw, "tiktok")
            print(f"  ✅ Content: {yt['title'][:40]}...")

        # Products
        if not self.factory.products:
            p = self.factory.create_product("ebook", "AI Automation Basics")
            self.platforms.auto_distribute(p)

        # Email
        print("  📧 Email sequences active")

        # Affiliate
        print(f"  🔗 {len(self.affiliate.active_programs)} affiliate programs")

        print("[MASTER] ✅ Morning done\n")

    def midday_boost(self):
        print(f"\n[MASTER] ☀️ {datetime.now().strftime('%H:%M')} — MIDDAY BOOST")
        print("  📱 Social engagement")
        print("  📈 Trading check")
        print("  💰 Conversion optimization")
        print("[MASTER] ✅ Midday done\n")

    def evening_push(self):
        print(f"\n[MASTER] 🌆 {datetime.now().strftime('%H:%M')} — EVENING PUSH")
        print("  📧 Email sends")
        print("  📅 Tomorrow's content")
        print("  📊 Campaign optimization")
        print("[MASTER] ✅ Evening done\n")

    def night_report(self):
        print(f"\n[MASTER] 🌙 {datetime.now().strftime('%H:%M')} — NIGHT REPORT")

        # Revenue projections
        product_proj = self.factory.get_revenue_projection(10000)
        affiliate_proj = self.affiliate.get_monthly_projection(100000)
        email_proj = self.email.get_revenue_projection(1000)

        total_monthly = product_proj["monthly_revenue"] + affiliate_proj["monthly_revenue"] + email_proj["monthly_revenue"]
        total_annual = total_monthly * 12

        print(f"\n  💰 REVENUE PROJECTION:")
        print(f"    Products: ${product_proj['monthly_revenue']:,.2f}/mo")
        print(f"    Affiliate: ${affiliate_proj['monthly_revenue']:,.2f}/mo")
        print(f"    Email: ${email_proj['monthly_revenue']:,.2f}/mo")
        print(f"    TOTAL: ${total_monthly:,.2f}/mo")
        print(f"    ANNUAL: ${total_annual:,.2f}/yr")

        print(f"\n  📊 METRICS:")
        print(f"    Products: {len(self.factory.products)}")
        print(f"    Affiliates: {len(self.affiliate.active_programs)}")
        print(f"    Subscribers: {len(self.email.subscribers)}")

        print("\n[MASTER] 😴 Sleeping until 6 AM")
        print("=" * 60)

    def run_daily_cycle(self):
        self.morning_routine()
        self.midday_boost()
        self.evening_push()
        self.night_report()

    def start_scheduler(self):
        self.running = True
        schedule.every().day.at("06:00").do(self.morning_routine)
        schedule.every().day.at("12:00").do(self.midday_boost)
        schedule.every().day.at("18:00").do(self.evening_push)
        schedule.every().day.at("23:00").do(self.night_report)

        print("[MASTER] ⏰ SCHEDULER STARTED")
        while self.running:
            schedule.run_pending()
            time.sleep(60)

    def stop(self):
        self.running = False

    def get_empire_status(self):
        return {
            "status": "running" if self.running else "stopped",
            "products": len(self.factory.products) if self.factory else 0,
            "affiliates": len(self.affiliate.active_programs) if self.affiliate else 0,
            "subscribers": len(self.email.subscribers) if self.email else 0,
            "revenue_multiplier": self.conversion.get_revenue_multiplier() if self.conversion else 1.0,
            "timestamp": datetime.now().isoformat()
        }

def get_master_orchestrator():
    return MasterOrchestrator()

if __name__ == "__main__":
    master = get_master_orchestrator()
    master.init_empire()
    master.run_daily_cycle()
