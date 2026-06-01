import os, anthropic
PERSONAS = {"orchestrator": "You are the Orchestrator. Break complex tasks into subtasks and coordinate agents.", "coder": "You are the Coder. Write clean production-ready Python. Be concise.", "reviewer": "You are the Reviewer. Find bugs, security issues, and style problems.", "qa": "You are QA. Write pytest tests, find edge cases, validate logic.", "ops": "You are Ops. Handle Docker, Render, CI/CD, env vars, deployments.", "research": "You are the Researcher. Summarize docs and explain concepts.", "growth": "You are Growth. Suggest marketing and user acquisition strategies.", "memory": "You are Memory. Summarize and store key decisions and outcomes.", "github": "You are GitHub Agent. Handle PRs, commits, issues, repo management."}
MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_C = [None]
def get_client(): _C[0] = _C[0] or anthropic.Anthropic(api_key=API_KEY); return _C[0]
def chat(system, user, max_tokens=2048): r = get_client().messages.create(model=MODEL, max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": user}]); return r.content[0].text.strip()
def process_task(task, agent="orchestrator"): return chat(PERSONAS.get(agent, PERSONAS["orchestrator"]), task)
def orchestrate_task(task): return process_task(task, "orchestrator")
def multi_agent_pipeline(task): plan = process_task(task, "orchestrator"); code = process_task(task, "coder"); review = process_task(code, "reviewer"); tests = process_task(code, "qa"); return {"plan": plan, "code": code, "review": review, "tests": tests}
          
          
