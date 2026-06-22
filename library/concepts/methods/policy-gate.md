---
aliases:
- policy gate
- action-boundary policy gate
tags:
- kg/method
- concept
- method
kg:
  id: method:policy-gate
  type: method
  status: canonical
area: agent-safety
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[ledgeragent]]'
- '[[task-state-ledger]]'
relationships:
- type: proposed_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: part_of
  target: '[[ledgeragent]]'
  target_id: method:ledgeragent
  confidence: high
- type: uses
  target: '[[task-state-ledger]]'
  target_id: term:task-state-ledger
  confidence: high
---

A policy gate is an executable check that runs before an environment-changing
tool call is executed. In LedgerAgent, the gate evaluates the proposed call
against domain predicates over the current task-state ledger and returns allow,
revise, or block.

**Why it matters here:** A policy gate moves compliance checks to the action
boundary, preventing invalid writes instead of relying only on model reasoning
or post-hoc correction.

**Lineage:** introduced as a component of [[ledgeragent]] in
[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]].
