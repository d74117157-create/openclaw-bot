#!/usr/bin/env python3
"""Ops Agent — Infrastructure, CI/CD, monitoring

SUPERIOR TO VIKTOR: Viktor can't manage infrastructure.
OpenClaw Ops handles servers, deployments, and monitoring.

Capabilities:
- Server provisioning and configuration
- CI/CD pipeline management
- Docker container management
- Monitoring and alerting setup
- Log aggregation
- Security auditing
"""

import os
import logging

from worker.agents.orchestrator import BaseAgent
from shared.message_bus import MessageBus

logger = logging.getLogger("agent.ops")


class OpsAgent(BaseAgent):
    """Specialist agent for operations tasks."""

    def __init__(self, bus: MessageBus):
        super().__init__(bus, "ops", "devops_engineer")
        self.capabilities = [
            "infrastructure", "ci_cd", "docker", "monitoring",
            "security", "logging", "backup", "scaling"
        ]

    async def process(self, context: dict) -> str:
        """Process ops tasks."""
        message = context.get("message", "")
        msg_lower = message.lower()

        if "docker" in msg_lower or "container" in msg_lower:
            return await self._docker_task(message)
        elif "monitor" in msg_lower or "alert" in msg_lower:
            return await self._monitoring_task(message)
        elif "security" in msg_lower or "audit" in msg_lower:
            return await self._security_audit(message)
        elif "deploy" in msg_lower or "server" in msg_lower:
            return await self._deploy_infrastructure(message)
        else:
            return await self._general_ops(message)

    async def _docker_task(self, prompt: str) -> str:
        """Generate Docker configurations."""
        system = """You are a Docker expert. Generate production-ready Docker configurations:
- Multi-stage builds for optimization
- Security best practices (non-root user, minimal base images)
- Health checks
- Proper logging
- Resource limits"""
        return await self._call_llm(system, prompt)

    async def _monitoring_task(self, prompt: str) -> str:
        """Set up monitoring."""
        system = """You are a monitoring expert. Generate configurations for:
- Prometheus metrics
- Grafana dashboards
- AlertManager rules
- Uptime checks
- Log aggregation (Loki/ELK)"""
        return await self._call_llm(system, prompt)

    async def _security_audit(self, prompt: str) -> str:
        """Perform security audit."""
        system = """You are a security engineer. Audit the system for:
1. Vulnerabilities (OWASP Top 10)
2. Misconfigurations
3. Access control issues
4. Data exposure risks
5. Compliance gaps (GDPR, SOC2)"""
        return await self._call_llm(system, prompt)

    async def _deploy_infrastructure(self, prompt: str) -> str:
        """Generate infrastructure code."""
        system = """You are a cloud infrastructure engineer. Generate Terraform/Pulumi/CloudFormation code for:
- Scalable architecture
- High availability
- Cost optimization
- Security groups and IAM
- Auto-scaling policies"""
        return await self._call_llm(system, prompt)

    async def _general_ops(self, prompt: str) -> str:
        """General ops advice."""
        system = "You are a senior DevOps engineer. Provide expert advice on infrastructure, CI/CD, and operations."
        return await self._call_llm(system, prompt)
