"""
OpenClaw — worker/agents/ops.py
OPS AGENT: Railway deployments, Docker, scaling, rollbacks, monitoring.
"""
from worker.ai_worker import process_task, _chat

SYSTEM = (
    "You are the OPS AGENT of OpenClaw. You manage Railway deployments, Docker images, "
    "scaling strategies, rollback procedures, and uptime monitoring. "
    "Rules: prioritize uptime, validate before every release, maintain rollback capability. "
    "Always return:\n"
    "DEPLOYMENT PLAN: <step-by-step>\n"
    "ENV VARS REQUIRED: <list — never reveal values>\n"
    "HEALTH CHECKS: <commands to verify system is live>\n"
    "ROLLBACK PROCEDURE: <exact commands>\n"
    "MONITORING: <what to watch>"
)


def deploy_plan(service: str, env: str = "production") -> str:
    return _chat(SYSTEM, f"Create full Railway deployment plan for: {service} (env: {env})")


def rollback_plan(service: str, version: str = "previous") -> str:
    return _chat(SYSTEM, f"Write rollback procedure for: {service} to version: {version}")


def scale_plan(service: str, direction: str = "up", reason: str = "") -> str:
    return _chat(SYSTEM, f"Design scaling plan for {service} ({direction}). Reason: {reason}")


def monitoring_plan(service: str) -> str:
    return _chat(
        SYSTEM,
        f"Design a monitoring plan for {service}: health checks, alerts, "
        f"Slack notifications, Railway metrics, error rate thresholds."
    )


def docker_plan(service: str) -> str:
    return _chat(SYSTEM, f"Create a production Dockerfile and docker-compose.yml for: {service}")


def incident_response(incident: str) -> str:
    return _chat(
        SYSTEM,
        f"Write an incident response runbook for: {incident}\n"
        f"Include: detection, containment, resolution, post-mortem template."
    )


def run(task: str) -> str:
    return process_task(task, "ops")
