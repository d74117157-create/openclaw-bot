#!/usr/bin/env python3
"""Test that all imports work before starting the bot."""
import sys
print("Python path:", sys.path)
print("CWD:", __import__('os').getcwd())

errors = []

# Test memory package
try:
    import memory
    print("✅ memory imported")
    print("memory attributes:", dir(memory))
except Exception as e:
    print("❌ memory import failed:", e)
    errors.append(("memory", e))

try:
    from memory import init_db, save_task, update_task, get_stats, save_decision
    print("✅ memory functions imported")
except Exception as e:
    print("❌ memory functions import failed:", e)
    errors.append(("memory functions", e))

# Test worker.ai_worker
try:
    import worker.ai_worker
    print("✅ worker.ai_worker imported")
except Exception as e:
    print("❌ worker.ai_worker import failed:", e)
    errors.append(("worker.ai_worker", e))

# Test worker.slack_reporter
try:
    import worker.slack_reporter
    from worker.slack_reporter import task_started, agent_complete, task_complete
    print("✅ worker.slack_reporter imported")
    # Test the function signatures
    task_started("test_task", "test description", False)
    agent_complete("coder", "test task", "test result", True)
    task_complete("test_task", "test result")
    print("✅ slack_reporter functions callable with correct signatures")
except Exception as e:
    print("❌ worker.slack_reporter import or function call failed:", e)
    errors.append(("worker.slack_reporter", e))

# Test discord
try:
    import discord
    print("✅ discord.py imported (version %s)" % discord.__version__)
except Exception as e:
    print("❌ discord.py import failed:", e)
    errors.append(("discord.py", e))

# Test dotenv
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported")
except Exception as e:
    print("❌ python-dotenv import failed:", e)
    errors.append(("python-dotenv", e))

# Test aiohttp
try:
    import aiohttp
    print("✅ aiohttp imported")
except Exception as e:
    print("❌ aiohttp import failed:", e)
    errors.append(("aiohttp", e))

if errors:
    print("\n❌ %d import error(s) found:" % len(errors))
    for name, err in errors:
        print("  - %s: %s" % (name, err))
    sys.exit(1)
else:
    print("\n✅ All imports OK! Bot can start.")
