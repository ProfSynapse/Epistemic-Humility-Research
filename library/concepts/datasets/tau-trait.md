---
aliases:
- tau-Trait
- tau trait
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:tau-trait
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

tau-Trait is an interactive customer-service benchmark used by LedgerAgent for
the telehealth domain. It preserves the structured tool-use setting while
testing agent behavior under simulated user traits.

**Why it matters here:** It supplies a tool-use setting where state and policy
adherence must hold across dialogue rather than a single API call.
