"""
OpenClaw Task Dispatcher — routes tasks from Discord → Agents → Results → Storage
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from memory import save_task, update_task, get_task, get_pending_tasks
from worker.agents import AGENT_DISPATCH
from shared.message_bus import get_default_bus

logger = logging.getLogger(__name__)

class TaskDispatcher:
    """Central task router — receives from Discord, dispatches to agents."""
    
    def __init__(self):
        self.bus = get_default_bus()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def submit_task(self, task_desc: str, agent_name: str = "orchestrator", 
                         requester: str = "discord", channel_id: str = None) -> str:
        """
        Submit a task for execution.
        Returns task_id for tracking.
        """
        # Save to DB
        task_id = save_task(task_desc, agent_name, requester)
        logger.info(f"📋 Task {task_id}: {task_desc} → {agent_name}")
        
        # Track locally
        self.active_tasks[task_id] = {
            "desc": task_desc,
            "agent": agent_name,
            "requester": requester,
            "channel_id": channel_id,
            "status": "pending",
            "submitted_at": datetime.now().isoformat(),
        }
        
        # Publish to bus for any listeners
        await self.bus.publish("task.submitted", {
            "task_id": task_id,
            "description": task_desc,
            "agent": agent_name,
            "channel_id": channel_id
        })
        
        return task_id
    
    async def execute_task(self, task_id: str) -> str:
        """Execute a pending task via its assigned agent."""
        task_data = self.active_tasks.get(task_id)
        if not task_data:
            task_data = get_task(task_id)
        
        if not task_data:
            logger.error(f"Task {task_id} not found")
            return "Task not found"
        
        agent_name = task_data.get("agent", "orchestrator")
        task_desc = task_data.get("desc") or task_data.get("description")
        
        # Get agent function
        agent_fn = AGENT_DISPATCH.get(agent_name)
        if not agent_fn:
            update_task(task_id, f"Agent '{agent_name}' not found", "failed")
            logger.error(f"Agent {agent_name} not found")
            return f"Agent {agent_name} not found"
        
        try:
            update_task(task_id, "executing", "running")
            logger.info(f"🚀 Executing {agent_name}: {task_desc}")
            
            # Run agent
            result = agent_fn(task_desc)
            
            # Update task
            update_task(task_id, result, "done")
            logger.info(f"✅ Task {task_id} done: {result[:100]}")
            
            # Publish result
            await self.bus.publish("task.completed", {
                "task_id": task_id,
                "result": result,
                "agent": agent_name
            })
            
            return result
        
        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            update_task(task_id, error_msg, "failed")
            logger.error(f"❌ Task {task_id} failed: {e}", exc_info=True)
            
            await self.bus.publish("task.failed", {
                "task_id": task_id,
                "error": error_msg,
                "agent": agent_name
            })
            
            return error_msg
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status from local cache or DB."""
        local = self.active_tasks.get(task_id)
        if local:
            return local
        
        db_task = get_task(task_id)
        if db_task:
            return {
                "task_id": task_id,
                "desc": db_task.get("description"),
                "status": db_task.get("status"),
                "result": db_task.get("result"),
            }
        
        return {"error": "Task not found"}
    
    async def list_pending(self) -> list:
        """List all pending tasks."""
        return get_pending_tasks()


# Singleton dispatcher
_dispatcher = TaskDispatcher()

async def submit_task(task_desc: str, agent: str = "orchestrator", 
                     requester: str = "discord", channel_id: str = None) -> str:
    return await _dispatcher.submit_task(task_desc, agent, requester, channel_id)

async def execute_task(task_id: str) -> str:
    return await _dispatcher.execute_task(task_id)

async def get_task_status(task_id: str) -> Dict[str, Any]:
    return await _dispatcher.get_task_status(task_id)

async def list_pending() -> list:
    return await _dispatcher.list_pending()

def get_dispatcher() -> TaskDispatcher:
    return _dispatcher
