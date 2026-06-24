---
aliases:
- final layers concentrate discriminative gradient signal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:final-layers-concentrate-discriminative-gradient-signal
  type: mechanism
  status: canonical
cause: "Restricting Grad Detect's gradient features to the final five transformer layers."
effect: "Over 97% of the discriminative signal for hallucination and abstention prediction is retained, enabling efficient deployment with minimal performance loss."
polarity: enables
related:
- '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
- '[[grad-detect]]'
- '[[knowledge-boundary]]'
relationships:
- type: supported_by
  target: '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
  target_id: paper:2606.24790
  confidence: high
- type: related_to
  target: '[[grad-detect]]'
  target_id: method:grad-detect
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: low
---

Through layer ablation across all eleven models from four architectural
families, Kamat et al. find that the last five layers concentrate over 97% of
the discriminative gradient signal Grad Detect relies on. Dropping the earlier
layers therefore costs almost no detection performance while sharply cutting the
gradient features that must be stored and scored, which is what makes a
single-backward-pass detector cheap enough to run at inference time. The result
also localizes where correctness-relevant failure signal lives in the network.
