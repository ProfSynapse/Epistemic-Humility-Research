---
aliases:
- Class-attention layers improve classification readout
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:class-attention-layers-improve-class-embedding-readout
  type: mechanism
  status: canonical
cause: "Reading patch-embedding content into the class embedding through dedicated class-attention layers late in the network, instead of jointly updating a class token with patch embeddings from layer 0."
effect: "Top-1 classification accuracy improves at matched depth and parameter budget over the joint class-token approach used by ViT and DeiT."
polarity: increases
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[class-attention-layers]]'
- '[[vision-transformer]]'
- '[[data-efficient-image-transformer]]'
relationships:
- type: supported_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: related_to
  target: '[[class-attention-layers]]'
  target_id: method:class-attention-layers
  confidence: high
- type: related_to
  target: '[[vision-transformer]]'
  target_id: method:vision-transformer
  confidence: medium
- type: related_to
  target: '[[data-efficient-image-transformer]]'
  target_id: method:data-efficient-image-transformer
  confidence: medium
---

Separating the class embedding's readout role from the patch embeddings'
representation-building role, and only letting the class embedding attend
into the patch stream (not the reverse) in a small number of late layers,
gives a better classification signal than [[vision-transformer]]'s and
[[data-efficient-image-transformer]]'s practice of mixing the class token into
patch updates from the first layer onward.
