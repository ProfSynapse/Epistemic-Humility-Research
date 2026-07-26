---
aliases:
- layer skip
- skipping layers
tags:
- kg/method
- concept
- method
kg:
  id: method:layer-skipping
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[residual-stream]]'
relationships:
- type: used_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

Layer skipping removes one or more transformer layers from the forward pass at
inference time on an otherwise-frozen pretrained model: the layer's input is
passed directly to the next layer, and the skipped layer's transformation is
never applied. No retraining or weight modification is involved, which makes
the technique a clean probe of how load-bearing a given layer's contribution
to the residual stream actually is.

**Why it matters here:** Used as the baseline intervention in the
layers-as-painters study to establish that several middle layers can be
skipped with only graceful benchmark degradation, in contrast to the
catastrophic degradation from skipping first or last layers, and as the
control condition that middle-layer weight sharing is compared against.

**Lineage:** applied to Llama2-7B, Llama2-13B, Llama2-70B, and BERT-Large in
arXiv:2407.09298.
