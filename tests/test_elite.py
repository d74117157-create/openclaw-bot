"""
OpenClaw Elite — Comprehensive Test Suite
Tests: Intent Router, Agents, Memory, Verification, Monitoring, Approval
"""
import os
import sys
import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from worker.intent_router import IntentRouter, classify_intent
from worker.verification import SelfVerifier, VerificationResult
from worker.approval import ApprovalFramework, RiskLevel
from memory.elite_memory import EliteMemory, init_elite_memory


class TestIntentRouter(unittest.TestCase):
    """Test the intelligent intent routing system."""

    def setUp(self):
        self.router = IntentRouter()

    def test_conversation_routing(self):
        """Bob should handle conversational messages."""
        result = self.router.classify("Hello, how are you today?")
        self.assertEqual(result.agent, "bob")
        self.assertGreaterEqual(result.confidence, 0.80)
        self.assertFalse(result.requires_clarification)

    def test_research_routing(self):
        """Carla should handle research requests."""
        result = self.router.classify("Research the latest trends in AI agents")
        self.assertEqual(result.agent, "carla")
        self.assertGreaterEqual(result.confidence, 0.80)

    def test_coding_routing(self):
        """Dave should handle coding requests."""
        result = self.router.classify("Write a Python function to parse JSON")
        self.assertEqual(result.agent, "dave")
        self.assertGreaterEqual(result.confidence, 0.80)

    def test_planning_routing(self):
        """Alice should handle planning requests."""
        result = self.router.classify("Create a project plan for building a mobile app")
        self.assertEqual(result.agent, "alice")
        self.assertGreaterEqual(result.confidence, 0.80)

    def test_low_confidence_clarification(self):
        """Low confidence should trigger clarification."""
        result = self.router.classify("xyz abc 123")
        self.assertLess(result.confidence, 0.80)
        self.assertTrue(result.requires_clarification)

    def test_risk_assessment_safe(self):
        """Safe actions should not require approval."""
        result = self.router.classify("What is the weather today?")
        self.assertEqual(result.risk_level, "safe")
        self.assertFalse(result.requires_approval)

    def test_risk_assessment_dangerous(self):
        """Dangerous actions should require approval."""
        result = self.router.classify("Deploy to production and delete the database")
        self.assertEqual(result.risk_level, "dangerous")
        self.assertTrue(result.requires_approval)

    def test_multi_agent_detection(self):
        """Complex tasks should trigger multi-agent plans."""
        result = self.router.classify("Plan and build a new feature for the app")
        self.assertIsNotNone(result.execution_plan)
        self.assertGreaterEqual(len(result.sub_intents), 2)

    def test_clarifying_question(self):
        """Should generate exactly one clarifying question."""
        result = self.router.classify("help")
        question = self.router.get_clarifying_question("help", result)
        self.assertIsInstance(question, str)
        self.assertGreater(len(question), 10)

    def test_output_format(self):
        """Router must return correct structured output."""
        result = self.router.classify("Write a Python script")
        d = self.router.to_dict(result)
        self.assertIn("intent", d)
        self.assertIn("confidence", d)
        self.assertIn("agent", d)
        self.assertIn("requires_clarification", d)
        self.assertIn("reasoning", d)
        self.assertIsInstance(d["confidence"], float)
        self.assertIsInstance(d["requires_clarification"], bool)


class TestSelfVerification(unittest.TestCase):
    """Test the self-verification system."""

    def setUp(self):
        self.verifier = SelfVerifier()

    def test_successful_verification(self):
        """Successful task should pass verification."""
        agent_results = [{
            "agent": "dave",
            "response": "Here is the code:\n```python\ndef hello():\n    return 'world'\n```\nThis function returns 'world'.",
            "type": "code_generation"
        }]
        result = self.verifier.verify("Write a hello function", agent_results)
        self.assertTrue(result.task_completed)
        self.assertTrue(result.tools_succeeded)
        self.assertTrue(result.errors_handled)
        self.assertFalse(result.needs_user_input)
        self.assertTrue(result.can_respond)
        self.assertGreaterEqual(result.quality_score, 0.6)

    def test_failed_verification(self):
        """Failed task should not pass verification."""
        agent_results = [{
            "agent": "dave",
            "response": "Error: unable to complete the task due to missing information",
            "type": "code_generation",
            "error": "Missing parameter"
        }]
        result = self.verifier.verify("Write a complex function", agent_results)
        self.assertFalse(result.task_completed)
        self.assertFalse(result.can_respond)
        self.assertGreater(len(result.issues), 0)

    def test_needs_user_input(self):
        """Should detect when user input is needed."""
        agent_results = [{
            "agent": "carla",
            "response": "Could you specify which competitors you want me to research?",
            "type": "research"
        }]
        result = self.verifier.verify("Research competitors", agent_results)
        self.assertTrue(result.needs_user_input)
        self.assertFalse(result.can_respond)

    def test_quality_score(self):
        """Quality score should be within valid range."""
        agent_results = [{"agent": "bob", "response": "Hello!"}]
        result = self.verifier.verify("Say hello", agent_results)
        self.assertGreaterEqual(result.quality_score, 0.0)
        self.assertLessEqual(result.quality_score, 1.0)


