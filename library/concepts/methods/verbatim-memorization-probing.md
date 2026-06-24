---
aliases:
- memorization probing
- verbatim recall probing
- original-vs-paraphrase selection task
tags:
- kg/method
- concept
- method
kg:
  id: method:verbatim-memorization-probing
  type: method
  status: canonical
area: methods
related:
- '[[2509.20088--causal-understanding-uncertainty]]'
- '[[mcqa-causal]]'
- '[[consistency-based-confidence]]'
- '[[self-consistency]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2509.20088--causal-understanding-uncertainty]]'
  target_id: paper:2509.20088
  confidence: high
- type: related_to
  target: '[[mcqa-causal]]'
  target_id: dataset:mcqa-causal
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

A behavioral test for training-data memorization in which a model is asked to select among semantically equivalent paraphrases of a sentence it may have seen during pretraining. Under the memorization hypothesis, models assign higher probability to the original verbatim form. A null result (selection rate indistinguishable from uniform) indicates the model does not exhibit a surface-form bias toward training-seen text. The method controls for answer correctness by making all options semantically equivalent, isolating surface-form preference from task performance.

**Why it matters here:** Allows disentangling recall-based familiarity from representational understanding without access to training data logs. A null result on this probe strengthens the claim that measured uncertainty reflects genuine epistemic limitations rather than missing recall of a specific token sequence.

**Lineage:** Task design follows Duarte et al. (2024) memorization detection hypothesis; instantiated for causal text by Lithgow-Serrano et al. (2025).
