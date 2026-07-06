---
aliases:
- implicit attention bias
- implicit bias term
tags:
- kg/term
- concept
- term
kg:
  id: term:implicit-attention-bias
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2402.17762--massive-activations-large-language-models]]'
- '[[massive-activations]]'
- '[[attention-sink]]'
relationships:
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
- type: proposed_by
  target: '[[2402.17762--massive-activations-large-language-models]]'
  target_id: paper:2402.17762
  confidence: high
---

An implicit attention bias is a constant, input-independent additive term the
self-attention output acquires because attention concentrates on massive-
activation tokens whose value updates are near-identical across query positions.
The model learns this bias implicitly through massive activations rather than as
an explicit parameter; Sun et al. show that augmenting attention with an
explicit learnable bias key and value eliminates massive activations entirely,
confirming the two are functionally equivalent.

**Why it matters here:** it is the mechanistic reason a few fixed coordinates
carry a fixed, content-independent contribution to every hidden state, which the
census will see as a large but outcome-blind offset.

**Lineage:** the functional role of [[massive-activations]]; the cause of
[[attention-sink]] behavior.
