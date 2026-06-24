"""
OpenClaw Elite — Intent Router
Intelligent classification, confidence scoring, agent selection.
"""
import os
import json
import re
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from worker.ai_worker import call_groq_sync
from shared.config import Config

logger = logging.getLogger("intent_router")

AGENT_DEFINITIONS = {
    "bob": {
        "name": "Bob",
        "role": "Conversation & Customer Support Agent",
        "responsibilities": [
            "conversation", "customer_support", "user_interaction", 
            "explanations", "greeting", "small_talk", "faq", 
            "user_onboarding", "general_help"
        ],
        "keywords": [
            "hello", "hi", "help", "how do i", "what is", "explain", 
            "question", "support", "thanks", "thank you", "bye", "goodbye",
            "welcome", "tutorial", "guide", "how does", "clarify", "meaning",
            "customer", "user", "talk", "chat", "conversation", "friendly",
            "onboard", "getting started", "beginner", "new user"
        ],
        "description": "Handles all conversational interactions, user support, explanations, and friendly engagement."
    },
    "carla": {
        "name": "Carla",
        "role": "Research & Intelligence Agent",
        "responsibilities": [
            "research", "fact_gathering", "web_intelligence", 
            "competitive_analysis", "market_research", "data_collection",
            "information_synthesis", "trend_analysis", "benchmarking"
        ],
        "keywords": [
            "research", "find", "search", "look up", "investigate", "analyze",
            "competitor", "market", "industry", "trend", "data", "statistics",
            "report", "survey", "study", "paper", "article", "news", "web",
            "internet", "google", "compare", "benchmark", "intelligence",
            "gather", "collect", "synthesize", "summarize", "review literature"
        ],
        "description": "Conducts deep research, gathers facts, performs competitive analysis, and synthesizes intelligence."
    },
    "dave": {
        "name": "Dave",
        "role": "Coding & Infrastructure Agent",
        "responsibilities": [
            "coding", "debugging", "github", "infrastructure", 
            "deployments", "devops", "ci_cd", "docker", "terraform",
            "cloud", "aws", "render", "vercel", "netlify", "serverless"
        ],
        "keywords": [
            "code", "write", "function", "class", "script", "program",
            "debug", "fix", "bug", "error", "issue", "broken", "crash",
            "deploy", "deployment", "release", "publish", "push", "merge",
            "github", "git", "repo", "repository", "pull request", "pr",
            "infrastructure", "docker", "kubernetes", "k8s", "terraform",
            "cloud", "aws", "gcp", "azure", "server", "hosting", "ci/cd",
            "pipeline", "build", "test suite", "lint", "format", "refactor"
        ],
        "description": "Writes code, fixes bugs, manages GitHub operations, handles infrastructure and deployments."
    },
    "alice": {
        "name": "Alice",
        "role": "Planning & Project Management Agent",
        "responsibilities": [
            "planning", "scheduling", "project_management", 
            "task_breakdown", "roadmap", "timeline", "milestone",
            "coordination", "workflow", "prioritization", "organization"
        ],
        "keywords": [
            "plan", "schedule", "timeline", "roadmap", "milestone", "deadline",
            "project", "manage", "organize", "coordinate", "workflow", "process",
            "break down", "steps", "phases", "sprint", "kanban", "agile", "scrum",
            "prioritize", "order", "sequence", "calendar", "reminder", "due",
            "assign", "delegate", "track", "monitor progress", "status update",
            "gantt", "planning session", "strategy", "objective", "goal setting"
        ],
        "description": "Creates plans, breaks down tasks, manages schedules, and coordinates complex projects."
    }
}

RISKY_ACTIONS = {
    "production_deployment": ["deploy to prod", "production deploy", "live deployment", "push to main"],
    "data_deletion": ["delete", "remove data", "drop table", "clear database", "purge"],
    "credential_changes": ["change token", "rotate key", "update secret", "modify credentials"],
    "external_messaging": ["send email", "post to twitter", "publish to linkedin", "send sms", "notify external"],
    "financial": ["payment", "billing", "invoice", "charge", "refund", "subscription"],
    "destructive_git": ["force push", "delete branch", "reset --hard", "rebase -i", "amend history"]
}

SAFE_ACTIONS = {
    "research", "reading_files", "planning", "analysis", "query", "search",
    "summarize", "explain", "suggest", "recommend", "draft", "preview",
    "status_check", "monitoring", "reporting", "log_review"
}


@dataclass
class IntentResult:
    intent: str
    confidence: float
    agent: str
    requires_clarification: bool
    reasoning: str
    sub_intents: list
    risk_level: str
    requires_approval: bool
    execution_plan: Optional[list] = None


