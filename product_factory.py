"""
OpenClaw Product Factory
Generates digital products, courses, templates, bots.
"""
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any

class ProductFactory:
    TEMPLATES = [
        "discord_bot_template",
        "telegram_mini_app",
        "notion_template",
        "trading_strategy_pdf",
        "automation_script",
        "ai_prompt_pack",
    ]

    def __init__(self):
        self.products = []

    def create_product(self, name: str, template: str, price: float = 0.0, metadata: Dict = None) -> Dict:
        pid = hashlib.sha256(f"{name}{time.time()}".encode()).hexdigest()[:16]
        product = {
            "id": pid,
            "name": name,
            "template": template,
            "price": price,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "sales": 0,
            "revenue": 0.0
        }
        self.products.append(product)
        return product

    def list_products(self) -> List[Dict]:
        return self.products

    def publish(self, product_id: str) -> Dict:
        for p in self.products:
            if p["id"] == product_id:
                p["status"] = "published"
                p["published_at"] = datetime.utcnow().isoformat()
                return p
        return {"error": "Product not found"}

    def record_sale(self, product_id: str, amount: float):
        for p in self.products:
            if p["id"] == product_id:
                p["sales"] += 1
                p["revenue"] += amount
                return p
        return None

# ─── Singleton getter ───────────────────────────────────────────
_product_factory_instance = None

def get_product_factory():
    global _product_factory_instance
    if _product_factory_instance is None:
        _product_factory_instance = ProductFactory()
    return _product_factory_instance
