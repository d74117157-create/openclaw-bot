import asyncio
import random
import math
from typing import Callable, Awaitable, Any
from loguru import logger

async def retry_with_backoff(func: Callable[..., Awaitable[Any]], *args, retries: int = 5, base: float = 0.5, max_delay: float = 30.0, **kwargs):
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            delay = min(max_delay, base * (2 ** attempt) + random.random())
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay:.1f}s")
            await asyncio.sleep(delay)
    raise RuntimeError('All retries failed')

async def exponential_backoff(attempt: int, base: float = 0.5, max_delay: float = 30.0) -> float:
    return min(max_delay, base * (2 ** attempt))
