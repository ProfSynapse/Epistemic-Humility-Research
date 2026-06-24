---
aliases:
- truthfulness signal concentrates in sparse attention-head positions
- attention-head superiority for truthfulness probing
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:attention-head-truthfulness-concentration
  type: mechanism
  status: canonical
cause: "Selecting 1 or 2 attention-head output positions (out of 1,024 candidates across 32 layers and 32 heads) as features for a linear truthfulness probe"
effect: "Cross-task probe accuracy is at least 3 points higher than probes trained on layer residual activations, with no benefit from selecting more than 2 positions"
polarity: enables
related:
- '[[2407.08582--generalizable-truth-probes]]'
- '[[universal-truthfulness-probe]]'
- '[[universal-truthfulness-hyperplane]]'
- '[[truth-direction]]'
- '[[final-layers-concentrate-discriminative-gradient-signal]]'
- '[[inference-time-intervention]]'
relationships:
- type: supported_by
  target: '[[2407.08582--generalizable-truth-probes]]'
  target_id: paper:2407.08582
  confidence: high
- type: related_to
  target: '[[universal-truthfulness-probe]]'
  target_id: method:universal-truthfulness-probe
  confidence: high
- type: related_to
  target: '[[universal-truthfulness-hyperplane]]'
  target_id: term:universal-truthfulness-hyperplane
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[final-layers-concentrate-discriminative-gradient-signal]]'
  target_id: mechanism:final-layers-concentrate-discriminative-gradient-signal
  confidence: high
- type: related_to
  target: '[[inference-time-intervention]]'
  target_id: method:inference-time-intervention
  confidence: high
---

The paper finds that the truthfulness signal in LLM hidden states is concentrated in a small number of attention-head output positions, not broadly distributed in the residual stream. Training preliminary probes on each of 1,024 candidate positions and keeping the top 1-2 by validation accuracy yields the best final probe. This is analogous to the final-layers-concentrate-discriminative-gradient-signal finding for gradient-based detection, but localized to attention-head outputs rather than late-layer gradient norms. The sparsity finding implies that truthfulness may be encoded as a direction along a small number of attention heads, consistent with the universal-truthfulness-hyperplane hypothesis.
