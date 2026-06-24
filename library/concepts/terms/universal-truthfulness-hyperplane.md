---
aliases:
- universal truthfulness direction
- cross-task truthfulness linear separator
tags:
- kg/term
- concept
- term
kg:
  id: term:universal-truthfulness-hyperplane
  type: term
  status: canonical
area: terms
related:
- '[[2407.08582--generalizable-truth-probes]]'
- '[[truth-direction]]'
- '[[linear-probe]]'
- '[[universal-truthfulness-probe]]'
- '[[generation-discrimination-gap]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
relationships:
- type: proposed_by
  target: '[[2407.08582--generalizable-truth-probes]]'
  target_id: paper:2407.08582
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[universal-truthfulness-probe]]'
  target_id: method:universal-truthfulness-probe
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: medium
---

A hypothesized linear decision boundary in an LLM's hidden-state space that separates factually correct from incorrect outputs across diverse tasks and domains, as opposed to task-specific separators that overfit spurious distributional features of a single benchmark.

**Why it matters here:** The existence of this hyperplane would imply that truthfulness is a geometrically coherent, generalized concept in LLM representations, with direct implications for hallucination detection, mechanistic interpretability, and understanding how training affects the model's internal representation of factual accuracy.

**Lineage:** Proposed as a hypothesis to resolve the OOD generalization failure of single-dataset probes (Burns et al. 2023, Marks and Tegmark 2023). This paper provides the first systematic large-scale empirical evidence supporting its existence.
