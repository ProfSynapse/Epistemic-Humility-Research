---
aliases:
- Explicit Ledger State Prevents Policy-Violating Writes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:explicit-ledger-state-prevents-policy-violating-writes
  type: mechanism
  status: canonical
cause: A [[task-state-ledger]] stores observed records under stable schema paths and a [[policy-gate]] checks proposed environment-changing tool calls against those records
effect: Tool-calling agents make fewer stale-state or policy-violating writes and improve pass^k reliability on customer-service tasks
polarity: prevents
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[ledgeragent]]'
- '[[task-state-ledger]]'
- '[[policy-gate]]'
- '[[pass-k]]'
relationships:
- type: supported_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: related_to
  target: '[[ledgeragent]]'
  target_id: method:ledgeragent
- type: related_to
  target: '[[task-state-ledger]]'
  target_id: term:task-state-ledger
- type: related_to
  target: '[[policy-gate]]'
  target_id: method:policy-gate
- type: related_to
  target: '[[pass-k]]'
  target_id: metric:pass-k
---

LedgerAgent externalizes observed task state into a typed ledger and applies
policy predicates before environment-changing tool calls execute. The paper
reports that this setup improves pass^k over standard function-calling baselines
and is especially useful for tasks involving writes such as refunds,
reservation changes, and account updates.

**Why it matters here:** The mechanism separates grounded state from model
inference and keeps irreversible actions behind a deterministic compliance
check, a useful pattern for agentic systems that must act only on observed
facts.
