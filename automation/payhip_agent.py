"""
Payhip Digital Products Automation Agent
Auto-creates products, manages coupons, tracks sales.
Docs: https://payhip.com/help/api (no official API, uses web scraping + manual hooks)
"""
import os
import json
import requests
from datetime import datetime

PAYHIP_STORE = os.getenv("PAYHIP_STORE", "kinglulu")
PAYHIP_API_KEY = os.getenv("PAYHIP_API_KEY", "")  # If Payhip adds API later

class PayhipAgent:
    def __init__(self):
        self.store = PAYHIP_STORE
        self.products = []

    def create_product(self, title: str, price: float, file_path: str, description: str = "", tags: list = None):
        """Create a digital product on Payhip (manual upload + API hook when available)"""
        product = {
            "title": title,
            "price": price,
            "file": file_path,
            "description": description,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            "store": f"https://payhip.com/{self.store}"
        }
        self.products.append(product)
        print(f"[PAYHIP] 📦 Product created: {title} @ ${price}")
        print(f"[PAYHIP] 🔗 Upload manually at: {product['store']}/products/new")
        return product

    def generate_coupon(self, code: str, discount_pct: float, product_id: str = None):
        """Generate coupon code for launches"""
        coupon = {
            "code": code.upper(),
            "discount": discount_pct,
            "product": product_id,
            "created": datetime.now().isoformat()
        }
        print(f"[PAYHIP] 🎟️ Coupon: {code.upper()} — {discount_pct}% off")
        return coupon

    def get_sales_report(self):
        """Pull sales data (manual until API available)"""
        return {
            "store": self.store,
            "products": len(self.products),
            "last_check": datetime.now().isoformat(),
            "note": "Check Payhip dashboard for live sales data"
        }

    def auto_bundle(self, products: list, bundle_name: str, discount: float = 20.0):
        """Create product bundle for higher AOV"""
        total = sum(p["price"] for p in products)
        bundle_price = total * (1 - discount/100)
        print(f"[PAYHIP] 📚 Bundle '{bundle_name}': ${bundle_price:.2f} (was ${total:.2f}, {discount}% off)")
        return {
            "name": bundle_name,
            "products": [p["title"] for p in products],
            "original_price": total,
            "bundle_price": bundle_price,
            "discount": discount
        }

# Swarm integration
def get_payhip_agent() -> PayhipAgent:
    return PayhipAgent()
