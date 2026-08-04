---
aliases:
- ImageNet-V2
- ImageNet V2 matched frequency
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:imagenet-v2
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

ImageNet-V2 is a new test set collected to match the [[imagenet]] validation
set's class distribution and collection protocol as closely as possible, used
to measure how much a model's reported accuracy is overfit to the original
ImageNet validation images versus generalizing to a fresh sample. This paper
evaluates on the matched-frequency variant.

**Why it matters here:** the paper reports ImageNet-V2 (matched-frequency)
accuracy as a distribution-shift check for its CaiT models, and its best
model sets a new state of the art on this benchmark among no-external-data
models.

**Lineage:** an independently collected out-of-sample test set matched to the
[[imagenet]] validation distribution.
