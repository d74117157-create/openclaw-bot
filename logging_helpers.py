"""Shared logging helpers for OpenClaw
Provides a simple setup_logging(name) and get_logger(name) wrapper used by gateway modules.
"""
import logging
import sys
from typing import Optional

_logger_configured = False


def setup_logging(name: Optional[str] = None, level: int = logging.INFO):
    global _logger_configured
    if _logger_configured:
        return
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    _logger_configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if not _logger_configured:
        setup_logging(name)
    return logging.getLogger(name)
