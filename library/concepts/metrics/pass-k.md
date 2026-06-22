---
aliases:
- pass^k
- pass@k
- multi-trial pass rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:pass-k
  type: metric
  status: canonical
area: agent-safety
related:
- '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
- '[[tool-calling-agent]]'
relationships:
- type: measured_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: related_to
  target: '[[tool-calling-agent]]'
  target_id: term:tool-calling-agent
---

pass^k is a multi-trial task-success metric used in LedgerAgent: a task receives
pass^k only if all k independent trials pass. pass^1 measures single-run
success, while pass^4 is used as a stricter consistency measure.

**Why it matters here:** Multi-trial success is useful for agentic reliability
because a tool-calling agent that succeeds once but fails under reruns may still
be unsafe for consequential workflows.