class TestApprovalFramework(unittest.TestCase):
    """Test the approval framework."""

    def setUp(self):
        self.framework = ApprovalFramework()

    def test_safe_action_auto_approved(self):
        """Safe actions should not require approval."""
        result = self.framework.assess_action("research")
        self.assertFalse(result["requires_approval"])
        self.assertEqual(result["risk_level"], RiskLevel.SAFE.value)

    def test_dangerous_action_requires_approval(self):
        """Dangerous actions should require approval."""
        result = self.framework.assess_action("deploy_production")
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["risk_level"], RiskLevel.DANGEROUS.value)

    def test_approval_workflow(self):
        """Test full approval/denial workflow."""
        req = self.framework.request_approval("deploy_production", {"env": "prod"}, "test_user")
        self.assertEqual(req.status, "pending")
        self.assertIn(req.id, self.framework.pending_requests)

        # Approve
        result = self.framework.approve(req.id, "admin")
        self.assertTrue(result["success"])
        self.assertNotIn(req.id, self.framework.pending_requests)
        self.assertIn(req.id, self.framework.approved_requests)

    def test_deny_workflow(self):
        """Test denial workflow."""
        req = self.framework.request_approval("delete_data", {"table": "users"}, "test_user")
        result = self.framework.deny(req.id, "Too risky")
        self.assertTrue(result["success"])
        self.assertIn(req.id, self.framework.denied_requests)

    def test_heuristic_assessment(self):
        """Heuristic should detect risky keywords."""
        result = self.framework.assess_action("unknown_action", {"target": "production database"})
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["risk_level"], RiskLevel.DANGEROUS.value)


class TestEliteMemory(unittest.TestCase):
    """Test the elite memory system."""

    def setUp(self):
        import tempfile
        import memory.elite_memory as em
        # Clear singleton and use fresh DB
        em._memory_instance = None
        self.db_path = tempfile.mktemp(suffix=".db")
        os.environ["MEMORY_DB"] = self.db_path
        # Re-init tables
        em.init_elite_memory()
        self.memory = em.EliteMemory()

    def tearDown(self):
        import memory.elite_memory as em
        em._memory_instance = None
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_project_storage(self):
        """Should store and retrieve projects."""
        self.memory.store_project("TestProject", "A test project", {"key": "value"})
        project = self.memory.get_project("TestProject")
        self.assertIsNotNone(project)
        self.assertEqual(project["name"], "TestProject")
        self.assertEqual(project["description"], "A test project")

    def test_user_profile(self):
        """Should store and retrieve user profiles."""
        self.memory.store_user_profile("user123", "discord", "TestUser", 
                                       preferences={"style": "formal"})
        profile = self.memory.get_user_profile("user123")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["username"], "TestUser")
        self.assertEqual(profile["preferences"]["style"], "formal")

    def test_conversation_storage(self):
        """Should store and retrieve conversations."""
        self.memory.store_conversation("thread_convo_test", "user123", "discord",
                                       "Hello", "Hi there!", "greeting", "bob", 0.95)
        convs = self.memory.get_conversation_thread("thread_convo_test")
        self.assertGreaterEqual(len(convs), 1)
        self.assertEqual(convs[0]["message"], "Hello")

    def test_task_management(self):
        """Should manage open tasks."""
        self.memory.store_task("task_1", "Do something important", "dave", "high")
        tasks = self.memory.get_open_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task_id"], "task_1")

        self.memory.update_task("task_1", status="completed", result="Done!")
        tasks = self.memory.get_open_tasks()
        self.assertEqual(len(tasks), 0)

    def test_goal_tracking(self):
        """Should track user goals."""
        self.memory.store_goal("user123", "Build AI system", "Create an AI agent", "2026-12-31")
        goals = self.memory.get_user_goals("user123")
        self.assertGreaterEqual(len(goals), 1)
        self.assertEqual(goals[0]["title"], "Build AI system")

    def test_resume_context(self):
        """Should generate resume context for returning users."""
        self.memory.store_user_profile("user123", "discord", "TestUser")
        self.memory.store_conversation("thread_convo_test", "user123", "discord",
                                       "Previous message", "Previous response", "test", "bob", 0.9)
        context = self.memory.get_resume_context("user123")
        self.assertTrue(context["has_previous_session"])


class TestIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""

    def test_full_pipeline_simulation(self):
        """Simulate the full message processing pipeline."""
        # 1. Intent classification
        routing = classify_intent("Write a Python function to calculate fibonacci")
        self.assertEqual(routing["agent"], "dave")
        self.assertGreaterEqual(routing["confidence"], 0.80)
        self.assertFalse(routing["requires_clarification"])

        # 2. Risk assessment
        self.assertIn(routing["risk_level"], ["safe", "caution", "dangerous"])

        # 3. Verification would happen after execution
        # (We can't test actual agent execution without API keys)

        # 4. Check output format
        self.assertIn("intent", routing)
        self.assertIn("confidence", routing)
        self.assertIn("agent", routing)
        self.assertIn("requires_clarification", routing)
        self.assertIn("reasoning", routing)
        self.assertIn("risk_level", routing)
        self.assertIn("requires_approval", routing)


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestIntentRouter))
    suite.addTests(loader.loadTestsFromTestCase(TestSelfVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestEliteMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return {
        "total": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful()
    }


if __name__ == "__main__":
    results = run_tests()
    print(f"\n{'='*60}")
    print(f"TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total:   {results['total']}")
    print(f"Passed:  {results['passed']}")
    print(f"Failed:  {results['failed']}")
    print(f"Errors:  {results['errors']}")
    print(f"Success: {results['success']}")

    sys.exit(0 if results['success'] else 1)
