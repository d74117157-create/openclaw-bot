"""
Platform Integration Engine
Connects to every sales platform. No inventory. No shipping. Pure digital.
"""
import os
import json
import requests
from datetime import datetime

class PlatformEngine:
    """One engine. All platforms. Passive income."""

    PLATFORMS = {
        "gumroad": {
            "type": "digital",
            "fee": 0.10,  # 10% + $0.50
            "setup": "instant",
            "best_for": ["ebooks", "guides", "courses", "templates"],
            "api": "https://api.gumroad.com/v2",
            "webhook": True
        },
        "shopify": {
            "type": "hybrid",
            "fee": 0.029,  # 2.9% + 30¢ + $29/mo
            "setup": "1_hour",
            "best_for": ["storefront", "bundles", "subscriptions"],
            "api": "https://your-store.myshopify.com/admin/api/2024-01",
            "apps": ["printful", "gumroad", "digital_downloads"]
        },
        "amazon_kdp": {
            "type": "ebook",
            "royalty": 0.70,  # 70% for $2.99-$9.99
            "setup": "30_mins",
            "best_for": ["ebooks", "paperbacks"],
            "url": "https://kdp.amazon.com",
            "traffic": "organic_billions"
        },
        "etsy": {
            "type": "digital",
            "fee": 0.065,  # 6.5% + $0.20 listing
            "setup": "instant",
            "best_for": ["templates", "planners", "art"],
            "traffic": "high_intent_buyers"
        },
        "printful": {
            "type": "pod",
            "fee": 0,  # You set margin
            "setup": "15_mins",
            "best_for": ["merch", "apparel", "home_goods"],
            "integration": ["shopify", "etsy", "amazon", "ebay"]
        },
        "teachable": {
            "type": "course",
            "fee": 0.05,  # 5% + $39/mo
            "setup": "1_hour",
            "best_for": ["video_courses", "coaching"]
        },
        "patreon": {
            "type": "membership",
            "fee": 0.08,  # 8% + processing
            "setup": "instant",
            "best_for": ["recurring_revenue", "exclusive_content"]
        }
    }

    def __init__(self):
        self.active_platforms = []
        self.listings = []

    def setup_platform(self, name: str, config: dict = None):
        """Activate a platform."""
        if name not in self.PLATFORMS:
            print(f"[PLATFORM] ❌ Unknown: {name}")
            return None

        platform = self.PLATFORMS[name].copy()
        platform["name"] = name
        platform["status"] = "active"
        platform["connected"] = datetime.now().isoformat()

        self.active_platforms.append(platform)
        print(f"[PLATFORM] ✅ {name.upper()} activated")
        print(f"           Fee: {platform['fee']*100:.1f}% | Setup: {platform['setup']}")
        return platform

    def list_product(self, product: dict, platforms: list = None):
        """List product across platforms."""
        platforms = platforms or ["gumroad", "etsy"]
        listings = []

        for platform_name in platforms:
            if platform_name not in [p["name"] for p in self.active_platforms]:
                self.setup_platform(platform_name)

            listing = {
                "product_id": product.get("id"),
                "platform": platform_name,
                "title": product.get("title"),
                "price": product.get("price"),
                "url": f"https://{platform_name}.com/your-store/{product.get('id')}",
                "status": "live",
                "listed_at": datetime.now().isoformat()
            }
            listings.append(listing)
            self.listings.append(listing)
            print(f"[LISTING] 🚀 {product['title']} on {platform_name.upper()}")

        return listings

    def get_revenue_projection(self, platform: str = None):
        """Calculate revenue across all platforms."""
        if platform:
            p = self.PLATFORMS.get(platform, {})
            return {
                "platform": platform,
                "fee": p.get("fee", 0),
                "best_for": p.get("best_for", []),
                "example": f"$100 sale → You keep ${100*(1-p.get('fee',0)):.2f}"
            }

        # All platforms
        total = {"platforms": [], "monthly_potential": 0}
        for name, p in self.PLATFORMS.items():
            total["platforms"].append({
                "name": name,
                "fee": p["fee"],
                "best_for": p["best_for"][0] if p["best_for"] else "general"
            })
        return total

    def auto_distribute(self, product: dict):
        """Smart distribution — best platform for product type."""
        product_type = product.get("type", "ebook")

        platform_map = {
            "ebook": ["amazon_kdp", "gumroad", "etsy"],
            "guide": ["gumroad", "shopify"],
            "course": ["teachable", "gumroad"],
            "template": ["etsy", "gumroad"],
            "bundle": ["shopify", "gumroad"],
            "merch": ["printful", "etsy"],
            "membership": ["patreon", "gumroad"]
        }

        targets = platform_map.get(product_type, ["gumroad"])
        return self.list_product(product, targets)

def get_platform_engine():
    return PlatformEngine()
