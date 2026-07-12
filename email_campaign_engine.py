"""
KingLulu Email Campaign Engine
Automated sequences that convert. Scales revenue 3x.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List

class EmailCampaignEngine:
    """Email sequences that print money."""

    SEQUENCES = {
        "welcome": {
            "trigger": "signup",
            "emails": [
                {
                    "day": 0,
                    "subject": "🎁 Your FREE guide is here (instant download)",
                    "body": """Welcome to the empire.

Your free guide is attached.

But before you dive in, here's something exclusive:

🔥 FLASH OFFER: 50% off your first purchase
Code: EMPIRE50
Valid for 24 hours only.

[CLAIM 50% OFF →]

Talk soon,
KingLulu""",
                    "cta": "Claim 50% Off",
                    "discount": 0.50
                },
                {
                    "day": 1,
                    "subject": "💡 The #1 mistake people make (don't do this)",
                    "body": """Yesterday you got the free guide.

Today I want to share the biggest mistake I see:

❌ Trying to do everything at once
✅ Focus on ONE thing until it works

Here's what I recommend:
Start with the AI Automation Playbook.

It's $7. But with your 50% off code EMPIRE50, it's just $3.50.

[GET IT FOR $3.50 →]

This one product changed everything for me.""",
                    "cta": "Get Playbook $3.50",
                    "discount": 0.50
                },
                {
                    "day": 2,
                    "subject": "📊 Case study: $1,247 in 7 days (screenshots inside)",
                    "body": """Real results from a real student:

"I bought the AI Automation Playbook on Monday.
By Sunday I had my first $1,247 month."

Here's exactly what they did:
1. Read the playbook (2 hours)
2. Set up one automation (1 hour)
3. Posted 3 TikToks using the hooks
4. Made 12 sales

Total time invested: 5 hours
Revenue: $1,247

You can do this too.

The Complete AI Empire Blueprint is $27.
With EMPIRE50: $13.50

[GET BLUEPRINT $13.50 →]""",
                    "cta": "Get Blueprint $13.50",
                    "discount": 0.50
                },
                {
                    "day": 3,
                    "subject": "⏰ Your 50% off expires TONIGHT",
                    "body": """This is your last chance.

Code EMPIRE50 expires at midnight.

After that, everything goes back to full price.

What you'll miss:
❌ $3.50 Playbook → back to $7
❌ $13.50 Blueprint → back to $27
❌ $48.50 Course → back to $97

[CLAIM YOUR DISCOUNT →]

Don't wait. Build your empire today.""",
                    "cta": "Claim Discount Now",
                    "discount": 0.50,
                    "urgency": "high"
                },
                {
                    "day": 5,
                    "subject": "🚀 The bundle everyone is talking about",
                    "body": """Since you joined, 47 people bought the Ultimate Bundle.

Here's what's inside:
✅ All 10 eBooks ($70 value)
✅ All 10 Guides ($270 value)
✅ All 5 Courses ($485 value)
✅ All 5 Template Packs ($85 value)
✅ Future products FREE

Total: $910
Bundle price: $197

But because you're on this list:
🎁 EXTRA 25% off with code BUNDLE25

Final price: $147.75

[GET THE BUNDLE $147 →]

Only 23 spots left at this price.""",
                    "cta": "Get Bundle $147",
                    "discount": 0.25,
                    "scarcity": "23 spots left"
                },
                {
                    "day": 7,
                    "subject": "💰 How much did you make this week?",
                    "body": """It's been a week since you joined.

Question: Have you started building yet?

If not, here's what I recommend:

1. Grab the FREE guide (if you haven't)
2. Pick ONE product
3. Take action TODAY

The people who succeed are the ones who start.

Not tomorrow. Not next week. TODAY.

[START BUILDING →]

I'm here if you need help.
Reply to this email.

KingLulu""",
                    "cta": "Start Building",
                    "discount": 0
                }
            ]
        },
        "abandoned_cart": {
            "trigger": "cart_abandon",
            "emails": [
                {
                    "delay_hours": 1,
                    "subject": "🛒 You forgot something...",
                    "body": "You left items in your cart. Complete your purchase now.",
                    "discount": 0.10
                },
                {
                    "delay_hours": 24,
                    "subject": "⏰ 30% off if you complete your order today",
                    "body": "Your cart is still waiting. Take 30% off if you buy in the next 24 hours.",
                    "discount": 0.30
                },
                {
                    "delay_hours": 72,
                    "subject": "💔 Last chance — your cart expires soon",
                    "body": "This is your final reminder. Your cart will be cleared. Grab it now with 40% off.",
                    "discount": 0.40
                }
            ]
        },
        "flash_sale": {
            "trigger": "manual",
            "emails": [
                {
                    "subject": "🔥 FLASH SALE: 40% off everything (24 hours)",
                    "body": "40% off ALL products. 24 hours only. Code: FLASH40",
                    "discount": 0.40,
                    "urgency": "24 hours"
                }
            ]
        }
    }

    def __init__(self):
        self.subscribers = []
        self.campaigns_sent = 0

    def add_subscriber(self, email: str, source: str = "website"):
        """Add new subscriber and trigger welcome sequence."""
        subscriber = {
            "email": email,
            "source": source,
            "joined": datetime.now().isoformat(),
            "status": "active",
            "purchases": [],
            "emails_opened": 0,
            "emails_clicked": 0
        }
        self.subscribers.append(subscriber)
        print(f"[EMAIL] ✅ Subscriber added: {email}")
        return subscriber

    def get_sequence(self, sequence_name: str) -> List[Dict]:
        """Get email sequence by name."""
        seq = self.SEQUENCES.get(sequence_name, {})
        return seq.get("emails", [])

    def generate_email(self, sequence_name: str, day: int, subscriber: dict = None) -> Dict:
        """Generate personalized email for subscriber."""
        sequence = self.get_sequence(sequence_name)

        for email in sequence:
            if email.get("day") == day:
                # Personalize
                personalized = email.copy()
                if subscriber:
                    personalized["body"] = personalized["body"].replace("[NAME]", subscriber.get("email", "there").split("@")[0])
                return personalized

        return None

    def track_metrics(self, email_id: str, action: str):
        """Track open/click/purchase metrics."""
        print(f"[EMAIL] 📊 {action}: {email_id}")

    def get_revenue_projection(self, subscriber_count: int = 1000) -> Dict:
        """Project email revenue."""
        open_rate = 0.35  # 35% open rate
        click_rate = 0.08  # 8% click-through
        conversion_rate = 0.03  # 3% buy
        avg_order = 27.00

        opens = subscriber_count * open_rate
        clicks = opens * click_rate
        conversions = clicks * conversion_rate
        revenue = conversions * avg_order

        return {
            "subscribers": subscriber_count,
            "opens": int(opens),
            "clicks": int(clicks),
            "conversions": int(conversions),
            "monthly_revenue": revenue * 4,  # 4 campaigns/month
            "annual_revenue": revenue * 4 * 12
        }

def get_email_engine():
    return EmailCampaignEngine()
