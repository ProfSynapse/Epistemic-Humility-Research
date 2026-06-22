---
aliases:
- tool-calling agent
- tool-using agent
- function-calling agent
tags:
- kg/term
- concept
- term
kg:
  id: term:tool-calling-agent
  type: term
  status: canonical
area: agent-safety
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[ledgeragent]]'
relationships:
- type: studied_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: related_to
  target: '[[ledgeragent]]'
  target_id: method:ledgeragent
---

A tool-calling agent is an LLM-based agent that can invoke external tools or
APIs during an interaction. In customer-service settings, tool calls may read
records, update orders, issue refunds, change reservations, or otherwise modify
external state.

**Why it matters here:** Tool-calling agents make epistemic boundaries
operational: an agent must distinguish observed state from inferred or stale
state before taking consequential actions.
