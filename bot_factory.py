"""
OpenClaw — bot_factory.py
Bot Factory: spawns sub-bots, manages bot lifecycle, registers new Discord apps.
"""
import os, time, threading, json
from dotenv import load_dotenv
from worker.ai_worker import process_task, AGENT_PERSONAS
from memory import init_db, save_decision

load_dotenv()

FACTORY_TICK = int(os.environ.get("FACTORY_TICK_SECONDS", "30"))
BOT_REGISTRY_PATH = "bot_registry.json"

def load_registry() -> dict:
    if os.path.exists(BOT_REGISTRY_PATH):
        with open(BOT_REGISTRY_PATH) as f:
            return json.load(f)
    return {"bots": []}

def save_registry(registry: dict):
    with open(BOT_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

def register_bot(name, role, token_env, status="active"):
    registry = load_registry()
    entry = {"name": name, "role": role, "token_env": token_env, "status": status,
             "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    registry["bots"].append(entry)
    save_registry(registry)
    save_decision(f"Bot factory registered: {name}", f"Role: {role}", "registered")
    print(f"[BotFactory] Registered: {name} ({role})")
    return entry

def get_active_bots():
    return [b for b in load_registry().get("bots", []) if b.get("status") == "active"]

def health_check_all():
    for bot in get_active_bots():
        token = os.environ.get(bot["token_env"], "")
        print(f"[BotFactory] {bot['name']} -> {'OK' if token else 'MISSING TOKEN'}")

def spawn_bot_from_spec(spec):
    task = f"Write a complete Discord bot (discord.py 2.x) for: {spec}"
    code = process_task(task, "coder")
    safe = spec[:20].replace(" ","_").lower()
    path = f"bots/generated_{safe}.py"
    os.makedirs("bots", exist_ok=True)
    open(path, "w").write(code)
    register_bot(f"generated_{safe}", spec[:60], "DISCORD_TOKEN", "generated")
    return code

def factory_loop():
    init_db()
    print(f"[BotFactory] Started (tick={FACTORY_TICK}s)")
    registry = load_registry()
    names = {b["name"] for b in registry.get("bots", [])}
    if "openclaw-main" not in names:
        register_bot("openclaw-main", "MAIN BRAIN Discord gateway", "DISCORD_TOKEN")
    if "openclaw-slack" not in names:
        register_bot("openclaw-slack", "Slack coordination gateway", "SLACK_BOT_TOKEN")
    while True:
        try:
            health_check_all()
        except Exception as e:
            print(f"[BotFactory] Error: {e}")
        time.sleep(FACTORY_TICK)

if __name__ == "__main__":
    t = threading.Thread(target=factory_loop, daemon=True)
    t.start()
    try:
        while True: time.sleep(60)
    except KeyboardInterrupt:
        print("[BotFactory] Stopped.")
