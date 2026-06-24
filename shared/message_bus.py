"""
OpenClaw shared message bus — in-process async pub/sub.
Provides both a class-based MessageBus and module-level functional API.
All agents import MessageBus; gateways may use functional API.
"""
import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Class-based async pub/sub message bus.
    Each agent swarm gets one shared instance passed via constructor.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, handler: Callable[..., Coroutine]) -> None:
        self._subscribers.setdefault(topic, [])
        if handler not in self._subscribers[topic]:
            self._subscribers[topic].append(handler)
            logger.debug("subscribed %s -> %s", topic, getattr(handler, "__name__", handler))

    def unsubscribe(self, topic: str, handler: Callable) -> None:
        if topic in self._subscribers:
            self._subscribers[topic] = [h for h in self._subscribers[topic] if h != handler]

    async def publish(self, topic: str, payload: Any = None) -> int:
        """Publish to topic; returns handler count. Exceptions are logged, not raised."""
        handlers = self._subscribers.get(topic, [])
        if not handlers:
            logger.debug("publish(%s): no subscribers", topic)
            return 0

        async def _safe(h):
            try:
                await h(topic, payload)
            except Exception as exc:
                logger.error("bus handler %s raised: %s", getattr(h, "__name__", h), exc, exc_info=True)

        await asyncio.gather(*[_safe(h) for h in handlers])
        return len(handlers)

    def get_topics(self) -> List[str]:
        return [t for t, hs in self._subscribers.items() if hs]


# ── Module-level singleton + functional API ──────────────────────────────────
_default_bus = MessageBus()


def subscribe(topic: str, handler: Callable[..., Coroutine]) -> None:
    _default_bus.subscribe(topic, handler)


def unsubscribe(topic: str, handler: Callable) -> None:
    _default_bus.unsubscribe(topic, handler)


async def publish(topic: str, payload: Any = None) -> int:
    return await _default_bus.publish(topic, payload)


def get_topics() -> List[str]:
    return _default_bus.get_topics()


def get_default_bus() -> MessageBus:
    """Return the module-level singleton bus (useful for agent constructors)."""
    return _default_bus
