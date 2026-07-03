---
aliases:
- OR-Bench
- or-bench over-refusal benchmark
- Or-Bench
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:or-bench
  type: dataset
  status: canonical
area: safety-evaluation
related: []
relationships: []
---

OR-Bench is an over-refusal benchmark containing harmless prompts that superficially resemble harmful ones, designed to measure how often a safety-tuned model refuses benign queries. The prompts are constructed to trigger surface-level pattern matching (keywords, phrasing) associated with harm without expressing genuine harmful intent, so a well-calibrated model should answer them while a miscalibrated safety system refuses. OR-Bench is commonly paired with a harmful-prompt set to construct balanced fine-tuning datasets that teach models to distinguish genuine harm from superficially similar benign queries.

**Why it matters here:** Over-refusal is the flip side of under-refusal: a model with good epistemic calibration should refuse genuinely dangerous requests while engaging with harmless ones, and OR-Bench operationalizes that distinction for empirical evaluation.

**Lineage:** standalone benchmark; no parent method in this graph.
