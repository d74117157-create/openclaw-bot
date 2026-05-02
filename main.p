"""
EONIX — Digital Empire OS
===========================
Master orchestrator. Boots all agents and verticals.

Run: python main.py
"""

import os, asyncio, threading, yaml
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY    = os.environ.get("GROQ_API_KEY", "")
DISCORD_TOKEN   = os.environ.get("DISCORD_TOKEN", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "")

# ─── AGENT REGISTRY ────────────────────────────────────────────────────────────

AGENTS = {
    "orchestrator": "Master coordinator — routes all tasks",
    "script":       "YouTube script writer (African history focus)",
    "seo":          "Titles, tags, descriptions optimizer",
    "research":     "Deep history & suppressed civilization researcher",
    "product":      "Payhip/Gumroad digital product creator",
    "publisher":    "YouTube upload metadata generator",
    "cto":          "Tech architecture & deployment advisor",
    "cmo":          "Marketing strategy & brand builder",
    "cfo":          "Financial tracking & investment advisor",
    "ux":           "Design & product experience agent",
}

# ─── VERTICAL REGISTRY ─────────────────────────────────────────────────────────

VERTICALS = {
    "innovate":  {"focus": "Tech startups", "agents": ["cto", "research"]},
    "ventures":  {"focus": "Investments",   "agents": ["cfo", "research"]},
    "media":     {"focus": "Content",       "agents": ["script", "seo", "publisher"]},
    "platforms": {"focus": "SaaS/products", "agents": ["product", "cto"]},
}

def print_empire_status():
    print("\n" + "="*50)
    print("🏛️  EONIX DIGITAL EMPIRE — ONLINE")
    print("="*50)
    print(f"\n✅ Groq AI:    {'SET' if GROQ_API_KEY else '❌ MISSING'}")
    print(f"✅ Discord:    {'SET' if DISCORD_TOKEN else '❌ MISSING'}")
    print(f"✅ Slack:      {'SET' if SLACK_BOT_TOKEN else '❌ MISSING'}")
    print(f"✅ GitHub:     {'SET' if GITHUB_TOKEN else '❌ MISSING'}")
    print(f"\n📡 Agents online: {len(AGENTS)}")
    for name, desc in AGENTS.items():
        print(f"   🤖 {name:<15} — {desc}")
    print(f"\n🏢 Verticals active: {len(VERTICALS)}")
    for name, cfg in VERTICALS.items():
        print(f"   📊 {name:<12} — {cfg['focus']}")
    print("\n" + "="*50)

def boot_gateway():
    """Boot Discord + Slack bots."""
    try:
        from gateway.bot import run_discord
        t = threading.Thread(target=run_discord, daemon=True)
        t.start()
        print("✅ Discord gateway booted")
    except Exception as e:
        print(f"⚠️  Discord gateway: {e}")

    try:
        from gateway.slack_bot import run_slack
        t2 = threading.Thread(target=run_slack, daemon=True)
        t2.start()
        print("✅ Slack gateway booted")
    except Exception as e:
        print(f"⚠️  Slack gateway: {e}")

def boot_bot_factory():
    """Boot the bot factory in background."""
    try:
        import subprocess, sys
        subprocess.Popen([sys.executable, "bot_factory.py"])
        print("✅ Bot Factory booted")
    except Exception as e:
        print(f"⚠️  Bot Factory: {e}")

if __name__ == "__main__":
    print_empire_status()
    boot_gateway()
    boot_bot_factory()

    print("\n🚀 All systems online. Empire is running.\n")

    # Keep alive
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n⛔ Empire shutdown.")
