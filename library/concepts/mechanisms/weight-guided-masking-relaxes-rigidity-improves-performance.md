---
aliases:
- weight-guided masking relaxes rigidity and improves performance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:weight-guided-masking-relaxes-rigidity-improves-performance
  type: mechanism
  status: canonical
cause: "weight-guided masking (WeMask) masks a top-weighted subset of the massive-activation token's dimensions, reducing the directional rigidity of that token's hidden state."
effect: "downstream performance improves across instruction-following, math-reasoning, and safety-alignment tasks, both training-free at inference time and when incorporated into SFT/DPO/GRPO training; masking 100% of the top-weighted dimensions instead catastrophically degrades performance."
polarity: enables
related:
- '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
- '[[weight-guided-masking]]'
- '[[massive-activation-directional-rigidity-reduces-attention-diversity]]'
relationships:
- type: supported_by
  target: '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
  target_id: paper:2605.08504
  confidence: high
- type: related_to
  target: '[[weight-guided-masking]]'
  target_id: method:weight-guided-masking
  confidence: high
- type: related_to
  target: '[[massive-activation-directional-rigidity-reduces-attention-diversity]]'
  target_id: mechanism:massive-activation-directional-rigidity-reduces-attention-diversity
  confidence: high
---

Shi et al. show that WeMask's partial masking of the massive-activation
token's top-weighted dimensions consistently improves downstream performance
across instruction-following, math-reasoning, and safety-alignment tasks, in
both training-free inference-time and fine-tuning (SFT, DPO, GRPO) settings.
The benefit is dosed, not monotonic in mask fraction: masking 100% of the
top-weighted dimensions catastrophically degrades performance, indicating the
gain comes specifically from relaxing (not eliminating) the token's
directional rigidity.

**Lineage:** established by
[[2605.08504--single-layer-explain-them-all-understanding-massive]]; the
performance consequence of [[weight-guided-masking]] acting on the rigidity
described in
[[massive-activation-directional-rigidity-reduces-attention-diversity]].
