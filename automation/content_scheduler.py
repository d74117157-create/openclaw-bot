"""
OpenClaw Content Scheduler
Auto-generates and schedules content across all platforms.
Runs daily via cron or Discord command.
"""
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List

class ContentScheduler:
    def __init__(self):
        self.niches = {
            "history": [
                "Forgotten empires that shaped modern politics",
                "The real story behind today's headlines",
                "Ancient technologies we still use",
                "Conspiracy theories vs historical facts",
                "Secret societies: myth or reality?",
                "How history repeats itself (and how to profit)",
                "The dark side of popular narratives",
                "Hidden connections between wars and wealth",
                "Why the history books lied to you",
                "Ancient money systems vs crypto today"
            ],
            "ai_automation": [
                "Build a bot army in 24 hours",
                "AI agents that make money while you sleep",
                "How I automated my entire business",
                "Claude Code vs Groq: which AI wins?",
                "The $0 startup: AI tools only",
                "Passive income with trading bots",
                "How to build a digital empire from your phone",
                "AI content machine: YouTube + TikTok + Payhip",
                "Why most people fail at automation (and how to win)",
                "The 1-hour workday: full automation setup"
            ],
            "money_hacks": [
                "Genius money hacks they don't teach in school",
                "How to 10x your income with AI tools",
                "The lazy person's guide to wealth",
                "Crypto trading for beginners (paper mode first)",
                "How I made $1K in a week with zero followers",
                "Affiliate marketing without showing your face",
                "The truth about passive income streams",
                "Why your 9-5 is keeping you poor",
                "Automated sales funnels that print money",
                "The AI millionaire mindset"
            ]
        }

        self.hooks = [
            "You won't believe what {topic} just revealed...",
            "The truth about {topic} that nobody talks about.",
            "Why {topic} is about to change everything.",
            "I analyzed {topic} so you don't have to. Here's what I found.",
            "They don't want you to know this about {topic}.",
            "{topic} explained in 60 seconds.",
            "What if I told you {topic} was a lie?",
            "The shocking reality of {topic}.",
            "How {topic} made me $$$ overnight.",
            "Stop doing {topic} wrong. Do this instead."
        ]

    def generate_content_plan(self, days: int = 30) -> Dict:
        """Generate a 30-day content calendar."""
        plan = {
            "youtube": [],
            "tiktok": [],
            "discord": [],
            "telegram": []
        }

        start_date = datetime.now()

        for day in range(days):
            date = start_date + timedelta(days=day)

            # YouTube: 2x per week (Mon, Thu)
            if date.weekday() in [0, 3]:
                niche = random.choice(list(self.niches.keys()))
                topic = random.choice(self.niches[niche])
                plan["youtube"].append({
                    "date": date.strftime("%Y-%m-%d"),
                    "topic": topic,
                    "niche": niche,
                    "format": "long_form" if date.weekday() == 0 else "shorts",
                    "hook": random.choice(self.hooks).format(topic=topic),
                    "cta": "Link in bio for full guide"
                })

            # TikTok: Daily
            niche = random.choice(list(self.niches.keys()))
            topic = random.choice(self.niches[niche])
            plan["tiktok"].append({
                "date": date.strftime("%Y-%m-%d"),
                "topic": topic,
                "niche": niche,
                "format": random.choice(["hook", "story", "tutorial", "reaction"]),
                "hook": random.choice(self.hooks).format(topic=topic),
                "sound_trend": random.choice(["trending", "original", "remix"])
            })

            # Discord: 3x per week
            if date.weekday() in [1, 3, 5]:
                plan["discord"].append({
                    "date": date.strftime("%Y-%m-%d"),
                    "type": random.choice(["update", "tip", "resource", "poll"]),
                    "content": f"Daily swarm update: {random.choice(['New build', 'Trading signal', 'Content drop', 'Tool release'])}"
                })

            # Telegram: Daily broadcast
            plan["telegram"].append({
                "date": date.strftime("%Y-%m-%d"),
                "type": random.choice(["alert", "tip", "link", "reminder"]),
                "content": f"🦅 OpenClaw Empire Update — Day {day+1}"
            })

        return plan

    def get_today_content(self) -> Dict:
        """Get today's scheduled content."""
        plan = self.generate_content_plan(days=1)
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            platform: [item for item in items if item["date"] == today]
            for platform, items in plan.items()
        }

    def generate_script(self, topic: str, platform: str = "youtube", duration: int = 600) -> Dict:
        """Generate a full video script."""
        hook = random.choice(self.hooks).format(topic=topic)

        if platform == "youtube":
            return {
                "hook": hook,
                "intro": f"Welcome back to the empire. Today we're breaking down {topic}.",
                "body_points": [
                    f"Point 1: What is {topic} and why it matters",
                    f"Point 2: The hidden truth about {topic}",
                    f"Point 3: How to use {topic} to your advantage",
                    f"Point 4: Real examples and case studies",
                    f"Point 5: Action steps you can take today"
                ],
                "outro": f"If this helped, grab the free guide in the description. Build your empire. See you in the next one.",
                "cta": "Subscribe + hit the bell for daily builds",
                "duration_estimate": duration,
                "affiliate_insert": "After Point 3: Mention relevant tool"
            }
        elif platform == "tiktok":
            return {
                "hook": hook,
                "script": f"{hook} [pause] Here's the truth about {topic} in 60 seconds... [fast cuts]",
                "hashtags": ["#AI", "#Automation", "#PassiveIncome", "#DigitalEmpire", "#MoneyHacks"],
                "sound": "trending",
                "duration": 60
            }

        return {"hook": hook, "topic": topic}

def get_scheduler():
    return ContentScheduler()
