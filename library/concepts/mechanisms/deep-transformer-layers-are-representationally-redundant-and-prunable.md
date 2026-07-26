---
aliases:
- Deep Layers Are Representationally Redundant
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:deep-transformer-layers-are-representationally-redundant-and-prunable
  type: mechanism
  status: canonical
cause: Position of a transformer layer in the deeper (later) portion of the layer stack, as measured by low angular distance between the hidden states entering and leaving a candidate block
effect: The block can be removed outright and the remaining layers reconnected, then healed with a small amount of QLoRA finetuning, with only minimal degradation in QA-benchmark accuracy -- up to roughly half of a model's layers can be dropped this way for some model families
polarity: enables
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[layer-pruning]]'
- '[[angular-distance]]'
- '[[qlora]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: related_to
  target: '[[layer-pruning]]'
  target_id: method:layer-pruning
  confidence: high
- type: related_to
  target: '[[angular-distance]]'
  target_id: metric:angular-distance
  confidence: high
- type: related_to
  target: '[[qlora]]'
  target_id: method:qlora
  confidence: medium
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Deeper blocks of transformer layers are more similar to their immediate
neighbors (lower angular distance between the hidden state entering and
leaving the block) than shallow blocks are, with the exception of the
block touching the final layer. This representational redundancy means the
deep blocks can be pruned outright -- their transformation approximated by
the identity -- and, after a small amount of QLoRA healing, the model
recovers most of its QA-benchmark accuracy even after removing a large
fraction of its total depth.

**Why it matters here:** This is the paper's headline mechanism: it reframes
"how much of a pretrained transformer's depth is load-bearing for the
knowledge needed on common QA benchmarks" and motivates the paper's two
follow-on findings, that loss and QA accuracy decouple under pruning and
that pruning harms reasoning tasks more than knowledge-recall tasks.

**Lineage:** established in arXiv:2403.17887 (Figures 1, 2, 4, 5) across
Llama-2, Qwen, Mistral-7B, and Phi-2.
