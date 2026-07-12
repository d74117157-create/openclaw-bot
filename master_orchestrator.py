#!/usr/bin/env python3
"""
OpenClaw Superswarm v3.2 — Master Orchestrator
Boots FastAPI + Real Bot Swarm + AI Brain + Revenue Engines
"""
import os, sys, asyncio, json, threading, time
from datetime import datetime

PORT = int(os.getenv("PORT", 10000))
EMPIRE_STATE_PATH = os.getenv("EMPIRE_STATE_PATH", "/tmp/empire-state.json")

from assets.fastapi_superswarm_api import app, empire, uvicorn
from core.swarm_orchestrator import SwarmOrchestrator
from core.config import settings
from youtube_engine import YouTubeEngine
from binance_engine import BinancePaperTrader
from revenue_tracker import RevenueTracker
from ai_brain import get_brain

class MasterOrchestrator:
    def __init__(self):
        self.running = False
        self.boot_time = datetime.utcnow()
        self.swarm_orchestrator = SwarmOrchestrator()
        self.youtube = YouTubeEngine()
        self.trader = BinancePaperTrader()
        self.revenue = RevenueTracker()
        self.brain = get_brain()

    def boot(self):
        print("=" * 60)
        print("  OPENCLAW SUPERSWARM v3.2 — BOOT SEQUENCE")
        print("=" * 60)

        empire.log("boot_sequence", {"phase": "init"})

        # Boot AI brain first
        print("[BOOT] Initializing AI brain...")
        if self.brain.is_configured():
            print(f"[BOOT] AI brain online. Primary: {self.brain.primary}")
            empire.log("ai_brain", {"status": "online", "primary": self.brain.primary})
        else:
            print("[BOOT] ⚠️ No AI brain configured. Set GROQ_API_KEY or GROK_API_KEY")
            empire.log("ai_brain", {"status": "offline"})

        self.revenue.boot()
        self.trader.boot()
        self.youtube.boot()

        self.running = True
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._revenue_loop, daemon=True).start()
        threading.Thread(target=self._trading_loop, daemon=True).start()
        threading.Thread(target=self._youtube_loop, daemon=True).start()
        threading.Thread(target=self._run_swarm, daemon=True).start()

        empire.log("boot_complete", {"timestamp": datetime.utcnow().isoformat()})
        print("[BOOT] Empire online. All systems nominal.")
        print("=" * 60)

        print(f"[MAIN] Starting FastAPI health server on port {PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)

    def _run_swarm(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.swarm_orchestrator.start())
        except Exception as e:
            print(f"[SWARM] Error: {e}")
            empire.log("swarm_error", {"error": str(e)})

    def _heartbeat_loop(self):
        while self.running:
            time.sleep(60)
            empire.log("heartbeat", {
                "uptime": str(datetime.utcnow() - self.boot_time),
                "ai_calls": self.brain.total_calls,
                "ai_failures": self.brain.failed_calls
            })

    def _revenue_loop(self):
        while self.running:
            time.sleep(300)
            self.revenue.aggregate()
            empire.save()

    def _trading_loop(self):
        while self.running:
            time.sleep(900)
            try:
                self.trader.run_strategy()
                empire.data["trading"] = self.trader.get_status()
                empire.save()
            except Exception as e:
                empire.log("trading_error", {"error": str(e)})

    def _youtube_loop(self):
        while self.running:
            time.sleep(1800)
            try:
                self.youtube.run_automation()
                empire.log("youtube_automation", {"status": "completed"})
            except Exception as e:
                empire.log("youtube_error", {"error": str(e)})

    def shutdown(self):
        self.running = False
        empire.log("shutdown", {"timestamp": datetime.utcnow().isoformat()})
        empire.save()

if __name__ == "__main__":
    MasterOrchestrator().boot()
