---
aliases:
- LedgerAgent
tags:
- kg/method
- concept
- method
kg:
  id: method:ledgeragent
  type: method
  status: canonical
area: agent-safety
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[task-state-ledger]]'
- '[[policy-gate]]'
- '[[tool-calling-agent]]'
relationships:
- type: proposed_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: has_component
  target: '[[task-state-ledger]]'
  target_id: term:task-state-ledger
  confidence: high
- type: has_component
  target: '[[policy-gate]]'
  target_id: method:policy-gate
  confidence: high
- type: applied_to
  target: '[[tool-calling-agent]]'
  target_id: term:tool-calling-agent
  confidence: high
---

LedgerAgent is an inference-time method for policy-adherent tool-calling agents.
It maintains a typed ledger of observed task state from read-tool returns,
renders that ledger into the prompt, and checks environment-changing tool calls
with deterministic policy predicates before execution.

**Why it matters here:** LedgerAgent is a concrete pattern for separating
observed state from model-generated plans, which is useful for agentic systems
that must avoid acting beyond what they actually know.

**Lineage:** introduced in
[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]].
