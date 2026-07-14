#!/usr/bin/env python3
"""Empire Secret Sync Operator — GitHub Secrets → Render Env Vars"""
import os, sys, requests

RENDER_API_KEY = os.environ["RENDER_API_KEY"]
SERVICE_ID = os.environ["RENDER_SERVICE_ID"]
BASE_URL = "https://api.render.com/v1"
HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

SYNC_KEYS = [
    "GROQ_API_KEY", "OPENAI_API_KEY", "TELEGRAM_BOT1_TOKEN",
    "TELEGRAM_BOT2_TOKEN", "TELEGRAM_BOT3_TOKEN", "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN", "GOOGLE_API_KEY", "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET", "EMPIRE_PASSWORD",
    "DISCORD_TOKEN", "DISCORD_GUILD_ID", "DISCORD_CHANNEL_ID",
    "RENDER_API_KEY", "JWT_SECRET_KEY", "EMPIRE_PASSWORD",
    "TRADING_MODE", "MAX_DAILY_LOSS_PCT", "MAX_POSITION_PCT",
    "STOP_LOSS_PCT", "TAKE_PROFIT_PCT", "PYTHON_VERSION",
    "PORT", "PYTHONPATH", "EMPIRE_STATE_PATH",
]

def sync():
    success_count = 0
    fail_count = 0
    for key in SYNC_KEYS:
        val = os.environ.get(key)
        if not val:
            print(f"⏭️  Skipping {key} — not set in GitHub secrets")
            continue

        print(f"📦 Syncing {key}...")
        r = requests.put(
            f"{BASE_URL}/services/{SERVICE_ID}/env-vars/{key}",
            headers=HEADERS,
            json={"value": val},
            timeout=30
        )
        if r.status_code in (200, 201):
            print(f"   ✅ {key}")
            success_count += 1
        else:
            print(f"   ❌ {key}: HTTP {r.status_code} — {r.text[:200]}")
            fail_count += 1

    print(f"\n📊 Results: {success_count} synced, {fail_count} failed")
    if fail_count > 0:
        sys.exit(1)
    print("✅ All secrets synced successfully.")

if __name__ == "__main__":
    sync()
