---
aliases:
- ACDC
- Automated Circuit Discovery (ACDC)
- MatchNLL circuit discovery
tags:
- kg/method
- concept
- method
kg:
  id: method:automated-circuit-discovery
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[attribution-patching]]'
- '[[circuit-faithfulness]]'
- '[[indirect-object-identification]]'
- '[[sparse-feature-circuits]]'
relationships:
- type: related_to
  target: '[[attribution-patching]]'
  target_id: method:attribution-patching
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
- type: related_to
  target: '[[indirect-object-identification]]'
  target_id: dataset:indirect-object-identification
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
---

Automated Circuit Discovery (ACDC) is an algorithm that identifies minimal
faithful subgraphs (circuits) in a transformer's computation graph by
iteratively ablating edges and measuring the effect on model output using a
MatchNLL objective. Edges whose removal causes a notable performance drop are
retained; the rest are pruned, yielding the smallest subgraph that reproduces
the full model's behavior on a task. The approach systematizes what was
previously done by hand: instead of manually tracing attention heads and MLP
layers, ACDC automates the search over the exponential space of possible
sub-circuits.

**Why it matters here:** Automated circuit discovery is the methodological
backbone for isolating which components mediate factual recall and epistemic
signals (confidence, abstention). Understanding these circuits is a prerequisite
for targeted interventions that improve calibration without sacrificing capability.

**Lineage:** related to [[attribution-patching]] (a faster linear approximation
for the same edge-importance ranking), [[circuit-faithfulness]] (the evaluation
criterion ACDC optimizes), and the empirical case studies in
[[indirect-object-identification]] and [[sparse-feature-circuits]].
