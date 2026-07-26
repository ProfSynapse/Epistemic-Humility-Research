---
aliases:
- Outer-Layer Skipping Is More Catastrophic Than Middle-Layer Skipping
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:outer-layer-skipping-more-catastrophic-than-middle
  type: mechanism
  status: canonical
cause: Skipping (bypassing) a layer located among the first or last few layers of a frozen pretrained transformer, versus skipping a layer in the middle block
effect: Benchmark accuracy collapses toward random-baseline performance when outer layers are skipped, while skipping middle layers -- even several at once -- causes only graceful degradation
polarity: increases
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[layer-skipping]]'
- '[[middle-layers-share-representation-space]]'
relationships:
- type: supported_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[layer-skipping]]'
  target_id: method:layer-skipping
- type: related_to
  target: '[[middle-layers-share-representation-space]]'
  target_id: mechanism:middle-layers-share-representation-space
---

Skipping any single one of the first or last few layers of a frozen
pretrained transformer is catastrophic to downstream benchmark performance,
driving accuracy toward random-baseline levels. Skipping middle layers,
including multiple middle layers simultaneously, produces only graceful,
proportionate degradation. This asymmetry holds uniformly across Llama2-7B,
Llama2-13B, Llama2-70B, and BERT-Large, indicating the beginning and end of
the layer stack perform specialized, non-substitutable computation while the
middle block does not.

**Why it matters here:** This is the direct behavioral consequence of
[[middle-layers-share-representation-space]]: it is the skip-tolerance
pattern, replicated across model scales, that establishes the beginning/
middle/ending block structure the layers-as-painters analogy is built on.
