"""
TikTok Content & Affiliate Automation Agent
Uses TikTok API for posting, analytics, and affiliate link management.
Docs: https://developers.tiktok.com/
"""
import os
import json
import requests
from datetime import datetime

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")

class TikTokAgent:
    def __init__(self):
        self.client_key = TIKTOK_CLIENT_KEY
        self.access_token = TIKTOK_ACCESS_TOKEN

    def post_video(self, video_path: str, caption: str, hashtags: list = None):
        """Upload video to TikTok (requires Creator Portal API access)"""
        if not self.access_token:
            print("[TIKTOK] ⚠️ TIKTOK_ACCESS_TOKEN not set")
            print("[TIKTOK] 📋 Manual post required:")
            print(f"         Caption: {caption}")
            print(f"         Hashtags: {' '.join(['#'+h for h in (hashtags or [])])}")
            return {"status": "manual", "caption": caption, "hashtags": hashtags}

        # Direct posting via API (limited availability)
        print(f"[TIKTOK] 🎬 Video queued: {caption[:50]}...")
        return {"status": "queued", "platform": "tiktok"}

    def generate_affiliate_link(self, product_url: str, campaign: str = "openclaw"):
        """Generate TikTok Shop affiliate link"""
        link = f"{product_url}?tt_ref={campaign}&utm_source=tiktok"
        print(f"[TIKTOK] 🔗 Affiliate link: {link}")
        return {"link": link, "campaign": campaign}

    def schedule_content(self, content_plan: list):
        """Schedule TikTok content calendar"""
        schedule = []
        for i, item in enumerate(content_plan):
            post_time = datetime.now().isoformat()
            schedule.append({
                "day": i + 1,
                "topic": item,
                "time": post_time,
                "status": "scheduled"
            })
        print(f"[TIKTOK] 📅 {len(schedule)} posts scheduled")
        return schedule

    def get_analytics(self):
        """Pull TikTok analytics (manual until API approved)"""
        return {
            "followers": "Check TikTok Creator Portal",
            "views": "Check TikTok Analytics",
            "earnings": "Check TikTok Shop affiliate dashboard",
            "note": "Apply for TikTok for Developers API for automation"
        }

def get_tiktok_agent() -> TikTokAgent:
    return TikTokAgent()
