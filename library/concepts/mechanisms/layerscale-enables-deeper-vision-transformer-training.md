---
aliases:
- LayerScale stabilizes deep transformer training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layerscale-enables-deeper-vision-transformer-training
  type: mechanism
  status: canonical
cause: "Applying LayerScale (a per-channel learnable diagonal scaling on each residual-block output, initialized near zero) to an image transformer."
effect: "Training stabilizes and top-1 accuracy improves monotonically with depth, whereas the unmodified baseline fails to converge at 24 and 36 layers."
polarity: enables
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[layerscale]]'
- '[[data-efficient-image-transformer]]'
relationships:
- type: supported_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: related_to
  target: '[[layerscale]]'
  target_id: method:layerscale
  confidence: high
- type: related_to
  target: '[[data-efficient-image-transformer]]'
  target_id: method:data-efficient-image-transformer
  confidence: medium
---

Deep image transformers built on the [[data-efficient-image-transformer]]
recipe become progressively harder to optimize with depth and fail to
converge past roughly 24 layers. Adding [[layerscale]] fixes this: with it,
accuracy keeps improving as layers are added instead of saturating or
collapsing.
