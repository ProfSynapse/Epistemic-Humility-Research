---
aliases:
- ViT
- Vision Transformer
tags:
- kg/method
- concept
- method
kg:
  id: method:vision-transformer
  type: method
  status: canonical
area: methods
related:
- '[[2103.17239--going-deeper-image-transformers]]'
relationships:
- type: used_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
---

Vision Transformer (ViT) applies the standard transformer encoder, alternating
self-attention and feed-forward blocks over a sequence of flattened image
patches plus a prepended class token, directly to image classification instead
of using convolutions.

**Why it matters here:** ViT is the base architecture that
[[data-efficient-image-transformer]] and [[class-attention-in-image-transformers]]
build on; its practice of inserting and jointly updating a class token from
layer 0 is the readout design that [[class-attention-layers]] is proposed as
an improvement over, and its plain residual-block structure is what
[[layerscale]] is shown to stabilize at greater depth.

**Lineage:** the foundational patch-sequence transformer architecture for
image classification; [[data-efficient-image-transformer]] and
[[class-attention-in-image-transformers]] are later architectural refinements.
