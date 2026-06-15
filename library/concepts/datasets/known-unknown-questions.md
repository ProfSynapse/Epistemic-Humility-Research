---
aliases:
- Known-Unknown Questions
- KUQ dataset
- KUQ (Known-Unknown Questions)
- kuq
- KUQ
- Known-Unknown Questions (KUQ)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:known-unknown-questions
  type: dataset
  status: canonical
area: datasets-benchmarks
related:
- '[[2305.13712--kuq-knowledge-of-knowledge]]'
relationships:
- type: proposed_by
  target: '[[2305.13712--kuq-knowledge-of-knowledge]]'
  target_id: paper:2305.13712
  confidence: high
---

Known-Unknown Questions (KUQ) is a benchmark that pairs questions a model is observed to answer correctly with questions it is observed to answer incorrectly, enabling discriminative evaluation of refusal behaviour. Each question type spans seven semantic categories of unknowability (see [[known-unknowns-taxonomy]]), so the benchmark probes both model-specific knowledge gaps and principled limits of answerable questions. It was introduced to measure whether honesty-recovery interventions teach appropriate differential uncertainty rather than blanket hedging.

**Why it matters here:** The Phase 1 abstention study needs to distinguish genuine over-refusal from correct abstention. KUQ's known/unknown pairing lets a post-training evaluation check whether the trained model answers what it knows while abstaining on what it does not, which is the central falsifier for the alignment-tax hypotheses.

**Lineage:** proposed by [[2305.13712--kuq-knowledge-of-knowledge]]; also used in [[2511.12991--finetuned-llms-know-they-dont-know]] to evaluate post-training abstention generalization.
