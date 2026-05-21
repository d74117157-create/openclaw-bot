"""
OpenClaw — worker/agents/research.py
RESEARCH AGENT: Discovers APIs, tools, docs, integration patterns.
"""
from worker.ai_worker import process_task, _chat

SYSTEM = (
    "You are the RESEARCH AGENT of OpenClaw. You discover APIs, tools, libraries, "
    "integration patterns, and technical documentation. "
    "Rules: validate sources, cite versions, flag deprecated info, recommend alternatives. "
    "Always return:\n"
    "FINDINGS: <structured research results>\n"
    "RECOMMENDED LIBRARIES: <with versions>\n"
    "INTEGRATION PATTERN: <how to implement>\n"
    "GOTCHAS: <known issues or limits>\n"
    "SOURCES: <docs URLs>"
)


def research_api(api_name: str) -> str:
    return _chat(SYSTEM, f"Research the {api_name} API: endpoints, auth, rate limits, SDKs, examples.")


def research_tool(tool_name: str, use_case: str = "") -> str:
    return _chat(SYSTEM, f"Research {tool_name} for: {use_case}. Compare alternatives.")


def research_integration(service_a: str, service_b: str) -> str:
    return _chat(SYSTEM, f"Research integration pattern between {service_a} and {service_b}.")


def research_best_practices(domain: str) -> str:
    return _chat(SYSTEM, f"Research current best practices for: {domain}")


def compare_tools(tools: list, criteria: str) -> str:
    tool_list = ", ".join(tools)
    return _chat(SYSTEM, f"Compare these tools: {tool_list}. Criteria: {criteria}")


def run(task: str) -> str:
    return process_task(task, "research")
