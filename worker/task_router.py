"""
OpenClaw — worker/task_router.py
Smart task router. Decides which agents to spawn, browser execution, priority.
"""
import re
from worker.ai_worker import _chat

BROWSER_TRIGGERS = [
    "shopify", "store", "website", "web app", "sign up", "sign in",
    "login", "register", "navigate", "browse", "click", "fill form",
    "submit", "checkout", "order", "buy", "purchase", "stripe",
    "vercel", "netlify", "heroku", "deploy to", "upload", "download",
    "scrape", "crawl", "search google", "search web", "open browser",
    "go to", "visit", "open site", "open url", "http", "www.",
    "dashboard", "admin panel", "portal", "app.railway", "github.com",
]

AGENT_TRIGGERS = {
    "coder":    ["build", "write", "code", "create", "implement", "script",
                 "function", "class", "api", "bot", "app", "fix", "refactor"],
    "reviewer": ["review", "audit", "check", "validate", "analyse", "analyze",
                 "inspect", "quality", "security"],
    "qa":       ["test", "testing", "qa", "quality", "verify", "validate",
                 "assert", "spec", "coverage"],
    "ops":      ["deploy", "deployment", "railway", "docker", "container",
                 "scale", "monitor", "uptime", "rollback", "infra", "server"],
    "research": ["research", "find", "discover", "compare", "analyse", "look up",
                 "what is", "how to", "best way", "options", "alternatives"],
    "growth":   ["grow", "funnel", "onboard", "engage", "retention", "community",
                 "discord server", "slack workspace", "automation flow", "roi"],
    "github":   ["github", "repo", "repository", "pr", "pull request", "branch",
                 "commit", "issue", "workflow", "actions", "ci", "cd", "merge"],
    "memory":   ["remember", "log", "track", "history", "past", "previous",
                 "decisions", "what did", "record"],
}

ROUTER_SYSTEM = (
    "You are a task router for an AI swarm. Given a task, output JSON:\n"
    "{\n"
    '  "needs_browser": true,\n'
    '  "agents": ["agent1"],\n'
    '  "priority": "high",\n'
    '  "browser_task": "sub-task",\n'
    '  "github_issue": true,\n'
    '  "slack_alert": true,\n'
    '  "estimated_steps": 3\n'
    "}\n"
    "Agents: orchestrator, coder, reviewer, qa, ops, research, growth, memory, github, browser.\n"
    "Return ONLY valid JSON."
)


class TaskRouter:

    def route(self, task: str) -> dict:
        try:
            raw   = _chat(ROUTER_SYSTEM, f"Task: {task}", max_tokens=400)
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start != -1 and end > start:
                import json
                decision = json.loads(raw[start:end])
                if "agents" in decision and "needs_browser" in decision:
                    return decision
        except Exception:
            pass
        return self._keyword_route(task)

    def _keyword_route(self, task: str) -> dict:
        task_lower = task.lower()
        needs_browser = any(kw in task_lower for kw in BROWSER_TRIGGERS)
        agents = ["orchestrator"]
        for agent, keywords in AGENT_TRIGGERS.items():
            if any(kw in task_lower for kw in keywords):
                if agent not in agents:
                    agents.append(agent)
        if "memory" not in agents:
            agents.append("memory")
        if "coder" in agents and "qa" not in agents:
            agents.append("qa")
        if "coder" in agents and "reviewer" not in agents:
            agents.append("reviewer")
        if needs_browser and "browser" not in agents:
            agents.append("browser")
        if any(kw in task_lower for kw in AGENT_TRIGGERS["github"]) and "github" not in agents:
            agents.append("github")
        priority = "high" if needs_browser else "medium"
        if any(kw in task_lower for kw in ["urgent", "asap", "critical", "emergency", "now"]):
            priority = "high"
        return {
            "needs_browser":   needs_browser,
            "agents":          agents,
            "priority":        priority,
            "browser_task":    task if needs_browser else "",
            "github_issue":    True,
            "slack_alert":     True,
            "estimated_steps": len(agents) * 2,
        }

    def describe(self, route: dict) -> str:
        parts = [f"**Priority:** {route.get('priority','medium').upper()}"]
        if route.get("needs_browser"):
            parts.append("**Browser execution:** Yes")
        parts.append(f"**Agents:** {', '.join(route.get('agents', []))}")
        parts.append(f"**Estimated steps:** {route.get('estimated_steps', '?')}")
        if route.get("github_issue"):
            parts.append("**GitHub issue:** Will be created")
        if route.get("slack_alert"):
            parts.append("**Slack:** Full log posted")
        return "\n".join(parts)
