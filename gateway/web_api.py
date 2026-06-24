#!/usr/bin/env python3
"""Web API Gateway — REST API for OpenClaw Swarm

SUPERIOR TO VIKTOR: Viktor is chat-only. OpenClaw has a full REST API
for integrations, webhooks, and third-party tools.

Endpoints:
  POST /api/v1/ask         — Submit a task
  GET  /api/v1/status       — System status
  GET  /api/v1/agents       — List agents
  GET  /api/v1/tasks/<id>   — Get task status
  POST /api/v1/deploy       — Trigger deployment
  POST /webhook/github      — GitHub webhook
  POST /webhook/slack       — Slack webhook
  GET  /health              — Health check
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from aiohttp import web

from memory import get_redis, push_task, get_task_status
from worker.slack_reporter import SlackReporter

logger = logging.getLogger("web_gateway")
API_KEY = os.getenv("OPENCLAW_API_KEY", "")


class WebGateway:
    """Web API server for external integrations."""

    def __init__(self, swarm, port: int = 8080):
        self.swarm = swarm
        self.swarm.gateways["web"] = self
        self.port = port
        self.app = web.Application()
        self.slack = SlackReporter()
        self._setup_routes()

    def _setup_routes(self):
        """Configure API routes."""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/api/v1/status", self.api_status)
        self.app.router.add_get("/api/v1/agents", self.api_agents)
        self.app.router.add_post("/api/v1/ask", self.api_ask)
        self.app.router.add_get("/api/v1/tasks/{task_id}", self.api_task_status)
        self.app.router.add_post("/api/v1/deploy", self.api_deploy)
        self.app.router.add_post("/webhook/github", self.webhook_github)
        self.app.router.add_post("/webhook/slack", self.webhook_slack)

    async def start(self):
        """Start the web server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()
        logger.info("Web API listening on port %d", self.port)

        # Keep alive
        while True:
            await asyncio.sleep(3600)

    async def send_message(self, channel_id: str, content: str, task_id: str = None):
        """Web doesn't send messages — it returns responses via HTTP."""
        pass

    def _check_auth(self, request: web.Request) -> bool:
        """Check API key authentication."""
        if not API_KEY:
            return True  # No auth required if key not set

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:] == API_KEY
        return False

    # ─── Route Handlers ────────────────────────────────────────────────────────

    async def health_check(self, request: web.Request):
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "service": "openclaw-swarm",
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def api_status(self, request: web.Request):
        """Get swarm status."""
        stats = self.swarm.get_stats()
        return web.json_response(stats)

    async def api_agents(self, request: web.Request):
        """List all agents."""
        agents = []
        for name, agent in self.swarm.agents.items():
            agents.append({
                "name": name,
                "type": agent.agent_type,
                "status": "online" if agent.is_ready() else "booting",
                "capabilities": agent.capabilities,
            })
        return web.json_response({"agents": agents})

    async def api_ask(self, request: web.Request):
        """Submit a task to the swarm."""
        if not self._check_auth(request):
            return web.json_response({"error": "Unauthorized"}, status=401)

        try:
            data = await request.json()
            message = data.get("message", "")
            platform = data.get("platform", "web")
            user_id = data.get("user_id", "anonymous")

            if not message:
                return web.json_response({"error": "message required"}, status=400)

            task_id = await self.swarm.route_message(
                platform=platform,
                user_id=user_id,
                username=user_id,
                message=message,
                channel_id="web_api",
            )

            return web.json_response({
                "task_id": task_id,
                "status": "queued",
                "message": "Task submitted successfully",
            })

        except Exception as e:
            logger.exception("API ask failed")
            return web.json_response({"error": str(e)}, status=500)

    async def api_task_status(self, request: web.Request):
        """Get task status by ID."""
        task_id = request.match_info["task_id"]
        status = get_task_status(task_id)

        if not status:
            return web.json_response({"error": "Task not found"}, status=404)

        return web.json_response(status)

    async def api_deploy(self, request: web.Request):
        """Trigger a deployment."""
        if not self._check_auth(request):
            return web.json_response({"error": "Unauthorized"}, status=401)

        try:
            data = await request.json()
            repo = data.get("repo")
            branch = data.get("branch", "main")

            if not repo:
                return web.json_response({"error": "repo required"}, status=400)

            task_id = await self.swarm.route_message(
                platform="web",
                user_id="api",
                username="api",
                message="deploy %s %s" % (repo, branch),
                channel_id="web_api",
            )

            return web.json_response({
                "task_id": task_id,
                "status": "queued",
                "message": "Deployment triggered",
            })

        except Exception as e:
            logger.exception("API deploy failed")
            return web.json_response({"error": str(e)}, status=500)

    async def webhook_github(self, request: web.Request):
        """Handle GitHub webhooks (push, PR, issues)."""
        try:
            data = await request.json()
            event = request.headers.get("X-GitHub-Event", "unknown")

            logger.info("GitHub webhook: %s", event)

            # Route to ops agent for CI/CD handling
            if event in ["push", "pull_request"]:
                repo = data.get("repository", {}).get("full_name", "unknown")
                ref = data.get("ref", "unknown")

                await self.swarm.route_message(
                    platform="github",
                    user_id="github",
                    username="github",
                    message="github %s on %s (%s)" % (event, repo, ref),
                    channel_id="webhook",
                )

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.exception("GitHub webhook failed")
            return web.json_response({"error": str(e)}, status=500)

    async def webhook_slack(self, request: web.Request):
        """Handle Slack slash commands and events."""
        try:
            data = await request.post()

            command = data.get("command", "")
            text = data.get("text", "")
            user_id = data.get("user_id", "")
            channel_id = data.get("channel_id", "")

            logger.info("Slack command: %s %s", command, text)

            if command == "/openclaw":
                task_id = await self.swarm.route_message(
                    platform="slack",
                    user_id=user_id,
                    username=user_id,
                    message=text,
                    channel_id=channel_id,
                )
                return web.json_response({
                    "response_type": "in_channel",
                    "text": "Task queued: `%s`" % task_id,
                })

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.exception("Slack webhook failed")
            return web.json_response({"error": str(e)}, status=500)
