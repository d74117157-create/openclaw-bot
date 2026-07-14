from agents.base_agent import BaseAgent
from typing import Dict, Any
import os, json, subprocess

class QAAgent(BaseAgent):
    async def respond(self, message: str, context: Dict[str, Any]) -> str:
        self.messages_handled += 1
        self.status = "working"
        receipt_dir = os.getenv("EMPIRE_RECEIPTS", "/tmp/empire-receipts")
        task_id = context.get("task_id", "unknown")
        receipt_path = os.path.join(receipt_dir, f"{task_id}.json")
        verdict = "❌ NO RECEIPT FOUND — BLOCKING COMPLETION"
        if os.path.exists(receipt_path):
            with open(receipt_path) as f:
                receipt = json.load(f)
            tests = receipt.get("test_results", {})
            files = receipt.get("files_created", [])
            files_exist = [os.path.exists(f) for f in files]
            if all(files_exist) and (tests.get("success") or tests.get("returncode") == 0):
                verdict = "✅ VERIFICATION PASSED — Task may complete"
            else:
                missing = [f for f, e in zip(files, files_exist) if not e]
                verdict = f"❌ VERIFICATION FAILED — Missing files: {missing}, Tests: {tests}"
        lint = subprocess.run("python -m py_compile main.py", shell=True, capture_output=True, text=True)
        lint_ok = lint.returncode == 0
        self.status = "idle"
        return f"""🧪 **QA Agent — Verification Report**

Task: `{task_id}`
Receipt: `{receipt_path}`
Verdict: {verdict}
Lint check main.py: {'PASS' if lint_ok else 'FAIL'}

I do not approve completion without a valid receipt and passing tests."""
