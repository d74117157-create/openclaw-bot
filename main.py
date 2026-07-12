"""
SUPERSWARM — KingLulu Digital Empire
Main entry point. Boots everything + keeps FastAPI alive.
"""
import os
import threading
from datetime import datetime

# Import all engines
from superswarm import get_superswarm
from product_factory import get_product_factory
from platform_engine import get_platform_engine
from marketing_engine import get_marketing_engine
from master_orchestrator import get_master_orchestrator
from product_catalog import get_all_products

# FastAPI server import
from assets.fastapi_superswarm_api import app, uvicorn

PORT = int(os.getenv("PORT", 10000))

def boot_empire():
    """Boot the entire empire."""
    print("=" * 60)
    print("🦅 KINGLULU DIGITAL EMPIRE")
    print("Superswarm v3.0 — Money Machine")
    print("=" * 60)

    # Initialize
    master = get_master_orchestrator()
    master.init_empire()

    # Load all 30 products
    products = get_all_products()
    print(f"\n📦 Loaded {len(products)} products")

    # Activate platforms
    master.platforms.setup_platform("gumroad")
    master.platforms.setup_platform("payhip")
    master.platforms.setup_platform("etsy")

    # Run one cycle
    print("\n🚀 Running first cycle...")
    master.run_daily_cycle()

    print("\n✅ EMPIRE BOOTED")
    print("Ready to make money.")

    return master

if __name__ == "__main__":
    # Boot empire in background thread
    boot_thread = threading.Thread(target=boot_empire, daemon=True)
    boot_thread.start()

    # Start FastAPI server (blocks, keeps Render web service alive)
    print(f"[MAIN] Starting FastAPI on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
