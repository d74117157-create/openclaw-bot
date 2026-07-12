#!/usr/bin/env python3
"""
GBABY AGENT - The swarm's AI brain
Uses Groq free tier (1M tokens/day, no credit card)
"""
import os
import requests
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are Gbaby, an aggressive, no-nonsense AI orchestrator. 
You execute immediately. No fluff. No "watch this" or "go check that."
You make decisions and return actionable commands.

When given a task, you decide:
1. Which pipeline to run (youtube, trading, broadcast, health)
2. What parameters to use
3. What the output should be

Return ONLY a JSON object with:
{
  "pipeline": "youtube|trading|broadcast|health|none",
  "params": {"niche": "...", "region": "..."},
  "message": "what to say to the user",
  "action": "what to execute immediately"
}"""

def think(user_input):
    """Gbaby thinks and returns a decision"""
    if not GROQ_API_KEY:
        return {
            "pipeline": "none",
            "params": {},
            "message": "❌ Gbaby needs GROQ_API_KEY in Render env. Get free key at https://console.groq.com",
            "action": "Set GROQ_API_KEY and redeploy"
        }

    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"User said: '{user_input}'. What should the swarm do?"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=15
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Try to parse JSON, fallback to text
        try:
            decision = json.loads(content)
        except:
            decision = {
                "pipeline": "broadcast",
                "params": {},
                "message": content,
                "action": "broadcast"
            }
        return decision
    except Exception as e:
        return {
            "pipeline": "none",
            "params": {},
            "message": f"⚠️ Gbaby error: {str(e)}",
            "action": "Check GROQ_API_KEY and network"
        }

def execute(decision):
    """Execute the decision Gbaby made"""
    import subprocess
    import sys

    pipeline = decision.get("pipeline", "none")
    params = decision.get("params", {})

    if pipeline == "youtube":
        niche = params.get("niche", "tech")
        region = params.get("region", "US")
        cmd = f"{sys.executable} automation/youtube_pipeline.py {niche} {region}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return f"📹 YouTube pipeline executed\n{result.stdout[:500]}"

    elif pipeline == "trading":
        cmd = f"{sys.executable} automation/trading_signals.py --top"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return f"📈 Trading signals executed\n{result.stdout[:500]}"

    elif pipeline == "broadcast":
        msg = decision.get("message", "Gbaby says hello")
        from victor import broadcast
        broadcast(msg)
        return f"📢 Broadcast sent: {msg[:100]}"

    elif pipeline == "health":
        from victor import run_health_check
        status = run_health_check()
        return f"🔍 Health check: {json.dumps(status, indent=2)[:500]}"

    else:
        return f"🤖 Gbaby: {decision.get('message', 'No action taken')}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        decision = think(user_input)
        print(json.dumps(decision, indent=2))
        print("\n--- EXECUTING ---")
        result = execute(decision)
        print(result)
    else:
        print("Usage: python3 agents/gbaby.py 'make a youtube video about crypto'")
