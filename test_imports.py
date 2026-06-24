#!/usr/bin/env python3
"""Test that all imports work before starting the bot."""
import sys
print("Python path:", sys.path)
print("CWD:", __import__('os').getcwd())

try:
    import memory
    print("✅ memory imported")
    print("memory attributes:", dir(memory))
except Exception as e:
    print("❌ memory import failed:", e)
    sys.exit(1)

try:
    from memory import init_db, save_task, update_task, get_stats, save_decision
    print("✅ memory functions imported")
except Exception as e:
    print("❌ memory functions import failed:", e)
    sys.exit(1)

try:
    import worker.ai_worker
    print("✅ worker.ai_worker imported")
except Exception as e:
    print("❌ worker.ai_worker import failed:", e)
    sys.exit(1)

try:
    import worker.slack_reporter
    print("✅ worker.slack_reporter imported")
except Exception as e:
    print("❌ worker.slack_reporter import failed:", e)
    sys.exit(1)

print("All imports OK!")
