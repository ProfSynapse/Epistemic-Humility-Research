---
aliases:
- task state ledger
- structured task state
- ledger state
tags:
- kg/term
- concept
- term
kg:
  id: term:task-state-ledger
  type: term
  status: canonical
area: agent-safety
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[ledgeragent]]'
- '[[policy-gate]]'
relationships:
- type: proposed_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: part_of
  target: '[[ledgeragent]]'
  target_id: method:ledgeragent
  confidence: high
- type: used_by
  target: '[[policy-gate]]'
  target_id: method:policy-gate
  confidence: high
---

A task-state ledger is a structured representation of facts, identifiers,
constraints, and conditions observed through successful tool calls. In
LedgerAgent, it is a typed dictionary keyed by canonical schema paths and
updated only from observed read-tool returns.

**Why it matters here:** Explicit state reduces reliance on transcript
reconstruction and helps separate what the agent has observed from what it may
infer or assume.
