"""
OpenClaw Platform Engine
Connects Discord brain, 3x Telegram bots, Slack, YouTube.
"""
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional

class PlatformEngine:
    def __init__(self):
        self.platforms = {
            "discord": {"token": os.getenv("DISCORD_TOKEN", ""), "status": "offline"},
            "telegram_bot1": {"token": os.getenv("TELEGRAM_BOT1_TOKEN", ""), "status": "offline"},
            "telegram_bot2": {"token": os.getenv("TELEGRAM_BOT2_TOKEN", ""), "status": "offline"},
            "telegram_bot3": {"token": os.getenv("TELEGRAM_BOT3_TOKEN", ""), "status": "offline"},
            "slack": {"bot_token": os.getenv("SLACK_BOT_TOKEN", ""), "app_token": os.getenv("SLACK_APP_TOKEN", ""), "status": "offline"},
            "youtube": {"api_key": os.getenv("GOOGLE_API_KEY", ""), "status": "offline"},
        }
        self.messages = []

    def boot(self):
        for name, config in self.platforms.items():
            has_creds = any(v for k, v in config.items() if "token" in k or "key" in k)
            config["status"] = "online" if has_creds else "offline (no credentials)"
            print(f"[PLATFORM] {name}: {config['status']}")

    def send_message(self, platform: str, message: str, target: str = None) -> Dict:
        entry = {
            "platform": platform,
            "message": message,
            "target": target,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "queued"
        }
        self.messages.append(entry)
        # In production, this would dispatch to actual APIs
        entry["status"] = "sent (simulated)"
        return entry

    def get_status(self) -> Dict:
        return {name: {"status": cfg["status"]} for name, cfg in self.platforms.items()}


    def setup_platform(self, name: str):
        """Activate a platform by name."""
        if name not in self.platforms:
            self.platforms[name] = {"status": "online"}
        else:
            self.platforms[name]["status"] = "online"
        print(f"[PLATFORM] {name}: online")

    def broadcast(self, message: str) -> List[Dict]:
        results = []
        for platform in self.platforms:
            if self.platforms[platform]["status"].startswith("online"):
                results.append(self.send_message(platform, message))
        return results

# ─── Singleton getter ───────────────────────────────────────────
_platform_engine_instance = None

def get_platform_engine():
    global _platform_engine_instance
    if _platform_engine_instance is None:
        _platform_engine_instance = PlatformEngine()
    return _platform_engine_instance
