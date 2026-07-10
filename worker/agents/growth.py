"""
OpenClaw — worker/agents/growth.py
GROWTH AGENT: Automation funnels, Discord/Slack engagement, ROI-driven workflows.
"""
from worker.ai_worker import process_task, _chat

SYSTEM = (
    "You are the GROWTH AGENT of OpenClaw. You design automation funnels, engagement systems, "
    "Discord/Slack community workflows, and ROI-driven automations. "
    "Rules: prioritize measurable ROI, automate repetitive work, design for scale. "
    "Always return:\n"
    "GROWTH STRATEGY: <high-level approach>\n"
    "AUTOMATION FLOWS: <step-by-step automation sequences>\n"
    "DISCORD IMPLEMENTATION: <specific Discord features/bots to use>\n"
    "SLACK IMPLEMENTATION: <specific Slack features/workflows>\n"
    "KPIs TO TRACK: <measurable success metrics>\n"
    "IMPLEMENTATION CHECKLIST: <ordered action items>"
)


def community_growth_plan(community_type: str, goal: str) -> str:
    return _chat(SYSTEM, f"Design a growth plan for a {community_type} community. Goal: {goal}")


def onboarding_flow(platform: str, user_type: str) -> str:
    return _chat(SYSTEM, f"Design a {platform} onboarding automation flow for: {user_type}")


def engagement_system(platform: str, metrics: str) -> str:
    return _chat(SYSTEM, f"Build an engagement system for {platform}. Track: {metrics}")


def retention_strategy(pain_points: str) -> str:
    return _chat(SYSTEM, f"Design a user retention strategy for these pain points: {pain_points}")


def discord_server_architecture(purpose: str) -> str:
    return _chat(
        SYSTEM,
        f"Design a complete Discord server architecture for: {purpose}\n"
        f"Include: channels, roles, bots, automations, welcome flow, moderation."
    )


def slack_workspace_automation(team_size: str, workflow: str) -> str:
    return _chat(
        SYSTEM,
        f"Design Slack workspace automations for a {team_size} team. Workflow: {workflow}"
    )


def run(task: str) -> str:
    return process_task(task, "growth")
