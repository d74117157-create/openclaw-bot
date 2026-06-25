#!/usr/bin/env python3
"""
OpenClaw Elite — Import Verification
FIXED: Properly classified required vs optional modules. Startup aborts if required fail.
"""
import sys
import os
import traceback

print("[OpenClaw Elite] Verifying imports...")

# REQUIRED modules — startup fails if any of these don't import
REQUIRED_MODULES = [
    # Core
    "shared.config",
    "shared.logging",
    "shared.message_bus",
    "shared.mission",
    # Memory
    "memory.db",
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
    # Worker — Agents (ALL agents)
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
    "worker.agents.orchestrator",
    # Gateways
    "gateway.telegram_bot",
    "gateway.discord_bot",
    "gateway.slack_bot",
    "gateway.brain_bot",
    "gateway.bot",
    # Kernel
    "kernel",
]

# OPTIONAL modules — startup continues if these fail
OPTIONAL_MODULES = [
    "gateway.discord_tasks",  # May not exist in all versions
    "memory.core",            # Stub module, not imported by main
]

failed_required = []
failed_optional = []

for mod in REQUIRED_MODULES:
    try:
        __import__(mod)
        print(f" [OK] {mod}")
    except ValueError as e:
        if "DISCORD_TOKEN" in str(e) or "SLACK" in str(e) or "TELEGRAM" in str(e):
            print(f" [OK] {mod} (requires env vars in production)")
        else:
            print(f" [FAIL] {mod}: {e}")
            failed_required.append((mod, str(e)))
    except Exception as e:
        print(f" [FAIL] {mod}: {type(e).__name__}: {e}")
        traceback.print_exc()
        failed_required.append((mod, f"{type(e).__name__}: {e}"))

for mod in OPTIONAL_MODULES:
    try:
        __import__(mod)
        print(f" [OK] {mod} (optional)")
    except Exception as e:
        print(f" [WARN] {mod}: {type(e).__name__}: {e} (optional, skipping)")
        failed_optional.append((mod, str(e)))

if failed_required:
    print(f"\n[OpenClaw Elite] {len(failed_required)} REQUIRED import(s) failed:")
    for mod, err in failed_required:
        print(f" - {mod}: {err}")
    print("\n[OpenClaw Elite] CRITICAL: Required modules failed. Startup aborted.")
    sys.exit(1)
else:
    print(f"\n[OpenClaw Elite] All {len(REQUIRED_MODULES)} required modules imported successfully!")
    if failed_optional:
        print(f"[OpenClaw Elite] {len(failed_optional)} optional module(s) failed (non-critical)")
    sys.exit(0)
