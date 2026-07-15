"""QA Agent — Reviews and validates other agents' work"""
from app.agents.base import BaseAgent
from typing import Dict, Any

class QAAgent(BaseAgent):
    def __init__(self, brain=None):
        super().__init__("QA", "qa", brain)

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = f"As the QA engineer, review and validate: {task}"
        result = self._think(prompt, context, max_tokens=2000)
        return result

    async def review(self, agent_result: Dict[str, Any], original_task: str) -> Dict[str, Any]:
        """Review another agent's work."""
        response = agent_result.get("response", "")
        confidence = agent_result.get("confidence", 0)
        warnings = agent_result.get("warnings", [])

        review_prompt = f"""Review this agent output for quality and accuracy:

Original Task: {original_task}
Agent Response: {response[:1000]}
Confidence Score: {confidence}
Warnings: {warnings}

Provide:
1. Quality assessment (1-10)
2. Issues found
3. Recommendations
4. Whether this should be approved or sent back"""

        review = self._think(review_prompt, max_tokens=1500)

        return {
            "review": review,
            "original_result": agent_result,
            "approved": confidence >= 0.6 and len(warnings) < 3
        }
