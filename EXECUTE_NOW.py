#!/usr/bin/env python3
"""
EXECUTE NOW - OpenClaw Swarm Launcher
Run this in your Render shell: python3 EXECUTE_NOW.py
"""
import os
import sys
import subprocess
import time

def run(cmd, desc):
    print(f"\n{'='*60}")
    print(f"🚀 {desc}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"⚠️  ERROR: {result.stderr[:500]}")
    return result.returncode == 0

# Check env vars
print("🔐 CHECKING CREDENTIALS...")
required = [
    "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", 
    "GOOGLE_REFRESH_TOKEN", "GOOGLE_ACCESS_TOKEN",
    "TELEGRAM_BOT_TOKEN_1", "TELEGRAM_BOT_TOKEN_2", "TELEGRAM_BOT_TOKEN_3"
]
missing = [r for r in required if not os.getenv(r)]
if missing:
    print(f"❌ MISSING ENV VARS: {missing}")
    print("Set these in Render dashboard → Environment → Save → Redeploy")
    sys.exit(1)
print("✅ All credentials present")

# Execute pipelines
print("\n" + "🐾"*30)
print("OPENCLAW SWARM EXECUTING")
print("🐾"*30)

success = []

# 1. YouTube Pipeline
if run("python3 automation/youtube_pipeline.py crypto US", "YOUTUBE CONTENT PIPELINE"):
    success.append("📹 YouTube video project created")

# 2. Trading Signals
if run("python3 automation/trading_signals.py --top", "TRADING SIGNALS"):
    success.append("📈 Trading signals generated")

# 3. Victor Health Check + Broadcast
if run('python3 victor.py "broadcast 🐾 OpenClaw Swarm EXECUTED. YouTube + Trading pipelines running."', "VICTOR BROADCAST"):
    success.append("📢 Broadcast sent to all platforms")

# 4. List created projects
print(f"\n{'='*60}")
print("📁 CREATED PROJECTS")
print(f"{'='*60}")
run("ls -la /tmp/youtube_projects/ 2>/dev/null || echo 'No projects yet'", "Listing projects")

print(f"\n{'='*60}")
print("✅ EXECUTION COMPLETE")
print(f"{'='*60}")
for s in success:
    print(f"  {s}")
print(f"\nNext steps:")
print("  1. Check /tmp/youtube_projects/ for your video script")
print("  2. Check Telegram/Discord/Slack for trading signals")
print("  3. Use CapCut or Pictory to render the video")
print("  4. Upload to YouTube manually (auto-upload coming v2)")
