---
aliases:
- RMSNorm
- Root Mean Square Layer Normalization
tags:
- kg/method
- concept
- method
kg:
  id: method:rms-norm
  type: method
  status: canonical
area: methods
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[residual-stream]]'
relationships:
- type: used_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

RMSNorm is a simplification of LayerNorm that rescales activations by their
root-mean-square statistic without re-centering on the mean, and is the
normalization used in the pre-norm blocks of most modern Llama/Qwen-family
transformers.

**Why it matters here:** Sun et al. identify the pre-norm RMSNorm configuration
as the specific architectural choice that couples massive activations and
attention sinks; ablating it (sandwich normalization, DynamicTanh) suppresses
spike magnitude while leaving the sink ratio largely unchanged, isolating
RMSNorm placement rather than normalization per se as the causal factor.

**Lineage:** the normalization component of the pre-norm transformer block used
across all seven models this paper evaluates.
