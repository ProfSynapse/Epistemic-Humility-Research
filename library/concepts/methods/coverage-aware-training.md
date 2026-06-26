---
aliases:
- task-uniform sampling
- coverage-aware sampling
- Coverage-Aware Training
tags:
- kg/method
- concept
- method
kg:
  id: method:coverage-aware-training
  type: method
  status: canonical
area: methods
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[state-action-coverage-gap]]'
relationships:
- type: proposed_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: related_to
  target: '[[state-action-coverage-gap]]'
  target_id: term:state-action-coverage-gap
---

A data resampling technique for world model training that samples uniformly across tasks rather than uniformly across frames. This upweights under-represented tasks in the training corpus, closing the [[state-action-coverage-gap]] at finetuning time. Applied as a finetuning recipe for the tokenizer and dynamics model separately or jointly, it outperforms loss-reweighting variants at reducing hallucination.

**Why it matters here:** Coverage-aware training is a tractable, data-level fix for epistemic gaps in learned world models, demonstrating that targeted distribution balancing can close specific failure modes rather than requiring more data in aggregate.

**Lineage:** related to [[state-action-coverage-gap]]; introduced by [[2606.27326--hallucination-world-models-predictable-preventable]].
