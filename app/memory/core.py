"""OpenClaw Empire — Memory Core"""
from typing import Dict, Any, Optional
from datetime import datetime

class MemoryStore:
    """Simple in-memory store with persistence hooks."""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._history: list = []

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._history.append({"op": "set", "key": key, "time": datetime.utcnow().isoformat()})

    def recall(self, agent: str, context: str = "") -> str:
        """Recall memory for an agent."""
        memories = self._data.get(f"agent:{agent}", [])
        if not memories:
            return "No prior memory."
        return f"Prior context: {len(memories)} memories stored."

    def store(self, agent: str, memory: str):
        key = f"agent:{agent}"
        if key not in self._data:
            self._data[key] = []
        self._data[key].append({"memory": memory, "time": datetime.utcnow().isoformat()})

# Global instance
memory_store = MemoryStore()
