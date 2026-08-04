---
aliases:
- SwiGLU
- Swish-Gated Linear Unit
tags:
- kg/method
- concept
- method
kg:
  id: method:swiglu
  type: method
  status: canonical
area: methods
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
relationships:
- type: used_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
---

SwiGLU is a gated feed-forward variant that multiplies a Swish-activated linear
projection elementwise by a second linear projection before the output
projection, and is the feed-forward block used in Llama- and Qwen-family
transformers in place of a plain ReLU/GELU MLP.

**Why it matters here:** Sun et al. trace massive activations to a quadratic
amplification effect in SwiGLU's elementwise gating multiplication, showing the
feed-forward block that injects the step-up spike into the residual stream
depends on this specific gated-multiplicative form rather than being an
incidental property of any MLP.

**Lineage:** the feed-forward component of the pre-norm transformer block used
across all seven models this paper evaluates.
