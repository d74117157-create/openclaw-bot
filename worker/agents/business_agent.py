"""
OpenClaw Business Agent — executes the core mission:
research opportunities, score them, generate leads, plan content.
"""
import logging
from worker.ai_worker import _chat
from shared.mission import (
    AGENT_SYSTEM_PROMPT, OPPORTUNITY_TEMPLATE, TASK_REPORT_TEMPLATE,
    CONTENT_PRIORITIES, LEAD_SIGNALS, score_opportunity, get_decision, MISSION
)
from memory import save_decision

logger = logging.getLogger(__name__)


def run(task: str) -> str:
    """Main entry point — routes task to appropriate business function."""
    task_lower = task.lower()

    if any(w in task_lower for w in ["opportunity", "niche", "business idea", "find"]):
        return research_opportunity(task)
    elif any(w in task_lower for w in ["lead", "prospect", "outreach"]):
        return generate_leads(task)
    elif any(w in task_lower for w in ["content", "post", "video", "script"]):
        return create_content(task)
    elif any(w in task_lower for w in ["report", "status", "performance", "weekly"]):
        return generate_report(task)
    elif any(w in task_lower for w in ["score", "evaluate", "analyze"]):
        return evaluate_opportunity(task)
    else:
        return general_strategy(task)


def research_opportunity(task: str) -> str:
    tier1 = "\n".join(f"- {x}" for x in MISSION["opportunity_tiers"][1])
    prompt = f"""You are OpenClaw business researcher.

Task: {task}

Analyze this as a business opportunity. Return a structured report covering:
- Business model (how it makes money)
- Startup cost (realistic $$ amount)
- Difficulty rating (1-10)
- Time to first revenue
- Monthly revenue potential
- Top 3 risks
- 5-step launch plan
- Scaling strategy

Focus on Tier 1 opportunities if relevant:
{tier1}

Be specific, realistic, and actionable. End with a score out of 100."""

    result = _chat(AGENT_SYSTEM_PROMPT, prompt)

    # Save as decision
    save_decision(
        context=f"Opportunity research: {task}",
        decision=result[:500],
        platform="openclaw",
        status="researched"
    )

    return result


def generate_leads(task: str) -> str:
    signals = "\n".join(f"- {s}" for s in LEAD_SIGNALS)
    prompt = f"""You are OpenClaw lead generation agent.

Task: {task}

Generate a practical lead generation plan. Include:
1. Target business type and location criteria
2. Where to find these leads (tools, directories, search strings)
3. What signals to look for:
{signals}
4. Personalized outreach template (email/DM)
5. Follow-up sequence (3 messages)
6. Expected conversion rate and revenue potential

Be specific — include actual search queries, tools, and scripts."""

    return _chat(AGENT_SYSTEM_PROMPT, prompt)


def create_content(task: str) -> str:
    priorities = "\n".join(f"- {p}" for p in CONTENT_PRIORITIES)
    prompt = f"""You are OpenClaw content strategist.

Task: {task}

Create a content plan. Include:
1. Hook (first 3 seconds for video / headline for text)
2. Core message
3. Call to action
4. Platform-specific versions: YouTube Short, TikTok, Instagram Reel, Blog post
5. SEO keywords if applicable
6. Posting schedule recommendation

Content priorities:
{priorities}

Make content viral-worthy, educational, and business-focused."""

    return _chat(AGENT_SYSTEM_PROMPT, prompt)


def generate_report(task: str) -> str:
    targets = MISSION["weekly_targets"]
    prompt = f"""You are OpenClaw reporting agent.

Task: {task}

Generate a weekly performance report using this template:

1. Objective: [what was the goal this week]
2. Actions Taken: [what was actually done]
3. Results: [metrics and outcomes]
4. Revenue Generated: [$ amount or pipeline value]
5. Problems Found: [blockers and issues]
6. Recommended Next Steps: [top 3 priorities for next week]

Weekly targets to measure against:
- Qualified leads: {targets['qualified_leads']}
- Short-form content: {targets['short_form_content']}
- Long-form content: {targets['long_form_content']}
- New digital assets: {targets['new_digital_assets']}
- New opportunities identified: {targets['new_revenue_opportunities']}

Be honest about gaps. Recommend specific fixes."""

    return _chat(AGENT_SYSTEM_PROMPT, prompt)


def evaluate_opportunity(task: str) -> str:
    prompt = f"""You are OpenClaw opportunity evaluator.

Task: {task}

Score this opportunity 0-100 using these criteria:
- ROI potential (30 pts)
- Difficulty/ease of execution (20 pts)  
- Time to first revenue (25 pts)
- Monthly revenue ceiling (15 pts)
- Market demand signals (10 pts)

Return:
- Score: X/100
- Decision: IMMEDIATE ACTION / VALIDATE FIRST / ARCHIVE
- Top 3 reasons for this score
- If score >= 60: exact next 3 steps to take today"""

    result = _chat(AGENT_SYSTEM_PROMPT, prompt)
    save_decision(
        context=f"Opportunity evaluation: {task}",
        decision=result[:500],
        platform="openclaw",
        status="evaluated"
    )
    return result


def general_strategy(task: str) -> str:
    prompt = f"""You are OpenClaw, autonomous digital business operator.

Owner's request: {task}

Mission: Build legitimate online businesses reaching $10,000+/month.

Respond with:
1. Your analysis of this request
2. Recommended approach (Tier 1 opportunities first)
3. Specific action plan with numbered steps
4. Resources or tools needed (free first)
5. Timeline estimate

Always be specific, actionable, and realistic."""

    return _chat(AGENT_SYSTEM_PROMPT, prompt)
