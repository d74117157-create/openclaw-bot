#!/usr/bin/env python3
"""
VICTOR ORCHESTRATOR - OpenClaw Master Controller
Runs all pipelines, posts to all platforms, tracks everything.
"""
import os
import sys
import json
import time
import subprocess
import traceback
from datetime import datetime

# Platform posting imports (graceful fallback if not installed)
try:
    import requests
except ImportError:
    requests = None

try:
    from telegram import Bot
except ImportError:
    Bot = None

try:
    from discord import Webhook
except ImportError:
    Webhook = None

# === CONFIGURATION ===
TELEGRAM_BOT_TOKENS = [
    os.getenv("TELEGRAM_BOT_TOKEN_1", ""),
    os.getenv("TELEGRAM_BOT_TOKEN_2", ""),
    os.getenv("TELEGRAM_BOT_TOKEN_3", "")
]
TELEGRAM_SUPER_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_SUPER", "")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")

# === LOGGING ===
LOG_FILE = "logs/orchestrator.log"
os.makedirs("logs", exist_ok=True)

def log(msg, level="INFO"):
    line = f"[{datetime.now().isoformat()}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# === PLATFORM POSTERS ===
def post_telegram(message, token_index=0):
    """Post to Telegram bot"""
    token = TELEGRAM_BOT_TOKENS[token_index] if token_index < len(TELEGRAM_BOT_TOKENS) else TELEGRAM_SUPER_TOKEN
    if not token or not requests:
        log("Telegram post skipped: no token or requests", "WARN")
        return False

    # Get updates to find chat IDs
    try:
        resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        updates = resp.json().get("result", [])
        chat_ids = list(set([u["message"]["chat"]["id"] for u in updates if "message" in u]))

        if not chat_ids:
            log("No Telegram chat IDs found. Send a message to the bot first.", "WARN")
            return False

        for chat_id in chat_ids:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10
            )
        log(f"Posted to Telegram (bot {token_index+1})", "OK")
        return True
    except Exception as e:
        log(f"Telegram error: {e}", "ERROR")
        return False

def post_discord(message):
    """Post to Discord webhook"""
    if not DISCORD_WEBHOOK or not requests:
        log("Discord post skipped: no webhook", "WARN")
        return False
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        log("Posted to Discord", "OK")
        return True
    except Exception as e:
        log(f"Discord error: {e}", "ERROR")
        return False

def post_slack(message):
    """Post to Slack webhook"""
    if not SLACK_WEBHOOK or not requests:
        log("Slack post skipped: no webhook", "WARN")
        return False
    try:
        requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=10)
        log("Posted to Slack", "OK")
        return True
    except Exception as e:
        log(f"Slack error: {e}", "ERROR")
        return False

def broadcast(message):
    """Post to ALL platforms"""
    log(f"BROADCASTING: {message[:100]}...")
    post_telegram(message, 0)
    post_telegram(message, 1)
    post_telegram(message, 2)
    post_discord(message)
    post_slack(message)

# === PIPELINE RUNNERS ===
def run_youtube_pipeline(niche="tech"):
    """Run the YouTube content pipeline"""
    log("Starting YouTube Pipeline...")
    try:
        result = subprocess.run(
            [sys.executable, "automation/youtube_pipeline.py", niche],
            capture_output=True, text=True, timeout=120
        )
        log(f"YouTube pipeline output: {result.stdout[:200]}")
        if result.returncode == 0:
            broadcast(f"📹 **YouTube Pipeline Complete**\nNiche: {niche}\nA new video project is ready for rendering. Check the project folder for script and instructions.")
            return True
        else:
            log(f"YouTube pipeline failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"YouTube pipeline exception: {e}", "ERROR")
        return False

def run_trading_pipeline():
    """Run the trading signal pipeline"""
    log("Starting Trading Signal Pipeline...")
    try:
        result = subprocess.run(
            [sys.executable, "automation/trading_signals.py", "--top"],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout
        log(f"Trading pipeline output: {output[:300]}")

        if result.returncode == 0 and "TOP OPPORTUNITY" in output:
            # Extract the opportunity line
            lines = output.split("\n")
            opp_line = [l for l in lines if "TOP OPPORTUNITY" in l]
            if opp_line:
                msg = f"📈 **Trading Signal**\n{opp_line[0].replace('TOP OPPORTUNITY:', '').strip()}"
                broadcast(msg)
            return True
        else:
            log("Trading pipeline: no strong signals today", "INFO")
            return False
    except Exception as e:
        log(f"Trading pipeline exception: {e}", "ERROR")
        return False

def run_health_check():
    """Check all systems"""
    log("Running health check...")
    status = {
        "timestamp": datetime.now().isoformat(),
        "platforms": {},
        "pipelines": {}
    }

    # Check platform connectivity
    for i, token in enumerate(TELEGRAM_BOT_TOKENS):
        status["platforms"][f"telegram_bot_{i+1}"] = "OK" if token else "NO_TOKEN"
    status["platforms"]["discord"] = "OK" if DISCORD_WEBHOOK else "NO_WEBHOOK"
    status["platforms"]["slack"] = "OK" if SLACK_WEBHOOK else "NO_WEBHOOK"

    # Check pipeline files exist
    status["pipelines"]["youtube"] = os.path.exists("automation/youtube_pipeline.py")
    status["pipelines"]["trading"] = os.path.exists("automation/trading_signals.py")

    log(f"Health check: {json.dumps(status)}")
    return status

# === MASTER CONTROL ===
def victor_command(command):
    """Parse natural language commands and execute"""
    command = command.lower().strip()
    log(f"VICTOR received: {command}")

    if "youtube" in command or "video" in command or "content" in command:
        niche = "tech"
        for n in ["tech", "crypto", "finance", "gaming", "music", "news"]:
            if n in command:
                niche = n
                break
        return run_youtube_pipeline(niche=niche)

    elif "trade" in command or "crypto" in command or "signal" in command or "market" in command:
        return run_trading_pipeline()

    elif "health" in command or "status" in command or "check" in command:
        status = run_health_check()
        broadcast(f"🔍 **System Health**\n```\n{json.dumps(status, indent=2)}\n```")
        return True

    elif "broadcast" in command or "post" in command or "send" in command:
        msg = command.replace("broadcast", "").replace("post", "").replace("send", "").strip()
        if msg:
            broadcast(f"📢 **Broadcast**\n{msg}")
            return True
        else:
            broadcast("📢 **OpenClaw Swarm Online**\nAll systems operational. Awaiting commands.")
            return True

    elif "help" in command or "commands" in command:
        help_msg = """🤖 **VICTOR ORCHESTRATOR - Available Commands**

Just say any of these naturally:

📹 **Content Creation**
- "make a youtube video" / "create content about tech"
- "generate a video about crypto"

📈 **Trading**
- "check the markets" / "get trading signals"
- "what's the best crypto opportunity"

🔍 **System**
- "health check" / "status report"
- "broadcast hello everyone"

The swarm handles the rest."""
        broadcast(help_msg)
        return True

    else:
        broadcast(f"🤖 **Victor**: I heard '{command}'. Try 'help' for commands, or tell me what you want to build.")
        return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        victor_command(cmd)
    else:
        print("VICTOR ORCHESTRATOR")
        print("Usage: python3 victor.py 'make a youtube video about crypto'")
        print("       python3 victor.py 'check the markets'")
        print("       python3 victor.py 'health check'")
