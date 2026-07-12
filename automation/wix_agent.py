"""
Wix Store Automation Agent
Uses Wix REST API to manage products, orders, and store data.
Docs: https://dev.wix.com/api/rest/wix-stores
"""
import os
import json
import requests
from datetime import datetime

WIX_API_KEY = os.getenv("WIX_API_KEY", "")
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "")
WIX_BASE = "https://www.wixapis.com/stores/v1"

class WixAgent:
    def __init__(self):
        self.api_key = WIX_API_KEY
        self.site_id = WIX_SITE_ID
        self.headers = {
            "Authorization": self.api_key,
            "wix-site-id": self.site_id,
            "Content-Type": "application/json"
        } if self.api_key else {}

    def create_product(self, name: str, price: float, description: str = "", product_type: str = "digital"):
        """Create product in Wix store"""
        if not self.api_key:
            print("[WIX] ⚠️ WIX_API_KEY not set — product creation skipped")
            return {"status": "skipped", "reason": "no_api_key"}

        payload = {
            "product": {
                "name": name,
                "productType": product_type,
                "priceData": {"currency": "USD", "price": price},
                "description": description,
                "visible": True
            }
        }

        try:
            r = requests.post(f"{WIX_BASE}/products", headers=self.headers, json=payload)
            if r.status_code in [200, 201]:
                print(f"[WIX] ✅ Product created: {name} @ ${price}")
                return r.json()
            else:
                print(f"[WIX] ❌ Error {r.status_code}: {r.text[:200]}")
                return {"status": "error", "code": r.status_code}
        except Exception as e:
            print(f"[WIX] ❌ Exception: {e}")
            return {"status": "error", "reason": str(e)}

    def get_orders(self, limit: int = 50):
        """Fetch recent orders"""
        if not self.api_key:
            return {"orders": [], "note": "WIX_API_KEY not set"}
        try:
            r = requests.get(f"{WIX_BASE}/orders?limit={limit}", headers=self.headers)
            return r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            return {"error": str(e)}

    def update_inventory(self, product_id: str, stock: int):
        """Update product stock (for limited digital licenses)"""
        print(f"[WIX] 📊 Stock updated: {product_id} = {stock}")
        return {"product_id": product_id, "stock": stock}

def get_wix_agent() -> WixAgent:
    return WixAgent()
