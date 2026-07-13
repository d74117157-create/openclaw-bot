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
    "SLACK_APP_TOKEN", "GOOGLE_API_KEY", "EMPIRE_PASSWORD",
    "DISCORD_TOKEN", "DISCORD_GUILD_ID", "DISCORD_CHANNEL_ID",
    "RENDER_API_KEY",
]

def sync():
    payload = []
    for key in SYNC_KEYS:
        val = os.environ.get(key)
        if val:
            payload.append({"key": key, "value": val})
        else:
            print(f"⏭️  Skipping {key} — not set in GitHub secrets")
    if not payload:
        print("❌ No secrets to sync."); sys.exit(1)

    print(f"📦 Syncing {len(payload)} secrets to Render {SERVICE_ID}...")
    r = requests.put(f"{BASE_URL}/services/{SERVICE_ID}/env-vars",
                     headers=HEADERS, json=payload, timeout=30)
    if r.status_code in (200, 201, 204):
        print("✅ Secrets synced successfully.")
        for item in payload:
            print(f"   • {item['key']}: {item['value'][:4]}***")
    else:
        print(f"❌ Sync failed: {r.status_code}
{r.text}"); sys.exit(1)

if __name__ == "__main__":
    sync()
