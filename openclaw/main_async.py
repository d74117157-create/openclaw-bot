"""Async entry point with health server."""

import asyncio
import logging
import signal
import sys
import os

# Ensure original modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from openclaw.config import Config
from openclaw.health import HealthServer
from openclaw.utils.logging import setup_logging

logger = setup_logging("INFO")


async def run_with_health() -> None:
    """Run original OpenClaw with health server."""
    config = Config()

    # Start health server
    health = HealthServer(port=config.health_port)
    await health.start()

    # Import and run original main
    import main as original_main

    # The original main.py runs synchronously
    # We run it in a thread pool
    loop = asyncio.get_event_loop()

    def run_original():
        try:
            original_main  # Original runs on import or has main guard
        except Exception as e:
            logger.error(f"Original main error: {e}")

    # Run original in executor
    future = loop.run_in_executor(None, run_original)

    # Wait for shutdown signal
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    await stop_event.wait()

    # Cleanup
    await health.stop()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(run_with_health())