class IntentRouter:
    """Intelligent router that classifies user intent, scores confidence, selects agent."""

    CONFIDENCE_THRESHOLD = 0.80
    HIGH_CONFIDENCE = 0.90

    def __init__(self):
        self.agent_defs = AGENT_DEFINITIONS
        self.risky_patterns = RISKY_ACTIONS
        self.safe_actions = SAFE_ACTIONS
        self.classification_history = []

    def classify(self, message: str, user_context: dict = None) -> IntentResult:
        """Main classification entry point."""
        message_lower = message.lower().strip()
        user_context = user_context or {}

        scores = self._keyword_score(message_lower)
        pattern_scores = self._pattern_detect(message_lower)
        for agent, score in pattern_scores.items():
            scores[agent] = scores.get(agent, 0) + score

        risk_level, requires_approval = self._assess_risk(message_lower)
        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]

        total_score = sum(scores.values()) or 1
        confidence = min(best_score / total_score * 1.5, 0.99)

        intent = self._build_intent(message_lower, best_agent)
        requires_clarification = confidence < self.CONFIDENCE_THRESHOLD
        reasoning = self._generate_reasoning(message, best_agent, confidence, scores)
        sub_intents = self._detect_sub_intents(message_lower, scores)

        execution_plan = None
        if len(sub_intents) > 1:
            execution_plan = self._build_execution_plan(message, sub_intents)

        result = IntentResult(
            intent=intent,
            confidence=round(confidence, 3),
            agent=best_agent,
            requires_clarification=requires_clarification,
            reasoning=reasoning,
            sub_intents=sub_intents,
            risk_level=risk_level,
            requires_approval=requires_approval,
            execution_plan=execution_plan
        )

        self._log_classification(result)
        return result

    def _keyword_score(self, message: str) -> Dict[str, float]:
        scores = {agent: 0.0 for agent in self.agent_defs}
        for agent_id, agent_def in self.agent_defs.items():
            for keyword in agent_def["keywords"]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', message):
                    scores[agent_id] += 1.0
                elif keyword in message:
                    scores[agent_id] += 0.3
        return scores

    def _pattern_detect(self, message: str) -> Dict[str, float]:
        scores = {}
        code_patterns = [
            r'\b(def |class |import |from |function|const |let |var )\b',
            r'\b(bug|error|exception|traceback|fix|debug)\b',
            r'\b(git |github|repo|branch|commit|merge|pull request)\b',
            r'\b(docker|kubernetes|terraform|deploy|infrastructure)\b',
            r'[{};]|\bprint\(|console\.log|def\s+\w+\(',
        ]
        code_score = sum(1.5 for p in code_patterns if re.search(p, message))
        if code_score > 0:
            scores["dave"] = code_score

        plan_patterns = [
            r'\b(plan|roadmap|timeline|schedule|milestone|sprint)\b',
            r'\b(step \d+|phase \d+|first.*then|after that|finally)\b',
            r'\b(break down|decompose|organize|coordinate|manage)\b',
        ]
        plan_score = sum(1.2 for p in plan_patterns if re.search(p, message))
        if plan_score > 0:
            scores["alice"] = plan_score

        research_patterns = [
            r'\b(research|find out|look into|investigate|study|analyze)\b',
            r'\b(competitor|market share|industry|trend|benchmark)\b',
            r'\b(data|statistics|survey|report|white paper)\b',
        ]
        research_score = sum(1.0 for p in research_patterns if re.search(p, message))
        if research_score > 0:
            scores["carla"] = research_score

        return scores

    def _assess_risk(self, message: str) -> tuple:
        for risk_category, patterns in self.risky_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    return "dangerous", True
        caution_indicators = ["deploy", "push", "merge", "delete", "update", "modify", "change"]
        for indicator in caution_indicators:
            if indicator in message:
                return "caution", False
        return "safe", False

    def _build_intent(self, message: str, agent: str) -> str:
        agent_def = self.agent_defs[agent]
        actions = {
            "create": ["create", "write", "make", "build", "generate"],
            "modify": ["update", "change", "edit", "modify", "fix", "refactor"],
            "delete": ["delete", "remove", "drop", "clear", "purge"],
            "query": ["what", "how", "why", "when", "where", "find", "search"],
            "execute": ["run", "execute", "deploy", "start", "launch", "stop"],
            "plan": ["plan", "organize", "schedule", "coordinate", "manage"],
        }
        primary_action = "process"
        for action, keywords in actions.items():
            if any(kw in message for kw in keywords):
                primary_action = action
                break
        return f"{primary_action}_{agent}_request"

    def _generate_reasoning(self, message: str, agent: str, confidence: float, scores: dict) -> str:
        agent_def = self.agent_defs[agent]
        runner_up = sorted(scores.items(), key=lambda x: x[1], reverse=True)[1] if len(scores) > 1 else (None, 0)
        reasoning = f"Selected '{agent_def['name']}' ({agent_def['role']}) with {confidence:.0%} confidence. Primary indicators: keyword matches in '{agent}' category. "
        if runner_up[0] and runner_up[1] > 0:
            reasoning += f"Runner-up: {self.agent_defs[runner_up[0]]['name']} (score: {runner_up[1]:.1f}). "
        if confidence >= self.HIGH_CONFIDENCE:
            reasoning += "High confidence — direct execution authorized."
        elif confidence >= self.CONFIDENCE_THRESHOLD:
            reasoning += "Moderate confidence — proceed with standard verification."
        else:
            reasoning += "Low confidence — clarification recommended before execution."
        return reasoning

    def _detect_sub_intents(self, message: str, scores: dict) -> list:
        sub_intents = []
        secondary_threshold = max(scores.values()) * 0.4 if scores.values() else 0
        for agent, score in scores.items():
            if score >= secondary_threshold and score > 0:
                sub_intents.append({
                    "agent": agent,
                    "confidence_contribution": score,
                    "role": self.agent_defs[agent]["role"]
                })
        sub_intents.sort(key=lambda x: x["confidence_contribution"], reverse=True)
        return sub_intents

    def _build_execution_plan(self, message: str, sub_intents: list) -> list:
        plan = []
        alice_idx = next((i for i, si in enumerate(sub_intents) if si["agent"] == "alice"), None)
        if alice_idx is not None:
            plan.append({"step": 1, "agent": "alice", "action": "analyze_and_plan", "description": "Break down the request into actionable steps", "depends_on": []})
        carla_idx = next((i for i, si in enumerate(sub_intents) if si["agent"] == "carla"), None)
        if carla_idx is not None:
            plan.append({"step": len(plan) + 1, "agent": "carla", "action": "research_and_gather", "description": "Gather facts, data, and intelligence needed for execution", "depends_on": [1] if alice_idx is not None else []})
        dave_idx = next((i for i, si in enumerate(sub_intents) if si["agent"] == "dave"), None)
        if dave_idx is not None:
            plan.append({"step": len(plan) + 1, "agent": "dave", "action": "execute_and_build", "description": "Implement technical solution based on research and plan", "depends_on": list(range(1, len(plan) + 1))})
        plan.append({"step": len(plan) + 1, "agent": "bob", "action": "summarize_and_respond", "description": "Synthesize results and communicate back to user", "depends_on": list(range(1, len(plan) + 1))})
        return plan

    def _log_classification(self, result: IntentResult):
        self.classification_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "intent": result.intent,
            "confidence": result.confidence,
            "agent": result.agent,
            "risk_level": result.risk_level,
            "requires_approval": result.requires_approval
        })
        self.classification_history = self.classification_history[-1000:]

    def get_clarifying_question(self, message: str, result: IntentResult) -> str:
        agent = result.agent
        agent_def = self.agent_defs[agent]
        ambiguous_aspects = []
        action_words = ["create", "update", "delete", "find", "deploy", "fix", "explain"]
        has_clear_action = any(w in message.lower() for w in action_words)
        if not has_clear_action:
            ambiguous_aspects.append("action")
        scope_indicators = ["for", "in", "about", "regarding", "related to"]
        has_scope = any(w in message.lower() for w in scope_indicators)
        if not has_scope and len(message.split()) < 5:
            ambiguous_aspects.append("scope")
        if agent == "dave" and "format" not in message.lower():
            ambiguous_aspects.append("format")
        if "action" in ambiguous_aspects:
            return f"I understand you're working on something related to {agent_def['role'].lower()}, but I'm not sure what you'd like me to do. Would you like me to create something new, fix an existing issue, research information, or plan a project?"
        if "scope" in ambiguous_aspects:
            return f"I can help with that! To give you the best assistance, could you clarify the scope — are you asking about a specific project, file, or system component?"
        if "format" in ambiguous_aspects:
            return f"Got it. What format would you like the output in — code, documentation, a summary, or a detailed report?"
        return f"I want to make sure I route this correctly. Are you looking for {agent_def['role'].lower()}, or is this more about one of these: " + ", ".join([f"{self.agent_defs[a]['role'].lower()}" for a in self.agent_defs if a != agent][:2]) + "?"

    def to_dict(self, result: IntentResult) -> dict:
        return {
            "intent": result.intent,
            "confidence": result.confidence,
            "agent": result.agent,
            "requires_clarification": result.requires_clarification,
            "reasoning": result.reasoning,
            "sub_intents": result.sub_intents,
            "risk_level": result.risk_level,
            "requires_approval": result.requires_approval,
            "execution_plan": result.execution_plan
        }


_router_instance = None

def get_router() -> IntentRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance


def classify_intent(message: str, user_context: dict = None) -> dict:
    router = get_router()
    result = router.classify(message, user_context)
    return router.to_dict(result)
