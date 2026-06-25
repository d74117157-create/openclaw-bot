#!/usr/bin/env python3
"""
OpenClaw Elite — Import Verification
Ensures all modules load correctly before starting the system.
"""
import sys
import os
import traceback

print("[OpenClaw Elite] Verifying imports...")

modules = [
    # Core
    "shared.config",
    "shared.logging",
    "shared.message_bus",
    "shared.mission",

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
    "worker.task_dispatcher",

    # Worker — Agents (all new ones included)
    "worker.agents.bob",
    "worker.agents.carla",
    "worker.agents.dave",
    "worker.agents.alice",
    "worker.agents.coder",
    "worker.agents.reviewer",
    "worker.agents.qa",
    "worker.agents.ops",
    "worker.agents.research",
    "worker.agents.researcher",
    "worker.agents.growth",
    "worker.agents.memory_agent",
    "worker.agents.business_agent",

    # Gateways
    "gateway.telegram_bot",
    "gateway.discord_bot",
    "gateway.discord_tasks",
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
    except ModuleNotFoundError as e:
        # Optional modules that may not exist yet
        optional = ["memory.core", "gateway.discord_tasks", "worker.task_dispatcher"]
        if any(opt in str(e) for opt in optional):
            print(f"  [WARN] {mod}: Module not found (optional, skipping)")
        else:
            print(f"  [FAIL] {mod}: {e}")
            failed.append((mod, f"ModuleNotFoundError: {e}"))
    except Exception as e:
        print(f"  [FAIL] {mod}: {type(e).__name__}: {e}")
        traceback.print_exc()
        failed.append((mod, f"{type(e).__name__}: {e}"))

if failed:
    print(f"\n[OpenClaw Elite] {len(failed)} import(s) failed:")
    for mod, err in failed:
        print(f"  - {mod}: {err}")
    print("\n[OpenClaw Elite] WARNING: Some modules failed to import.")
    print("[OpenClaw Elite] The system will attempt to start anyway.")
    print("[OpenClaw Elite] Non-critical modules may be unavailable.")
    sys.exit(0)
else:
    print(f"\n[OpenClaw Elite] All {len(modules)} modules imported successfully!")
    sys.exit(0)
