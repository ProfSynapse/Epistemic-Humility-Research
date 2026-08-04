---
aliases:
- LayerScale uniformizes residual branch updates
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layerscale-uniformizes-residual-branch-contribution
  type: mechanism
  status: canonical
cause: "LayerScale's near-zero-initialized, per-channel learnable diagonal scaling of each residual branch's (attention and FFN) output."
effect: "The magnitude of each residual branch's contribution to the network's output becomes more uniform across depth and channels, instead of a subset of branches dominating updates early in training."
polarity: increases
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[layerscale]]'
relationships:
- type: supported_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: related_to
  target: '[[layerscale]]'
  target_id: method:layerscale
  confidence: high
---

Without LayerScale, a small number of residual branches can dominate the
update at a given depth, destabilizing training as depth grows. Because
[[layerscale]] initializes each residual branch's per-channel scale near
zero and lets it grow independently during training, the branches' relative
contributions equalize, which is offered as the explanation for why deep
transformers with LayerScale train stably where unscaled ones do not.
