---
aliases:
- Loss/Accuracy Decoupling Under Pruning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layer-pruning-decouples-loss-continuity-from-qa-accuracy-phase-transition
  type: mechanism
  status: canonical
cause: Fraction of layers removed by similarity-informed layer pruning, after QLoRA healing
effect: Next-token-prediction loss on C4 increases smoothly and continuously with pruning fraction, while downstream QA-benchmark accuracy (MMLU, BoolQ) stays flat and then collapses sharply to random-guessing over a narrow range of pruning fractions -- the two metrics are decoupled rather than co-varying
polarity: enables
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[layer-pruning]]'
- '[[c4-corpus]]'
- '[[mmlu]]'
- '[[boolq]]'
relationships:
- type: supported_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: related_to
  target: '[[layer-pruning]]'
  target_id: method:layer-pruning
  confidence: high
- type: related_to
  target: '[[c4-corpus]]'
  target_id: dataset:c4-corpus
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[boolq]]'
  target_id: dataset:boolq
  confidence: medium
---

As layers are progressively pruned and the model healed with QLoRA, the
autoregressive next-token-prediction loss measured on C4 grows smoothly and
continuously -- there is no visible kink or discontinuity at any particular
pruning fraction. Downstream QA-benchmark accuracy (MMLU, BoolQ) behaves
completely differently: it stays roughly flat near the unpruned model's
accuracy, then transitions sharply to random-chance guessing over a narrow
band of pruning fractions that is model-family dependent. The same pruning
fraction that leaves loss barely changed can be exactly where QA accuracy
falls off a cliff.

**Why it matters here:** This decoupling is direct evidence that
perplexity/loss-style metrics are a poor proxy for downstream task capability
under structural interventions like pruning: a model can look "fine" by loss
while having already lost the specific computation a QA benchmark needs.

**Lineage:** established in arXiv:2403.17887 (Figure 3, Section 4.2), shown
to hold consistently after healing has been applied.
