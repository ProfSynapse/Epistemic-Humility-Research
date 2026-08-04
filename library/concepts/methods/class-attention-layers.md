---
aliases:
- Class-Attention Layers
- CA layers
tags:
- kg/method
- concept
- method
kg:
  id: method:class-attention-layers
  type: method
  status: canonical
area: methods
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[vision-transformer]]'
- '[[class-attention-in-image-transformers]]'
relationships:
- type: proposed_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: related_to
  target: '[[vision-transformer]]'
  target_id: method:vision-transformer
  confidence: medium
- type: required_by
  target: '[[class-attention-in-image-transformers]]'
  target_id: method:class-attention-in-image-transformers
  confidence: high
---

Class-attention layers separate the class embedding from the patch embeddings
for most of the network's depth, then insert a small number of dedicated
layers late in the network where the class embedding attends to (reads from)
the frozen patch embeddings, without the patch embeddings attending back or
being updated. This decouples the two jobs a class token otherwise does
jointly from layer 0: building a good patch representation, and pooling that
representation for classification.

**Why it matters here:** class-attention layers outperform [[vision-transformer]]'s
and [[data-efficient-image-transformer]]'s practice of inserting a class token
at layer 0 and jointly updating it with patch embeddings throughout the
network; they are one of the two pieces (with [[layerscale]]) composed into
[[class-attention-in-image-transformers]].

**Lineage:** a redesign of the class-token readout mechanism used in
[[vision-transformer]] and [[data-efficient-image-transformer]].
