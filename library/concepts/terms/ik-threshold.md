---
aliases:
- I-know threshold
- confidence threshold for known/unknown labeling
tags:
- kg/term
- concept
- term
kg:
  id: term:ik-threshold
  type: term
  status: canonical
area: terms
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[idk-dataset]]'
- '[[knowledge-quadrant-metric]]'
relationships:
- type: proposed_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: related_to
  target: '[[idk-dataset]]'
  target_id: dataset:idk-dataset
- type: related_to
  target: '[[knowledge-quadrant-metric]]'
  target_id: metric:knowledge-quadrant-metric
---

The Ik threshold is a hyperparameter in [0, 1] that sets the minimum per-question
accuracy rate above which a model is considered to "know" a question. Questions
with sampled accuracy at or above the threshold are labeled known and paired with
answer responses; questions below it are labeled unknown and paired with refusal
responses in the [[idk-dataset]]. Higher thresholds yield more conservative
(refusal-heavy) training sets.

**Why it matters here:** The threshold controls the precision-recall trade-off
between over-refusal and hallucination in abstention-training pipelines, a
tension central to the Phase 1 study comparing SFT, DPO, and KTO on the same
abstention objective.

**Lineage:** proposed alongside the [[idk-dataset]] in
[[2401.13275--can-ai-assistants-know-what-they-dont-know]].
