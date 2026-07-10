"""
OpenClaw - worker/ai_worker.py
Groq LLM engine with 8 agent personas for task processing.
"""
import os, json
from groq import Groq

load_dotenv = __import__('dotenv').load_dotenv
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama3-70b-8192")

client = None


def _get_client():
    global client
    if client is None:
        client = Groq(api_key=GROQ_API_KEY)
    return client


AGENT_PERSONAS = {
    "orchestrator": "You are the Orchestrator. Break down tasks into steps and delegate to other agents.",
    "coder": "You are the Coder. Write clean, tested Python code. Return only the code.",
    "reviewer": "You are the Code Reviewer. Review code for bugs, security, and style issues.",
    "qa": "You are the QA Engineer. Write tests and verify functionality.",
    "ops": "You are the DevOps Engineer. Handle deployments, infrastructure, and CI/CD.",
    "research": "You are the Researcher. Gather information and provide detailed analysis.",
    "growth": "You are the Growth Engineer. Optimize for user acquisition and retention.",
    "memory": "You are the Memory Agent. Store and retrieve information from the database.",
    "github": "You are the GitHub Agent. Manage repositories, branches, PRs, and issues.",
}


def _chat(system: str, user: str, temperature: float = 0.3) -> str:
    c = _get_client()
    resp = c.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=4096,
    )
    return resp.choices[0].message.content


def process_task(task: str, agent: str = "orchestrator") -> str:
    persona = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["orchestrator"])
    return _chat(persona, task)


def orchestrate_task(task: str) -> str:
    system = (
        "You are the Orchestrator. Break down the following task into a JSON array of steps. "
        "Each step must have 'agent' and 'task' keys. "
        "Available agents: coder, reviewer, qa, ops, research, growth, memory, github. "
        "Return ONLY valid JSON."
    )
    raw = _chat(system, task, temperature=0.1)
    # Extract JSON if wrapped in markdown
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    return raw.strip()
