---
aliases:
- ImageNet-ReaL
- ImageNet with Reassessed Labels
- ReaL
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:imagenet-real
  type: dataset
  status: canonical
area: datasets
related:
- '[[2103.17239--going-deeper-image-transformers]]'
- '[[imagenet]]'
relationships:
- type: evaluation_set_for
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
- type: derived_from
  target: '[[imagenet]]'
  target_id: dataset:imagenet
  confidence: high
---

ImageNet-ReaL (Reassessed Labels) re-annotates the [[imagenet]] validation set
with a more careful, multi-label labeling procedure, correcting the original
single-label annotations and giving a cleaner estimate of a model's true
top-1 accuracy on the same 50,000 images.

**Why it matters here:** the paper reports ImageNet-ReaL accuracy alongside
standard ImageNet-1k accuracy as an additional generalization check for its
CaiT models, and its best model sets a new state of the art on this benchmark
among no-external-data models.

**Lineage:** a relabeled evaluation split of the [[imagenet]] validation set.
