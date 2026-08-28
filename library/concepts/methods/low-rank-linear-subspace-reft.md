---
aliases:
- LoReFT
- Low-rank Linear Subspace ReFT
tags:
- kg/method
- concept
- method
kg:
  id: method:low-rank-linear-subspace-reft
  type: method
  status: canonical
area: methods
related:
- '[[2404.03592--reft-representation-finetuning-language-models]]'
- '[[representation-finetuning]]'
- '[[low-rank-adaptation]]'
relationships:
- type: proposed_by
  target: '[[2404.03592--reft-representation-finetuning-language-models]]'
  target_id: paper:2404.03592
  confidence: high
- type: variation_of
  target: '[[representation-finetuning]]'
  target_id: method:representation-finetuning
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

Low-rank Linear Subspace ReFT learns an orthonormal low-rank projection and a
linear projected source. It replaces selected components of hidden
representations while leaving the base model weights frozen.

**Why it matters here:** LoReFT shows that low-rank learned interventions can
adapt generation at chosen layers and token positions with few trainable
parameters.

**Lineage:** LoReFT is an instance of [[representation-finetuning]] derived
from distributed interchange interventions and distributed alignment search.
