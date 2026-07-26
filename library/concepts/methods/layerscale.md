---
aliases:
- LayerScale
tags:
- kg/method
- concept
- method
kg:
  id: method:layerscale
  type: method
  status: canonical
area: methods
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[vision-transformer]]'
relationships:
- type: proposed_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: related_to
  target: '[[vision-transformer]]'
  target_id: method:vision-transformer
  confidence: medium
---

LayerScale adds a per-channel learnable diagonal scaling to the output of each
residual block (attention and FFN branches) in a transformer, with the scaling
values initialized close to zero. It is a lightweight architectural change,
just an extra elementwise multiply per residual branch, that lets gradients
flow more conservatively through early training so deeper networks stay
trainable.

**Why it matters here:** LayerScale is the single change that unlocks stable
training of very deep image transformers (up to 36+ layers); without it, deep
[[data-efficient-image-transformer]]-style models fail to converge. It is one
of the two architectural pieces (with [[class-attention-layers]]) that compose
into [[class-attention-in-image-transformers]].

**Lineage:** developed as a fix for the optimization instability of deep
[[vision-transformer]]-style architectures; contrasted in the introducing paper
against ReZero, Fixup, and T-Fixup as alternative residual-scaling schemes.
