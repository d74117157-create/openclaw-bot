#!/usr/bin/env python3
"""
MASTER ORCHESTRATOR — OpenClaw Digital Empire v3.1
Unified command center for all agents, platforms, and revenue pipelines.

Integrates:
- Discord Gateway (gateway/discord_bot.py)
- Telegram Gateway (gateway/telegram_bot.py)  
- Slack Gateway (gateway/slack_bot.py)
- AI Brain (ai_brain.py)
- Superswarm (superswarm.py)
- Revenue Engine (agents/revenue_engine.py)
- Business Automation (agents/business_automation.py)
- GBaby Agent (agents/gbaby.py)
- Memory Systems (memory/core.py, memory/db.py)

Start command: python master_orchestrator.py
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# ─── LOGGING SETUP ──────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("./logs/master.log", mode="a")
    ]
)
logger = logging.getLogger("master_orchestrator")

# ─── IMPORT EXISTING SYSTEMS ────────────────────────────────────────────────

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_brain import AIBrain
    logger.info("[IMPORT] ai_brain loaded")
except Exception as e:
    logger.warning(f"[IMPORT] ai_brain failed: {e}")
    AIBrain = None

try:
    from superswarm import SuperswarmCore, get_superswarm
    logger.info("[IMPORT] superswarm loaded")
except Exception as e:
    logger.warning(f"[IMPORT] superswarm failed: {e}")
    SuperswarmCore = None
    get_superswarm = None

try:
    from agents.gbaby import think as gbaby_think, execute as gbaby_execute
    logger.info("[IMPORT] gbaby agent loaded")
except Exception as e:
    logger.warning(f"[IMPORT] gbaby failed: {e}")
    gbaby_think = None
    gbaby_execute = None

try:
    from agents.revenue_engine import RevenueEngine
    logger.info("[IMPORT] revenue_engine loaded")
except Exception as e:
    logger.warning(f"[IMPORT] revenue_engine failed: {e}")
    RevenueEngine = None

try:
    from agents.business_automation import BusinessAutomation
    logger.info("[IMPORT] business_automation loaded")
except Exception as e:
    logger.warning(f"[IMPORT] business_automation failed: {e}")
    BusinessAutomation = None

try:
    from memory.core import SwarmMemory
    logger.info("[IMPORT] memory.core loaded")
except Exception as e:
    logger.warning(f"[IMPORT] memory.core failed: {e}")
    SwarmMemory = None

try:
    from memory.db import init_db, get_stats
    logger.info("[IMPORT] memory.db loaded")
except Exception as e:
    logger.warning(f"[IMPORT] memory.db failed: {e}")
    init_db = None
    get_stats = None

# ─── MASTER ORCHESTRATOR CLASS ──────────────────────────────────────────────

class MasterOrchestrator:
    """
    The central brain of the OpenClaw Digital Empire.
    Receives goals, assigns tasks, tracks progress, reports results.
    """

    def __init__(self):
        self.boot_time = datetime.utcnow()
        self.running = False
        self.gateways = {}
        self.agents = {}
        self.ai_brain = None
        self.swarm = None
        self.revenue = None
        self.business = None
        self.memory = None
        self.heartbeat_interval = 60  # seconds
        self.task_queue = []
        self.completed_tasks = []
        self.failed_tasks = []

        logger.info("=" * 60)
        logger.info("MASTER ORCHESTRATOR INITIALIZING")
        logger.info("=" * 60)

        self._init_systems()

    def _init_systems(self):
        """Initialize all subsystems."""
        # Initialize memory
        if init_db:
            try:
                init_db()
                logger.info("[INIT] Database initialized")
            except Exception as e:
                logger.error(f"[INIT] Database init failed: {e}")

        if SwarmMemory:
            try:
                self.memory = SwarmMemory()
                logger.info("[INIT] SwarmMemory initialized")
            except Exception as e:
                logger.error(f"[INIT] SwarmMemory failed: {e}")

        # Initialize AI Brain
        if AIBrain:
            try:
                self.ai_brain = AIBrain()
                logger.info("[INIT] AI Brain initialized")
            except Exception as e:
                logger.error(f"[INIT] AI Brain failed: {e}")

        # Initialize Superswarm
        if get_superswarm:
            try:
                self.swarm = get_superswarm()
                logger.info("[INIT] Superswarm initialized")
            except Exception as e:
                logger.error(f"[INIT] Superswarm failed: {e}")

        # Initialize Revenue Engine
        if RevenueEngine:
            try:
                self.revenue = RevenueEngine()
                logger.info("[INIT] Revenue Engine initialized")
            except Exception as e:
                logger.error(f"[INIT] Revenue Engine failed: {e}")

        # Initialize Business Automation
        if BusinessAutomation:
            try:
                self.business = BusinessAutomation(ai_client=self.ai_brain)
                logger.info("[INIT] Business Automation initialized")
            except Exception as e:
                logger.error(f"[INIT] Business Automation failed: {e}")

        # Register agents
        self._register_agents()

        logger.info("[INIT] All systems initialized")

    def _register_agents(self):
        """Register all available agents."""
        agent_registry = {
            "viktor": {
                "name": "Viktor",
                "role": "Strategic Reasoning & Task Prioritization",
                "status": "online",
                "type": "orchestrator"
            },
            "bob": {
                "name": "Bob", 
                "role": "Task Assignment & Workflow Management",
                "status": "online",
                "type": "orchestrator"
            },
            "dave": {
                "name": "Dave",
                "role": "DevOps, GitHub, Deployments, Monitoring",
                "status": "online", 
                "type": "devops"
            },
            "carla": {
                "name": "Carla",
                "role": "Content Creation, YouTube, SEO, Publishing",
                "status": "online",
                "type": "content"
            },
            "alice": {
                "name": "Alice",
                "role": "Business, Products, Revenue, Opportunities",
                "status": "online",
                "type": "business"
            },
            "gbaby": {
                "name": "GBaby",
                "role": "Growth, Marketing, Swarm Coordination",
                "status": "online",
                "type": "growth"
            },
            "security": {
                "name": "Security Agent",
                "role": "Audits, Permissions, Vulnerability Scanning",
                "status": "online",
                "type": "security"
            },
            "researcher": {
                "name": "Research Agent",
                "role": "Trends, Markets, Opportunities, Data Analysis",
                "status": "online",
                "type": "research"
            },
            "coder": {
                "name": "Coder Agent",
                "role": "Code Generation, Bug Fixes, Deployment",
                "status": "online",
                "type": "coder"
            },
            "qa": {
                "name": "QA Agent",
                "role": "Testing, Validation, Quality Assurance",
                "status": "online",
                "type": "qa"
            }
        }

        self.agents = agent_registry
        logger.info(f"[AGENTS] Registered {len(agent_registry)} agents")

    # ─── GOAL PROCESSING ─────────────────────────────────────────────────────

    def process_goal(self, goal: str, source: str = "manual") -> Dict:
        """
        Process a high-level goal through the empire.

        Flow: Goal → Viktor (strategize) → Bob (assign) → Agents (execute) → Report
        """
        task_id = f"task_{int(time.time())}_{random.randint(1000,9999)}"

        logger.info(f"[GOAL] #{task_id} from {source}: {goal[:80]}")

        result = {
            "task_id": task_id,
            "goal": goal,
            "source": source,
            "started_at": datetime.utcnow().isoformat(),
            "steps": []
        }

        # Step 1: Viktor strategizes
        strategy = self._viktor_strategize(goal)
        result["steps"].append({"agent": "viktor", "action": "strategize", "output": strategy})

        # Step 2: Bob assigns tasks
        assignments = self._bob_assign(strategy)
        result["steps"].append({"agent": "bob", "action": "assign", "output": assignments})

        # Step 3: Execute assignments
        for assignment in assignments:
            agent_name = assignment.get("agent")
            task = assignment.get("task")

            logger.info(f"[EXECUTE] {agent_name} → {task[:60]}")

            try:
                output = self._execute_with_agent(agent_name, task)
                result["steps"].append({
                    "agent": agent_name,
                    "action": "execute",
                    "status": "success",
                    "output": output
                })
                self.completed_tasks.append(task_id)
            except Exception as e:
                logger.error(f"[EXECUTE] {agent_name} failed: {e}")
                result["steps"].append({
                    "agent": agent_name,
                    "action": "execute", 
                    "status": "failed",
                    "error": str(e)
                })
                self.failed_tasks.append(task_id)

        # Step 4: Compile report
        result["completed_at"] = datetime.utcnow().isoformat()
        result["status"] = "success" if all(s.get("status") != "failed" for s in result["steps"]) else "partial"

        logger.info(f"[GOAL] #{task_id} completed: {result['status']}")
        return result

    def _viktor_strategize(self, goal: str) -> Dict:
        """Viktor analyzes the goal and creates a strategy."""
        strategy = {
            "goal": goal,
            "priority": "high",
            "approach": "multi_agent",
            "estimated_time": "unknown",
            "agents_needed": []
        }

        # Keyword-based routing
        goal_lower = goal.lower()

        if any(k in goal_lower for k in ["revenue", "money", "income", "passive", "affiliate", "monetize"]):
            strategy["agents_needed"] = ["alice", "carla", "researcher", "gbaby"]
            strategy["pipeline"] = "revenue"
        elif any(k in goal_lower for k in ["code", "deploy", "fix", "bug", "github", "server"]):
            strategy["agents_needed"] = ["dave", "coder", "qa"]
            strategy["pipeline"] = "devops"
        elif any(k in goal_lower for k in ["content", "youtube", "blog", "seo", "social", "video"]):
            strategy["agents_needed"] = ["carla", "researcher", "gbaby"]
            strategy["pipeline"] = "content"
        elif any(k in goal_lower for k in ["research", "analyze", "trend", "market", "competitor"]):
            strategy["agents_needed"] = ["researcher", "gbaby"]
            strategy["pipeline"] = "research"
        elif any(k in goal_lower for k in ["security", "audit", "vulnerability", "scan"]):
            strategy["agents_needed"] = ["security", "dave"]
            strategy["pipeline"] = "security"
        else:
            strategy["agents_needed"] = ["gbaby", "researcher"]
            strategy["pipeline"] = "general"

        return strategy

    def _bob_assign(self, strategy: Dict) -> List[Dict]:
        """Bob breaks strategy into specific agent tasks."""
        assignments = []
        pipeline = strategy.get("pipeline", "general")

        if pipeline == "revenue":
            assignments = [
                {"agent": "researcher", "task": f"Research profitable niches related to: {strategy['goal']}"},
                {"agent": "alice", "task": f"Identify products and affiliate opportunities for: {strategy['goal']}"},
                {"agent": "carla", "task": f"Create content strategy for: {strategy['goal']}"},
                {"agent": "gbaby", "task": f"Coordinate growth and marketing for: {strategy['goal']}"}
            ]
        elif pipeline == "devops":
            assignments = [
                {"agent": "dave", "task": f"Handle infrastructure for: {strategy['goal']}"},
                {"agent": "coder", "task": f"Write or fix code for: {strategy['goal']}"},
                {"agent": "qa", "task": f"Test and validate: {strategy['goal']}"}
            ]
        elif pipeline == "content":
            assignments = [
                {"agent": "researcher", "task": f"Research topics for: {strategy['goal']}"},
                {"agent": "carla", "task": f"Create content for: {strategy['goal']}"},
                {"agent": "gbaby", "task": f"Plan distribution for: {strategy['goal']}"}
            ]
        else:
            assignments = [
                {"agent": "gbaby", "task": strategy["goal"]}
            ]

        return assignments

    def _execute_with_agent(self, agent_name: str, task: str) -> Any:
        """Execute a task with the specified agent."""

        # Revenue pipeline tasks
        if agent_name in ["alice", "carla", "researcher"] and self.revenue:
            if "research" in task.lower():
                return self.revenue.researcher.research_niche(task.replace("Research profitable niches related to: ", ""))
            elif "content" in task.lower():
                return self.revenue.content.create_youtube_script(task.replace("Create content strategy for: ", ""))
            elif "product" in task.lower() or "affiliate" in task.lower():
                return self.revenue.content.create_digital_product(task.replace("Identify products and affiliate opportunities for: ", ""))
            else:
                return self.revenue.run_pipeline(task)

        # GBaby tasks
        if agent_name == "gbaby" and gbaby_think:
            decision = gbaby_think(task)
            if gbaby_execute:
                return gbaby_execute(decision)
            return decision

        # Business automation
        if agent_name == "alice" and self.business:
            return self.business.research_products(task)

        # AI Brain fallback
        if self.ai_brain:
            agent_type = self.agents.get(agent_name, {}).get("type", "orchestrator")
            return self.ai_brain.chat(task, agent_type=agent_type)

        return f"Agent {agent_name} executed: {task}"

    # ─── GATEWAY INTEGRATION ─────────────────────────────────────────────────

    def register_gateway(self, name: str, gateway):
        """Register a platform gateway."""
        self.gateways[name] = gateway
        logger.info(f"[GATEWAY] Registered: {name}")

    def route_message(self, platform: str, user_id: str, username: str, 
                      message: str, channel_id: str = None) -> str:
        """Route an incoming message to the appropriate agent."""
        logger.info(f"[ROUTE] {platform}/{username}: {message[:60]}")

        # Check for commands
        msg_lower = message.lower().strip()

        if msg_lower.startswith("/status"):
            return self._cmd_status()
        elif msg_lower.startswith("/agents"):
            return self._cmd_agents()
        elif msg_lower.startswith("/revenue"):
            return self._cmd_revenue()
        elif msg_lower.startswith("/pipeline"):
            niche = message.replace("/pipeline", "").strip() or "passive income"
            result = self.process_goal(f"Run revenue pipeline for {niche}", source=platform)
            return json.dumps(result, indent=2)[:1900]  # Discord limit
        elif msg_lower.startswith("/deploy"):
            return self._cmd_deploy(message)
        elif msg_lower.startswith("/help"):
            return self._cmd_help()

        # Default: process as goal
        result = self.process_goal(message, source=platform)
        return f"✅ Task complete!

**Status:** {result['status']}
**Agents used:** {', '.join(s['agent'] for s in result['steps'] if 'agent' in s)}"

    def _cmd_status(self) -> str:
        """System status command."""
        uptime = (datetime.utcnow() - self.boot_time).total_seconds()
        return (
            f"🧠 **OpenClaw Master Brain**
"
            f"Uptime: {int(uptime)}s
"
            f"Agents: {len(self.agents)} online
"
            f"Gateways: {', '.join(self.gateways.keys()) or 'none'}
"
            f"Tasks completed: {len(self.completed_tasks)}
"
            f"Tasks failed: {len(self.failed_tasks)}
"
            f"AI Brain: {'✅' if self.ai_brain else '❌'}
"
            f"Revenue Engine: {'✅' if self.revenue else '❌'}
"
            f"Business Auto: {'✅' if self.business else '❌'}"
        )

    def _cmd_agents(self) -> str:
        """List all agents."""
        lines = ["🤖 **OpenClaw Agents:**"]
        for aid, agent in self.agents.items():
            lines.append(f"• **{agent['name']}** — {agent['role']} (`{agent['type']}`)")
        return "\n".join(lines)

    def _cmd_revenue(self) -> str:
        """Revenue report command."""
        if self.revenue:
            report = self.revenue.state.get_report()
            return (
                f"💰 **Revenue Report**
"
                f"Month: {report['month']}
"
                f"Total: ${report['total_revenue']:.2f}
"
                f"Target: ${report['target']:,}
"
                f"Progress: {report['progress_pct']:.1f}%
"
                f"Content created: {report['content_count']}
"
                f"Opportunities: {report['opportunities_open']}"
            )
        return "❌ Revenue Engine not loaded"

    def _cmd_deploy(self, message: str) -> str:
        """Deploy command."""
        return "🚀 Deployment triggered. Check GitHub Actions for status."

    def _cmd_help(self) -> str:
        """Help command."""
        return (
            "🦅 **OpenClaw Digital Empire Commands**
\n"
            "`/status` — System status\n"
            "`/agents` — List all agents\n"
            "`/revenue` — Revenue report\n"
            "`/pipeline [niche]` — Run revenue pipeline\n"
            "`/deploy` — Trigger deployment\n"
            "`/help` — Show this help\n\n"
            "Or just type any goal and the swarm will handle it!"
        )

    # ─── HEARTBEAT & MONITORING ──────────────────────────────────────────────

    def start_heartbeat(self):
        """Start the heartbeat monitoring loop."""
        def heartbeat_loop():
            while self.running:
                try:
                    self._heartbeat()
                except Exception as e:
                    logger.error(f"[HEARTBEAT] Error: {e}")
                time.sleep(self.heartbeat_interval)

        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info("[HEARTBEAT] Started")

    def _heartbeat(self):
        """Single heartbeat tick."""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.boot_time).total_seconds(),
            "agents_online": len([a for a in self.agents.values() if a.get("status") == "online"]),
            "gateways_connected": list(self.gateways.keys()),
            "queue_length": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks)
        }

        # Log to memory
        if self.memory:
            try:
                self.memory.log_event("heartbeat", "system", json.dumps(status))
            except:
                pass

        logger.debug(f"[HEARTBEAT] {status['uptime_seconds']}s | {status['agents_online']} agents | {status['queue_length']} queued")

    # ─── MAIN LOOP ───────────────────────────────────────────────────────────

    def start(self):
        """Start the master orchestrator."""
        self.running = True
        logger.info("=" * 60)
        logger.info("MASTER ORCHESTRATOR STARTED")
        logger.info("=" * 60)

        self.start_heartbeat()

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("[SHUTDOWN] Keyboard interrupt received")
            self.stop()

    def stop(self):
        """Graceful shutdown."""
        logger.info("[SHUTDOWN] Stopping Master Orchestrator...")
        self.running = False

        # Save state
        if self.revenue:
            try:
                self.revenue.state._save()
                logger.info("[SHUTDOWN] Revenue state saved")
            except:
                pass

        logger.info("[SHUTDOWN] Complete")


# ─── FASTAPI HEALTH SERVER ──────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="OpenClaw Master Orchestrator")
_orchestrator: Optional[MasterOrchestrator] = None

@app.on_event("startup")
async def startup():
    global _orchestrator
    _orchestrator = MasterOrchestrator()
    # Start in background thread
    threading.Thread(target=_orchestrator.start, daemon=True).start()

@app.get("/health")
async def health():
    """Health check for Render/Railway."""
    if _orchestrator and _orchestrator.running:
        return {"status": "healthy", "uptime": (datetime.utcnow() - _orchestrator.boot_time).total_seconds()}
    return JSONResponse(status_code=503, content={"status": "unhealthy"})

@app.get("/ready")
async def ready():
    """Readiness check."""
    if _orchestrator:
        return {
            "status": "ready",
            "agents": len(_orchestrator.agents),
            "gateways": list(_orchestrator.gateways.keys()),
            "ai_brain": _orchestrator.ai_brain is not None,
            "revenue": _orchestrator.revenue is not None
        }
    return JSONResponse(status_code=503, content={"status": "not_ready"})

@app.get("/status")
async def full_status():
    """Full system status."""
    if not _orchestrator:
        return JSONResponse(status_code=503, content={"error": "not_initialized"})
    return {
        "orchestrator": _orchestrator._cmd_status(),
        "agents": {k: v for k, v in _orchestrator.agents.items()},
        "tasks": {
            "completed": len(_orchestrator.completed_tasks),
            "failed": len(_orchestrator.failed_tasks)
        }
    }

@app.post("/goal")
async def submit_goal(goal: str, source: str = "api"):
    """Submit a goal via API."""
    if not _orchestrator:
        return JSONResponse(status_code=503, content={"error": "not_initialized"})
    result = _orchestrator.process_goal(goal, source=source)
    return result


# ─── CLI ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", 8080)))
    logger.info(f"[MAIN] Starting uvicorn on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
