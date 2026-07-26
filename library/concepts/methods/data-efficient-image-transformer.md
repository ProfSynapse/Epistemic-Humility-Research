---
aliases:
- DeiT
- Data-efficient Image Transformer
tags:
- kg/method
- concept
- method
kg:
  id: method:data-efficient-image-transformer
  type: method
  status: canonical
area: methods
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[vision-transformer]]'
relationships:
- type: used_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: derived_from
  target: '[[vision-transformer]]'
  target_id: method:vision-transformer
  confidence: high
---

DeiT (Data-efficient Image Transformer) trains [[vision-transformer]]-style
architectures to competitive accuracy on ImageNet-1k alone, without the
hundreds of millions of extra pre-training images the original ViT required,
using a strong data-augmentation and regularization recipe plus a distillation
token trained against a convolutional teacher.

**Why it matters here:** the CaiT architecture in
[[class-attention-in-image-transformers]] is built directly on the DeiT
training recipe and hyperparameters; the DeiT-S baseline (79.9% top-1 at 12
layers) is the reference point the paper's class-attention and LayerScale
ablations are measured against, and DeiT is also the baseline shown to fail to
converge at 24-36 layers without [[layerscale]].

**Lineage:** derives from [[vision-transformer]]; used as the training-recipe
and baseline-architecture foundation for [[class-attention-in-image-transformers]].
