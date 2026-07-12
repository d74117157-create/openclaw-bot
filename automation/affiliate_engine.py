"""
OpenClaw Affiliate Engine
Manages affiliate links across all platforms.
Auto-inserts into YouTube descriptions, TikTok bios, Discord pins.
"""
import os
import json
from datetime import datetime
from typing import Dict, List

class AffiliateEngine:
    def __init__(self):
        self.links = {
            # Payhip Products
            "payhip_free_script": {
                "url": "https://payhip.com/b/KingLuluFreeScript",
                "platforms": ["youtube", "tiktok", "discord", "telegram"],
                "cta": "🛠️ Free AI Script — Download Now",
                "commission": 0  # Own product
            },
            "payhip_full_store": {
                "url": "https://payhip.com/KingLulu",
                "platforms": ["youtube", "tiktok", "discord", "telegram", "slack"],
                "cta": "💰 Full Digital Store — AI Tools & Automation",
                "commission": 0
            },
            "payhip_inner_circle": {
                "url": "https://www.patreon.com/KingLulu",
                "platforms": ["youtube", "tiktok", "discord"],
                "cta": "⭐ Inner Circle — Exclusive AI Builds",
                "commission": 0
            },
            # External Affiliates
            "hostinger": {
                "url": "https://hostinger.com?REF=kinglulu",
                "platforms": ["youtube", "tiktok"],
                "cta": "🌐 Hostinger — 80% Off Web Hosting (Code: KINGLULU)",
                "commission": 0.60
            },
            "tubebuddy": {
                "url": "https://www.tubebuddy.com/KingLulu",
                "platforms": ["youtube"],
                "cta": "📊 TubeBuddy — YouTube SEO Tool (Free Trial)",
                "commission": 0.30
            },
            "vidiq": {
                "url": "https://vidiq.com/KingLulu",
                "platforms": ["youtube", "tiktok"],
                "cta": "🔍 VidIQ — Grow Your Channel Faster",
                "commission": 0.25
            },
            "binance_ref": {
                "url": "https://accounts.binance.com/register?ref=KINGLULU",
                "platforms": ["youtube", "tiktok", "discord", "telegram"],
                "cta": "📈 Binance — Trade Crypto (20% Fee Discount)",
                "commission": 0.20
            },
            "nordvpn": {
                "url": "https://nordvpn.com/KingLulu",
                "platforms": ["youtube", "tiktok"],
                "cta": "🔒 NordVPN — Stay Anonymous Online",
                "commission": 0.40
            },
            "grammarly": {
                "url": "https://grammarly.com/KingLulu",
                "platforms": ["youtube", "tiktok", "discord"],
                "cta": "✍️ Grammarly — Write Like a Pro (Free)",
                "commission": 0.15
            },
            "notion": {
                "url": "https://notion.so/KingLulu",
                "platforms": ["youtube", "tiktok", "discord"],
                "cta": "📝 Notion — Organize Your Empire",
                "commission": 0.20
            },
            "descript": {
                "url": "https://descript.com?ref=kinglulu",
                "platforms": ["youtube", "tiktok"],
                "cta": "🎬 Descript — Edit Video Like Text",
                "commission": 0.25
            },
            "elevenlabs": {
                "url": "https://elevenlabs.io?ref=kinglulu",
                "platforms": ["youtube", "tiktok"],
                "cta": "🗣️ ElevenLabs — AI Voiceovers",
                "commission": 0.22
            },
            "midjourney": {
                "url": "https://midjourney.com?ref=kinglulu",
                "platforms": ["youtube", "tiktok"],
                "cta": "🎨 Midjourney — AI Art Generation",
                "commission": 0.10
            },
            "jasper": {
                "url": "https://jasper.ai?ref=kinglulu",
                "platforms": ["youtube", "tiktok", "discord"],
                "cta": "🤖 Jasper AI — Write Content 10x Faster",
                "commission": 0.30
            },
        }

    def get_links_for_platform(self, platform: str, max_links: int = 5) -> List[Dict]:
        """Get affiliate links optimized for a platform."""
        filtered = [v for k, v in self.links.items() if platform in v["platforms"]]
        # Sort by commission (own products first, then highest commission)
        filtered.sort(key=lambda x: (x["commission"] == 0, -x["commission"]))
        return filtered[:max_links]

    def generate_youtube_description(self, video_topic: str) -> str:
        """Generate YouTube description with affiliate links."""
        links = self.get_links_for_platform("youtube", max_links=6)
        desc = f"""🎬 {video_topic}

Learn more about AI, automation, and building digital empires.

🛠️ MY TOOLS (Support the channel):
"""
        for link in links:
            desc += f"
{link['cta']}
{link['url']}"

        desc += """

📚 MY CHANNELS:
• @realhistory-lessons — Forgotten stories they erased
• @kinglulu — AI agents & automation builds

💰 BUSINESS: Luluharvey778@gmail.com

#AI #Automation #DigitalEmpire #PassiveIncome #OpenClaw"""
        return desc

    def generate_tiktok_bio(self) -> str:
        """Generate TikTok bio with links."""
        links = self.get_links_for_platform("tiktok", max_links=3)
        bio = "🛠️ AI builds & automation\n💰 Digital empire tools\n"
        bio += f"\n🔗 {links[0]['url']}" if links else ""
        return bio

    def generate_discord_pin(self) -> str:
        """Generate Discord pinned message with links."""
        links = self.get_links_for_platform("discord", max_links=4)
        msg = "🦅 **OpenClaw Empire — Resources**\n\n"
        for link in links:
            msg += f"• {link['cta']}: {link['url']}\n"
        return msg

    def track_click(self, link_id: str, platform: str, user_id: str = None):
        """Track affiliate link clicks via swarm memory."""
        from memory.core import get_memory
        get_memory().log_event("affiliate_click", platform, f"{link_id} clicked by {user_id or 'unknown'}")

    def get_revenue_estimate(self, platform: str, views: int) -> Dict:
        """Estimate affiliate revenue from views."""
        links = self.get_links_for_platform(platform)
        total_commission = sum(l["commission"] for l in links)
        avg_conversion = 0.02  # 2% click-through
        avg_purchase = 0.05   # 5% of clicks buy

        clicks = views * avg_conversion
        purchases = clicks * avg_purchase
        revenue = purchases * 30 * total_commission  # $30 avg product

        return {
            "platform": platform,
            "views": views,
            "estimated_clicks": int(clicks),
            "estimated_purchases": int(purchases),
            "estimated_revenue": revenue,
            "links_count": len(links)
        }

def get_affiliate_engine():
    return AffiliateEngine()
