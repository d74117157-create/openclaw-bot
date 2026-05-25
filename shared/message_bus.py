"""
OpenClaw Unified Message Bus
Manages communication between Discord, Slack, Brain, and Workers.
"""
import asyncio
import json
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from shared.logging import get_logger

logger = get_logger(__name__)


class MessageType(Enum):
    """Message types for inter-bot communication."""
    TASK_SUBMITTED = "task_submitted"
    TASK_PROGRESS = "task_progress"
    SUBTASK_CREATED = "subtask_created"
    SUBTASK_COMPLETE = "subtask_complete"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    STATUS_UPDATE = "status_update"


@dataclass
class TaskMessage:
    """Structure for task messages."""
    message_type: MessageType
    task_id: str
    task_description: str
    agent: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    subtasks: Optional[List[Dict[str, str]]] = None
    source_platform: str = "discord"  # discord, slack, brain
    source_user: Optional[str] = None
    source_channel: Optional[str] = None
    timestamp: Optional[str] = None
    parent_task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict(), default=str)


class MessageBus:
    """Central message bus for all bots."""

    def __init__(self):
        """Initialize message bus."""
        self.subscribers: Dict[MessageType, List[Callable]] = {}
        self.message_history: List[TaskMessage] = []
        self.max_history = 1000
        logger.info("MessageBus initialized")

    def subscribe(self, message_type: MessageType, callback: Callable) -> None:
        """Subscribe to message type."""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        self.subscribers[message_type].append(callback)
        logger.debug(f"Subscribed to {message_type.value}")

    async def publish(self, message: TaskMessage) -> None:
        """Publish a message to all subscribers."""
        try:
            message.timestamp = message.timestamp or datetime.now().isoformat()
            self.message_history.append(message)

            # Keep history bounded
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history:]

            logger.info(f"Publishing: {message.message_type.value} for task {message.task_id}")

            # Call all subscribers for this message type
            if message.message_type in self.subscribers:
                for callback in self.subscribers[message.message_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        logger.error(f"Error in subscriber: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error publishing message: {e}", exc_info=True)

    def get_task_history(self, task_id: str) -> List[TaskMessage]:
        """Get message history for a task."""
        return [msg for msg in self.message_history if msg.task_id == task_id]

    def get_recent_messages(self, limit: int = 50) -> List[TaskMessage]:
        """Get recent messages."""
        return self.message_history[-limit:]


# Global message bus instance
_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get or create global message bus."""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


async def publish_message(
    message_type: MessageType,
    task_id: str,
    task_description: str,
    agent: str,
    status: str,
    result: Optional[str] = None,
    error: Optional[str] = None,
    subtasks: Optional[List[Dict[str, str]]] = None,
    source_platform: str = "discord",
    source_user: Optional[str] = None,
    source_channel: Optional[str] = None,
    parent_task_id: Optional[str] = None,
) -> None:
    """Convenience function to publish a message."""
    bus = get_message_bus()
    message = TaskMessage(
        message_type=message_type,
        task_id=task_id,
        task_description=task_description,
        agent=agent,
        status=status,
        result=result,
        error=error,
        subtasks=subtasks,
        source_platform=source_platform,
        source_user=source_user,
        source_channel=source_channel,
        parent_task_id=parent_task_id,
    )
    await bus.publish(message)
