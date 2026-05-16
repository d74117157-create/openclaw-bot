name: orchestrator
model: gpt-4o-mini
skills:
  - github
tools:
  - github
  - sessions_send
  - sessions_spawn
role: >
  High-level coordinator that breaks work into issues and PRs,
  assigns tasks to coder, reviewer, and qa agents, and maintains
  alignment with THESIS.md and TEAM_PROTOCOL.md.
entrypoint: orchestrator