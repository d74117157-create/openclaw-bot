"""Tool registry — inspired by Copilot SDK defineTool pattern."""
import asyncio, logging
from typing import Dict, Callable, Any, List
from dataclasses import dataclass
logger = logging.getLogger("openclaw.tools")

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable

class ToolRegistry:
    def __init__(self): self._tools: Dict[str, ToolDefinition] = {}
    def register(self, name: str, description: str, parameters: Dict[str, Any]):
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(name=name, description=description, parameters=parameters, handler=func)
            logger.info(f"Tool registered: {name}"); return func
        return decorator
    async def call(self, name: str, args: Dict[str, Any]) -> Any:
        if name not in self._tools: raise ValueError(f"Tool '{name}' not found.")
        tool = self._tools[name]
        for param in tool.parameters.get("required", []):
            if param not in args: raise ValueError(f"Missing '{param}' for tool '{name}'")
        if asyncio.iscoroutinefunction(tool.handler): return await tool.handler(**args)
        return tool.handler(**args)
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}} for t in self._tools.values()]

registry = ToolRegistry()

@registry.register(name="get_weather", description="Get current weather for a city", parameters={"type": "object", "properties": {"city": {"type": "string", "description": "City name"}}, "required": ["city"]})
async def get_weather(city: str) -> Dict[str, Any]:
    import random
    return {"city": city, "temperature": f"{random.randint(50,80)}°F", "condition": random.choice(["sunny","cloudy","rainy","partly cloudy"])}

@registry.register(name="get_swarm_status", description="Get swarm status", parameters={"type": "object", "properties": {}, "required": []})
async def get_swarm_status() -> Dict[str, Any]:
    return {"status": "online", "agents": 6, "platforms": ["discord","telegram","slack"]}
