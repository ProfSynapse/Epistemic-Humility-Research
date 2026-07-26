---
aliases:
- pre-norm RMSNorm couples massive activations and attention sinks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pre-norm-configuration-couples-massive-activations-and-attention-sinks
  type: mechanism
  status: canonical
cause: "a transformer uses pre-norm RMSNorm placement (normalization applied before, not after, each sublayer's residual write)."
effect: "massive activations and attention sinks co-occur at the same token positions as an architectural artifact rather than a functional necessity; ablating the normalization configuration (sandwich normalization, DynamicTanh) decouples them, cutting spike magnitude by roughly 86-96% while leaving the sink ratio nearly unchanged or higher."
polarity: enables
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[massive-activations]]'
- '[[attention-sink]]'
- '[[rms-norm]]'
relationships:
- type: supported_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
- type: related_to
  target: '[[rms-norm]]'
  target_id: method:rms-norm
  confidence: high
---

Sun et al. identify pre-norm RMSNorm as the key architectural choice that
enables the frequently-reported co-occurrence of massive activations and
attention sinks. Swapping in sandwich normalization or DynamicTanh suppresses
spike magnitude by roughly 86-96% (3818 to 520/153) relative to the pre-norm
RMSNorm baseline while the sink ratio stays nearly unchanged or increases,
showing the two phenomena are architecturally coupled rather than functionally
bound to each other (Table 5; Section 4.2.2).
