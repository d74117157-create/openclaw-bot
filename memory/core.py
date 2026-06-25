"""
OpenClaw — memory/core.py
Core memory utilities and backward-compatible imports.
"""
import logging
from .db import init_db, save_task, update_task, get_stats, save_decision

logger = logging.getLogger("memory.core")

# Re-export common functions for backward compatibility
__all__ = ["init_db", "save_task", "update_task", "get_stats", "save_decision"]
