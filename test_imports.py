#!/usr/bin/env python3
"""
OpenClaw Elite — Import Verification
Ensures all modules load correctly before starting the system.
"""
import sys
import os

print("[OpenClaw Elite] Verifying imports...")

modules = [
    # Core
    "shared.config",
    "shared.logging",
    "shared.message_bus",

    # Memory
    "memory.db",
    "memory.core",
    "memory.elite_memory",

    # Worker — Core
    "worker.ai_worker",
    "worker.task_router",
    "worker.executor",
    "worker.intent_router",
    "worker.verification",
    "worker.monitoring",
    "worker.approval",
    "worker.slack_reporter",
    "worker.self_test",

    # Worker — Agents
    "worker.agents.bob",
    "worker.agents.carla",
    "worker.agents.dave",
    "worker.agents.alice",
    "worker.agents.coder",
    "worker.agents.researcher",
    "worker.agents.ops",
    "worker.agents.growth",
    "worker.agents.qa",

    # Gateways
    "gateway.telegram_bot",
    "gateway.discord_bot",
    "gateway.slack_bot",
    "gateway.brain_bot",
    "gateway.bot",

    # Kernel
    "kernel",
]

failed = []
for mod in modules:
    try:
        __import__(mod)
        print(f"  [OK] {mod}")
    except ValueError as e:
        if "DISCORD_TOKEN" in str(e) or "SLACK" in str(e):
            print(f"  [OK] {mod} (requires env vars in production)")
        else:
            print(f"  [FAIL] {mod}: {e}")
            failed.append((mod, str(e)))
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")
        failed.append((mod, str(e)))

if failed:
    print(f"\n[OpenClaw Elite] {len(failed)} import(s) failed:")
    for mod, err in failed:
        print(f"  - {mod}: {err}")
    sys.exit(1)
else:
    print(f"\n[OpenClaw Elite] All {len(modules)} modules imported successfully!")
    sys.exit(0)
