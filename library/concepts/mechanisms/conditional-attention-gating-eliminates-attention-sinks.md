---
aliases:
- input-conditioned attention gating eliminates attention sinks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:conditional-attention-gating-eliminates-attention-sinks
  type: mechanism
  status: canonical
cause: "an input-conditioned (per-channel or per-head) attention gate is added to a transformer's attention block, giving the model an explicit learned suppression mechanism."
effect: "attention sinks are eliminated: sink ratio drops from 46.0% to 4.5%/6.4% and spike magnitude falls from 3818 to roughly 190-200 with negligible perplexity change, whereas unconditional or static (positional/token-embedding) gates fail to suppress sinks."
polarity: prevents
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[attention-sink]]'
- '[[gated-attention]]'
relationships:
- type: supported_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
- type: related_to
  target: '[[gated-attention]]'
  target_id: method:gated-attention
  confidence: high
---

Sun et al. show attention sinks can be eliminated by input-conditioned
(per-channel or per-head) attention gating: sink ratio drops from 46.0% to
4.5%/6.4% and spike magnitude falls from 3818 to roughly 190-200 with
negligible perplexity change, whereas unconditional or static
(positional/token-embedding) gates fail to suppress sinks. This indicates sinks
function as a learned, input-dependent gating workaround the model abandons
once given an explicit gate (Table 7; Section 4.3.2).
