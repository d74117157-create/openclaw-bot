"""Entry point for python -m gateway.bot"""
import sys
import os

# Fix: Add parent directory to path so 'memory' and 'worker' packages are found
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from gateway.bot import bot, DISCORD_TOKEN
import traceback

if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw Discord Bot Starting (via __main__)")
    print("Python path:", sys.path)
    print("=" * 60)
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
