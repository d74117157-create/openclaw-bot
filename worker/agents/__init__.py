# OpenClaw — agents package
from worker.agents.coder import run as coder
from worker.agents.reviewer import run as reviewer
from worker.agents.qa import run as qa
from worker.agents.ops import run as ops
from worker.agents.research import run as research
from worker.agents.growth import run as growth
from worker.agents.memory_agent import run as memory
from worker.agents.business_agent import run as business

AGENT_DISPATCH = {
    "coder":        coder,
    "reviewer":     reviewer,
    "qa":           qa,
    "ops":          ops,
    "research":     research,
    "growth":       growth,
    "memory":       memory,
    "business":     business,
    "orchestrator": business,  # default → business agent
    "researcher":   research,
}
