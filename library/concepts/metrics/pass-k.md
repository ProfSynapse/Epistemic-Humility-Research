---
aliases:
- pass^k
- pass to the k
- all-k-trials-pass rate
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
- '[[pass-at-k]]'
relationships:
- type: measured_by
  target: '[[2606.20529--ledgeragent-structured-state-policy-adherent-tool-calling]]'
  target_id: paper:2606.20529
  confidence: high
- type: related_to
  target: '[[tool-calling-agent]]'
  target_id: term:tool-calling-agent
- type: different_from
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: high
  note: "Opposite quantifier: pass^k requires ALL k trials to pass, pass@k requires AT LEAST ONE of k. Near-identical surface forms; do not conflate."
---

Not to be confused with [[pass-at-k]] (Pass@k), which requires at least one of k
attempts to succeed. pass^k requires all of them. The two are opposite
quantifiers over the same k trials.

pass^k is a multi-trial task-success metric used in LedgerAgent: a task receives
pass^k only if all k independent trials pass. pass^1 measures single-run
success, while pass^4 is used as a stricter consistency measure.

**Why it matters here:** Multi-trial success is useful for agentic reliability
because a tool-calling agent that succeeds once but fails under reruns may still
be unsafe for consequential workflows.
