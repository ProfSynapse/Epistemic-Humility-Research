---
aliases:
- massive activations
- massive activation
tags:
- kg/term
- concept
- term
kg:
  id: term:massive-activations
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2402.17762--massive-activations-large-language-models]]'
- '[[attention-sink]]'
- '[[implicit-attention-bias]]'
- '[[rogue-dimensions]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2402.17762--massive-activations-large-language-models]]'
  target_id: paper:2402.17762
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
- type: related_to
  target: '[[implicit-attention-bias]]'
  target_id: term:implicit-attention-bias
  confidence: high
- type: related_to
  target: '[[rogue-dimensions]]'
  target_id: term:rogue-dimensions
  confidence: medium
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Massive activations are extremely rare scalar values in a transformer's
residual-stream hidden state whose magnitude exceeds roughly 100 and is about a
thousand times or more the median of that hidden state. Sun et al. find fewer
than about ten among tens of millions of activations, confined to a couple of
fixed feature dimensions (for example dimensions 1415 and 2533 in LLaMA2-7B) at
special token positions, the starting token and the first delimiter such as a
period or newline. Their values stay nearly constant across inputs, so they act
as fixed implicit bias terms: setting them to their mean leaves the model
unchanged while zeroing them collapses it, and they induce attention sinks by
concentrating attention on the tokens that carry them.

**Why it matters here:** massive activations are a prime nuisance identity for
the displacement census. A handful of fixed coordinates carrying enormous,
input-agnostic magnitude will dominate any raw norm or covariance of the
out-of-span residual while being outcome-blind. They must be identified and set
aside (per-coordinate kurtosis scan, checkpoint stability check) before the
residual is treated as candidate signal.

**Lineage:** cause of [[attention-sink]] via an [[implicit-attention-bias]];
distinct from [[rogue-dimensions]] and outlier features (a scalar at few tokens
versus a whole dimension large across most tokens) though both are large,
input-driven-invariant coordinates in the [[residual-stream]].
