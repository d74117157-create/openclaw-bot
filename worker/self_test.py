"""
OpenClaw — worker/self_test.py
Self-test harness. Runs after every task. QA agent validates outputs.
"""
import os, json, time
from worker.ai_worker import process_task

QA_SYSTEM = """You are a QA agent validating swarm task output.
Given the original task and all agent outputs, return JSON:
{
  "passed": true,
  "score": 85,
  "summary": "one sentence verdict",
  "tests": [{"name":"test","passed":true,"detail":"detail"}],
  "issues": [],
  "recommendations": [],
  "production_ready": true
}
Be strict. Return ONLY valid JSON."""


def run_self_test(task: str, results: dict) -> dict:
    results_block = "\n\n".join(
        f"[{agent.upper()}]:\n{str(out)[:600]}"
        for agent, out in results.items()
    )
    prompt = (
        f"ORIGINAL TASK: {task}\n\n"
        f"AGENT OUTPUTS:\n{results_block}\n\n"
        f"Run comprehensive QA validation. Check:\n"
        f"1. Task completion\n"
        f"2. Output quality\n"
        f"3. Errors\n"
        f"4. Security\n"
        f"5. Completeness\n"
        f"Return JSON only."
    )
    try:
        raw   = process_task(prompt, "qa")
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(raw[start:end])
            result["timestamp"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
            return result
    except Exception:
        pass
    combined   = " ".join(str(v) for v in results.values()).lower()
    has_errors = any(kw in combined for kw in ["error:", "exception", "traceback", "failed:"])
    return {
        "passed":           not has_errors,
        "score":            60 if not has_errors else 20,
        "summary":          "Automated check: " + ("No critical errors." if not has_errors else "Errors detected."),
        "tests":            [{"name": f"{a} output", "passed": "error" not in str(r).lower(), "detail": str(r)[:100]} for a, r in results.items()],
        "issues":           ["Error keywords detected"] if has_errors else [],
        "recommendations":  ["Review agent outputs manually"],
        "production_ready": not has_errors,
        "timestamp":        time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
    }


def format_discord_embed_fields(qa: dict) -> list:
    score  = qa.get("score", 0)
    bar    = _score_bar(score)
    fields = [
        {"name": "Score",      "value": f"{bar} **{score}/100**",     "inline": True},
        {"name": "Production", "value": "Ready" if qa.get("production_ready") else "Not Ready", "inline": True},
        {"name": "Summary",    "value": qa.get("summary", "")[:200], "inline": False},
    ]
    tests = qa.get("tests", [])
    if tests:
        test_lines = "\n".join(
            f"{'OK' if t.get('passed') else 'FAIL'} {t.get('name','test')}: {t.get('detail','')[:60]}"
            for t in tests[:6]
        )
        fields.append({"name": f"Tests ({len(tests)})", "value": test_lines, "inline": False})
    issues = qa.get("issues", [])
    if issues:
        fields.append({"name": "Issues", "value": "\n".join(f"- {i}" for i in issues[:5]), "inline": False})
    recs = qa.get("recommendations", [])
    if recs:
        fields.append({"name": "Recommendations", "value": "\n".join(f"- {r}" for r in recs[:4]), "inline": False})
    return fields


def format_slack_blocks(task: str, qa: dict) -> list:
    verdict = "PASSED" if qa.get("passed") else "FAILED"
    score   = qa.get("score", 0)
    return [
        {"type": "header",
         "text": {"type": "plain_text", "text": f"QA Self-Test -- {verdict}"}},
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": f"*Task:* {task[:120]}\n*Score:* {score}/100\n*Summary:* {qa.get('summary','')}"}},
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": "\n".join(
                      f"{'OK' if t.get('passed') else 'FAIL'} {t.get('name','')}: {t.get('detail','')[:60]}"
                      for t in qa.get("tests", [])[:5]
                  ) or "No tests"}},
        {"type": "context",
         "elements": [{"type": "mrkdwn",
                       "text": f"OpenClaw QA | {qa.get('timestamp', '')}"}]},
    ]


def _score_bar(score: int, width: int = 10) -> str:
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)
