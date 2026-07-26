---
aliases:
- CaiT
- Class-Attention in Image Transformers
tags:
- kg/method
- concept
- method
kg:
  id: method:class-attention-in-image-transformers
  type: method
  status: canonical
area: methods
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[layerscale]]'
- '[[class-attention-layers]]'
- '[[data-efficient-image-transformer]]'
relationships:
- type: proposed_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: has_component
  target: '[[layerscale]]'
  target_id: method:layerscale
  confidence: high
- type: has_component
  target: '[[class-attention-layers]]'
  target_id: method:class-attention-layers
  confidence: high
- type: derived_from
  target: '[[data-efficient-image-transformer]]'
  target_id: method:data-efficient-image-transformer
  confidence: high
---

CaiT (Class-Attention in Image Transformers) is a deep image-classification
transformer architecture that composes [[layerscale]] (stabilizing residual
updates so depth can be increased) with [[class-attention-layers]] (a dedicated
late-stage readout mechanism for the class embedding), built on top of the
[[data-efficient-image-transformer]] training recipe.

**Why it matters here:** CaiT is the paper's headline result, reaching 86.5%
top-1 accuracy on ImageNet-1k with no external training data, matching prior
SOTA with fewer FLOPs and parameters, and demonstrates that both architectural
changes are needed together for deep image transformers to keep improving with
depth rather than saturating.

**Lineage:** extends [[data-efficient-image-transformer]] (which itself builds
on [[vision-transformer]]) by replacing its class-token handling with
[[class-attention-layers]] and stabilizing its residual branches with
[[layerscale]].
