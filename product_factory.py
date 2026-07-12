"""
Digital Product Factory
Creates, prices, and lists products across ALL platforms.
"""
import os
import json
from datetime import datetime

class ProductFactory:
    """Builds digital products that sell."""

    PRODUCT_TEMPLATES = {
        "ebook": {
            "price": 7.00,
            "pages": 25,
            "delivery": "pdf",
            "upsell": "course",
            "platforms": ["gumroad", "payhip", "amazon_kdp"]
        },
        "guide": {
            "price": 27.00,
            "pages": 50,
            "delivery": "pdf+video",
            "upsell": "coaching",
            "platforms": ["gumroad", "payhip", "shopify"]
        },
        "course": {
            "price": 97.00,
            "videos": 10,
            "delivery": "video+worksheets",
            "upsell": "mastermind",
            "platforms": ["gumroad", "teachable", "thinkific"]
        },
        "template": {
            "price": 17.00,
            "format": "notion/figma/canva",
            "delivery": "instant",
            "upsell": "bundle",
            "platforms": ["gumroad", "etsy", "creative_market"]
        },
        "bundle": {
            "price": 197.00,
            "includes": ["ebook", "guide", "course", "templates"],
            "delivery": "all_access",
            "upsell": "membership",
            "platforms": ["gumroad", "shopify", "patreon"]
        }
    }

    def __init__(self):
        self.products = []

    def create_product(self, product_type: str, topic: str, niche: str = "ai_automation"):
        """Create a complete digital product."""
        template = self.PRODUCT_TEMPLATES.get(product_type, self.PRODUCT_TEMPLATES["ebook"])

        product = {
            "id": f"{niche}_{product_type}_{int(datetime.now().timestamp())}",
            "type": product_type,
            "topic": topic,
            "niche": niche,
            "title": self._generate_title(topic, product_type),
            "description": self._generate_description(topic, product_type),
            "price": template["price"],
            "delivery": template["delivery"],
            "upsell": template["upsell"],
            "platforms": template["platforms"],
            "created": datetime.now().isoformat(),
            "status": "draft"
        }

        self.products.append(product)
        print(f"[FACTORY] 📦 Created: {product['title']} @ ${product['price']}")
        return product

    def _generate_title(self, topic: str, product_type: str) -> str:
        """Generate compelling product titles."""
        hooks = {
            "ebook": [
                f"The {topic} Playbook: From Zero to $1K/Day",
                f"{topic} Secrets They Don't Want You to Know",
                f"How I Mastered {topic} in 30 Days"
            ],
            "guide": [
                f"The Complete {topic} Blueprint",
                f"{topic} Mastery: Step-by-Step System",
                f"The $10K/Month {topic} Framework"
            ],
            "course": [
                f"{topic} Empire Builder: Full Course",
                f"The {topic} Accelerator: 0 to Expert",
                f"{topic} Domination: Advanced Strategies"
            ],
            "template": [
                f"Done-For-You {topic} Templates",
                f"The {topic} Toolkit: Ready to Use",
                f"{topic} Swipe File: Copy & Paste"
            ],
            "bundle": [
                f"The Ultimate {topic} Empire Bundle",
                f"{topic} Everything Pack: All My Systems",
                f"The Complete {topic} Business in a Box"
            ]
        }
        import random
        return random.choice(hooks.get(product_type, [f"{topic} {product_type.title()}"]))

    def _generate_description(self, topic: str, product_type: str) -> str:
        """Generate sales copy."""
        return f"""🚀 STOP struggling with {topic}. This {product_type} gives you everything.

✅ What you'll get:
• The exact system I use daily
• Step-by-step (no fluff)
• Works even if you're starting from zero
• Instant delivery

💰 Price: Way less than one bad trade.

⚡ Limited time. Grab it now."""

    def list_all_products(self):
        return self.products

    def get_revenue_projection(self, monthly_traffic: int = 10000):
        """Calculate potential revenue."""
        conversion = 0.02  # 2% visit-to-buy
        avg_order = 27.00  # Average product price

        monthly_sales = monthly_traffic * conversion
        monthly_revenue = monthly_sales * avg_order

        return {
            "monthly_traffic": monthly_traffic,
            "conversion_rate": conversion,
            "monthly_sales": int(monthly_sales),
            "avg_order_value": avg_order,
            "monthly_revenue": monthly_revenue,
            "annual_revenue": monthly_revenue * 12
        }

def get_product_factory():
    return ProductFactory()
