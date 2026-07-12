"""
Revenue Tracker — $20K/month target
"""
import os
from datetime import datetime

class RevenueTracker:
    STREAMS = ["products", "youtube", "trading", "affiliate", "subscriptions"]

    def __init__(self):
        self.revenue = {s: 0.0 for s in self.STREAMS}
        self.monthly_target = 20000.0

    def boot(self):
        print("[REVENUE] Tracker initialized. Target: $20K/month")

    def aggregate(self):
        total = sum(self.revenue.values())
        progress = (total / self.monthly_target) * 100 if self.monthly_target else 0
        print(f"[REVENUE] Total: ${total:.2f} | Progress: {progress:.1f}%")
        return {"total": total, "streams": self.revenue, "progress": progress}

    def add_revenue(self, stream, amount, source=""):
        if stream in self.revenue:
            self.revenue[stream] += amount
            print(f"[REVENUE] +${amount:.2f} from {stream} ({source})")

    def get_status(self):
        return self.aggregate()
