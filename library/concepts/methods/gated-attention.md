---
aliases:
- gated attention
- attention output gating
- conditional attention gating
tags:
- kg/method
- concept
- method
kg:
  id: method:gated-attention
  type: method
  status: canonical
area: methods
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[attention-sink]]'
relationships:
- type: used_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
---

Gated attention augments the attention block with an input-conditioned
(per-channel or per-head) multiplicative gate applied to the attention output,
giving the model an explicit, learned mechanism to suppress or pass through
attention contributions rather than relying only on the softmax distribution
itself.

**Why it matters here:** Sun et al. use gated attention as an ablation arm: an
input-conditioned gate (per-channel or per-head) sharply reduces the sink ratio
with negligible perplexity cost, while unconditional or static (positional or
token-embedding) gates fail to suppress sinks, showing attention sinks function
as a learned, input-dependent gating workaround that the model abandons once
given an explicit gate.

**Lineage:** an architectural intervention studied here as an alternative to the
implicit gating role attention sinks otherwise play.
