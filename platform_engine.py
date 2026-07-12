"""
Platform Engine v2.0 — Gumroad + Payhip Focus
No Amazon KDP. eBooks everywhere else.
"""
import os
import json
import requests
from datetime import datetime

class PlatformEngine:
    """Gumroad + Payhip + Etsy + Shopify + Teachable + Patreon"""

    PLATFORMS = {
        "gumroad": {
            "type": "digital",
            "fee": 0.10,
            "setup": "instant",
            "best_for": ["ebooks", "guides", "courses", "templates", "bundles"],
            "api": "https://api.gumroad.com/v2",
            "webhook": True,
            "url": "https://gumroad.com"
        },
        "payhip": {
            "type": "digital",
            "fee": 0.05,
            "setup": "instant",
            "best_for": ["ebooks", "guides", "courses", "memberships"],
            "url": "https://payhip.com",
            "store_url": "https://payhip.com/b/lAr1N"
        },
        "etsy": {
            "type": "digital",
            "fee": 0.065,
            "setup": "instant",
            "best_for": ["templates", "planners", "digital_art", "printables"],
            "url": "https://etsy.com"
        },
        "shopify": {
            "type": "hybrid",
            "fee": 0.029,
            "monthly": 29,
            "setup": "1_hour",
            "best_for": ["storefront", "bundles", "subscriptions", "physical"],
            "url": "https://shopify.com"
        },
        "teachable": {
            "type": "course",
            "fee": 0.05,
            "monthly": 39,
            "setup": "1_hour",
            "best_for": ["video_courses", "coaching", "workshops"],
            "url": "https://teachable.com"
        },
        "patreon": {
            "type": "membership",
            "fee": 0.08,
            "setup": "instant",
            "best_for": ["recurring_revenue", "exclusive_content", "community"],
            "url": "https://patreon.com"
        }
    }

    def __init__(self):
        self.active_platforms = []
        self.listings = []

    def setup_platform(self, name: str):
        if name not in self.PLATFORMS:
            print(f"[PLATFORM] ❌ Unknown: {name}")
            return None

        platform = self.PLATFORMS[name].copy()
        platform["name"] = name
        platform["status"] = "active"
        platform["connected"] = datetime.now().isoformat()

        self.active_platforms.append(platform)
        print(f"[PLATFORM] ✅ {name.upper()} activated")
        return platform

    def list_product(self, product: dict, platforms: list = None):
        platforms = platforms or ["gumroad", "payhip", "etsy"]
        listings = []

        for platform_name in platforms:
            if platform_name not in [p["name"] for p in self.active_platforms]:
                self.setup_platform(platform_name)

            listing = {
                "product_id": product.get("id"),
                "platform": platform_name,
                "title": product.get("title"),
                "price": product.get("price"),
                "url": self._get_product_url(platform_name, product),
                "status": "live",
                "listed_at": datetime.now().isoformat()
            }
            listings.append(listing)
            self.listings.append(listing)
            print(f"[LISTING] 🚀 {product['title']} on {platform_name.upper()}")

        return listings

    def _get_product_url(self, platform: str, product: dict) -> str:
        urls = {
            "gumroad": f"https://gumroad.com/l/{product.get('id', 'product')}",
            "payhip": f"https://payhip.com/b/{product.get('id', 'product')}",
            "etsy": f"https://etsy.com/listing/{product.get('id', 'product')}",
            "shopify": f"https://your-store.myshopify.com/products/{product.get('id', 'product')}",
            "teachable": f"https://your-school.teachable.com/p/{product.get('id', 'product')}",
            "patreon": f"https://patreon.com/posts/{product.get('id', 'product')}"
        }
        return urls.get(platform, "")

    def auto_distribute(self, product: dict):
        product_type = product.get("type", "ebook")

        platform_map = {
            "ebook": ["gumroad", "payhip", "etsy"],
            "guide": ["gumroad", "payhip", "shopify"],
            "course": ["teachable", "gumroad", "payhip"],
            "template": ["etsy", "gumroad", "payhip"],
            "bundle": ["gumroad", "payhip", "shopify"],
            "membership": ["patreon", "gumroad"]
        }

        targets = platform_map.get(product_type, ["gumroad", "payhip"])
        return self.list_product(product, targets)

    def get_payhip_store_url(self):
        return "https://payhip.com/b/lAr1N"

def get_platform_engine():
    return PlatformEngine()
