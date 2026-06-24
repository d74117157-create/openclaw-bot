#!/usr/bin/env python3
"""Message Bus — Redis-backed pub/sub for inter-agent communication

Enables the swarm to coordinate:
- Agent-to-agent messaging
- Task delegation chains
- Broadcast notifications
- Event streaming
"""

import json
import logging
from typing import Callable, Dict, List
from memory import get_redis

logger = logging.getLogger("message_bus")


class MessageBus:
    """Redis-backed message bus for agent communication."""

    def __init__(self):
        self.redis = get_redis()
        self.subscribers: Dict[str, List[Callable]] = {}

    def publish(self, channel: str, message: dict):
        """Publish message to a channel."""
        payload = json.dumps(message)
        self.redis.publish(f"openclaw:bus:{channel}", payload)
        logger.debug("Published to %s: %s", channel, message.get("type", "unknown"))

    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)

    def broadcast(self, message: dict):
        """Broadcast to all agents."""
        self.publish("all", message)

    def agent_message(self, from_agent: str, to_agent: str, content: dict):
        """Send direct message between agents."""
        self.publish(f"agent:{to_agent}", {
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "timestamp": json.dumps({"now": True}),  # simplified
        })
