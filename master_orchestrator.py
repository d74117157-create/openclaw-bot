#!/usr/bin/env python3
"""
OpenClaw Superswarm v3.0 — Master Orchestrator
Entry point. Boots the empire. Runs 24/7.
"""
import os
import sys
import asyncio
import json
import threading
import time
from datetime import datetime

# ─── ENVIRONMENT ─────────────────────────────────────────────────
PORT = int(os.getenv("PORT", 10000))
EMPIRE_STATE_PATH = os.getenv("EMPIRE_STATE_PATH", "/tmp/empire-state.json")

# ─── IMPORT EMPIRE MODULES ──────────────────────────────────────
from assets.fastapi_superswarm_api import app, empire, uvicorn
from superswarm import SuperswarmCore
from product_factory import ProductFactory
from platform_engine import PlatformEngine
from marketing_engine import MarketingEngine

# ─── MASTER ORCHESTRATOR ────────────────────────────────────────
class MasterOrchestrator:
    def __init__(self):
        self.swarm = SuperswarmCore()
        self.factory = ProductFactory()
        self.platforms = PlatformEngine()
        self.marketing = MarketingEngine()
        self.running = False
        self.boot_time = datetime.utcnow()

    def boot(self):
        """Boot sequence. Called once on startup."""
        print("=" * 60)
        print("  OPENCLAW SUPERSWARM v3.0 — BOOT SEQUENCE")
        print("=" * 60)

        # 1. Initialize state
        empire.log("boot_sequence", {"phase": "init"})
        self._ensure_state()

        # 2. Load platforms
        print("[BOOT] Activating platform engines...")
        self.platforms.boot()
        empire.log("boot_sequence", {"phase": "platforms"})

        # 3. Initialize swarm
        print("[BOOT] Waking swarm agents...")
        self.swarm.boot()
        empire.log("boot_sequence", {"phase": "swarm"})

        # 4. Start marketing engine
        print("[BOOT] Starting marketing engine...")
        self.marketing.boot()
        empire.log("boot_sequence", {"phase": "marketing"})

        # 5. Start background loops
        print("[BOOT] Spawning background workers...")
        self.running = True
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._revenue_loop, daemon=True).start()
        threading.Thread(target=self._content_loop, daemon=True).start()

        empire.log("boot_complete", {"timestamp": datetime.utcnow().isoformat()})
        print("[BOOT] Empire online. All systems nominal.")
        print("=" * 60)

    def _ensure_state(self):
        os.makedirs(os.path.dirname(EMPIRE_STATE_PATH), exist_ok=True)
        if not os.path.exists(EMPIRE_STATE_PATH):
            empire.save()

    def _heartbeat_loop(self):
        """Every 60s: ping health, log alive status."""
        while self.running:
            time.sleep(60)
            empire.log("heartbeat", {"uptime": str(datetime.utcnow() - self.boot_time)})

    def _revenue_loop(self):
        """Every 5 min: aggregate revenue streams."""
        while self.running:
            time.sleep(300)
            self.marketing.aggregate_revenue()
            empire.save()

    def _content_loop(self):
        """Every 10 min: process content queue."""
        while self.running:
            time.sleep(600)
            self.marketing.process_content_queue()
            empire.save()


    def init_empire(self):
        """Alias for boot(). Called by main.py."""
        self.boot()

    def run_daily_cycle(self):
        """Run one daily empire cycle."""
        print("[CYCLE] Running daily cycle...")
        self.marketing.process_content_queue()
        revenue = self.marketing.aggregate_revenue()
        print(f"[CYCLE] Revenue status: {revenue}")
        self.swarm.auto_heal()
        print("[CYCLE] Daily cycle complete.")

    def shutdown(self):
        self.running = False
        empire.log("shutdown", {"timestamp": datetime.utcnow().isoformat()})
        empire.save()
        print("[SHUTDOWN] Empire state saved. Goodbye, Colonel.")

# ─── MAIN ───────────────────────────────────────────────────────

# ─── Singleton getter ───────────────────────────────────────────
_master_orchestrator_instance = None

def get_master_orchestrator():
    global _master_orchestrator_instance
    if _master_orchestrator_instance is None:
        _master_orchestrator_instance = MasterOrchestrator()
    return _master_orchestrator_instance

if __name__ == "__main__":
    orchestrator = MasterOrchestrator()

    # Boot in background thread so FastAPI can take main thread
    boot_thread = threading.Thread(target=orchestrator.boot, daemon=True)
    boot_thread.start()

    # Start FastAPI server (this blocks)
    print(f"[MAIN] Starting FastAPI on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
