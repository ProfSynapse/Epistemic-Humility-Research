---
aliases:
- tau2-Bench
- tau2-bench
- tau^2-Bench
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:tau2-bench
  type: dataset
  status: canonical
area: agent-safety
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[tool-calling-agent]]'
relationships:
- type: evaluation_set_for
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: related_to
  target: '[[tool-calling-agent]]'
  target_id: term:tool-calling-agent
---

tau2-Bench is a customer-service benchmark for interactive tool-agent-user
tasks. LedgerAgent uses its airline, retail, and telecom domains to evaluate
policy-adherent tool use under single-control and dual-control settings.

**Why it matters here:** The benchmark makes state tracking and policy
compliance measurable in multi-turn agent interactions.
