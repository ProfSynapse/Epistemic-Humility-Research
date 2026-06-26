---
aliases:
- log-probability
- sequence log-probability
- continuation probability
tags:
- kg/term
- concept
- term
kg:
  id: term:sequence-probability
  type: term
  status: canonical
area: verification
related: []
relationships: []
---

The joint conditional probability p(s|s̄) that an autoregressive language model assigns to a complete continuation s given a prompt s̄, computed as the product of per-token conditional probabilities across all positions. The quantity can be examined at multiple granularity levels (within-dataset, within-method, across-method, within-sample), and whether it reliably predicts response correctness depends on which level is examined. Reliability is asymmetric: high probability is necessary but not sufficient for high accuracy, and the relationship breaks down under distribution shift or adversarial prompting.

**Why it matters here:** Sequence probability is a natural proxy for model confidence requiring no external verifier, but its inconsistent relationship to correctness across benchmarks makes it a central case study for the limits of internal confidence signals in epistemic humility research.

**Lineage:** no direct predecessors encoded in this graph.
