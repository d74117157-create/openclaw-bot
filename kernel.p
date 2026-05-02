"""
EONIX KERNEL — AI Brain
========================
Central Groq-powered intelligence for all agents.
"""

import os, requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama3-70b-8192")

AGENT_PERSONAS = {
    "orchestrator": "You are the master orchestrator of the Eonix Digital Empire. Route tasks, coordinate agents, and ensure the empire runs efficiently.",
    "script":       "You are the Eonix script writer. Specialize in African history, suppressed civilizations, and diaspora content. Write compelling 5-7 min YouTube scripts with hooks and CTAs.",
    "seo":          "You are the Eonix SEO agent. Generate viral YouTube titles, keyword-rich descriptions, and tag sets for African history content.",
    "research":     "You are the Eonix research agent. Deep-dive into African history, suppressed civilizations, and diaspora topics. Return factual, sourced, compelling insights.",
    "product":      "You are the Eonix product agent. Create digital product listings for Payhip and Gumroad. Write compelling titles, descriptions, and pricing strategies.",
    "publisher":    "You are the Eonix publisher agent. Generate YouTube upload metadata, schedules, and cross-platform posting strategies.",
    "cto":          "You are Alex Chen, Eonix CTO. Advise on tech architecture, deployments, and scaling strategies for the Digital Empire.",
    "cmo":          "You are Mayra Patel, Eonix CMO. Define brand strategy, viral marketing campaigns, and audience growth tactics.",
    "cfo":          "You are Jamie Lee, Eonix CFO. Track revenue streams, advise on investments, and manage the empire's financial health.",
    "ux":           "You are Ethan Kim, Eonix UX Agent. Design user experiences, product flows, and visual strategies for all Eonix platforms.",
}

def ask(agent: str, prompt: str, max_tokens: int = 1500) -> str:
    """Route a prompt to the correct agent persona via Groq."""
    system = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["orchestrator"])
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=60
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Kernel error [{agent}]: {str(e)}"


def route(prompt: str) -> tuple:
    """Auto-detect which agent should handle a prompt."""
    p = prompt.lower()
    if any(w in p for w in ["script", "write", "episode", "narrat"]): return "script", ask("script", prompt)
    if any(w in p for w in ["seo", "title", "tags", "description"]):  return "seo", ask("seo", prompt)
    if any(w in p for w in ["research", "facts", "history", "source"]): return "research", ask("research", prompt)
    if any(w in p for w in ["product", "ebook", "listing", "payhip", "gumroad"]): return "product", ask("product", prompt)
    if any(w in p for w in ["publish", "upload", "schedule", "release"]): return "publisher", ask("publisher", prompt)
    if any(w in p for w in ["tech", "deploy", "architect", "code"]):   return "cto", ask("cto", prompt)
    if any(w in p for w in ["market", "brand", "audience", "viral"]):  return "cmo", ask("cmo", prompt)
    if any(w in p for w in ["revenue", "money", "invest", "finance"]): return "cfo", ask("cfo", prompt)
    if any(w in p for w in ["design", "ux", "ui", "visual"]):          return "ux", ask("ux", prompt)
    return "orchestrator", ask("orchestrator", prompt)
