---
aliases:
- Middle-Layer Weight Sharing Collapses Performance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:middle-layer-weight-sharing-collapses-performance
  type: mechanism
  status: canonical
cause: Replacing a span of a frozen pretrained transformer's middle layers with repeated copies of a single center layer's weights (the Middle Repeat intervention)
effect: Benchmark accuracy degrades toward random-baseline performance far faster than simply skipping the same layers, making Middle Repeat the single most catastrophic intervention tested
polarity: decreases
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[middle-layer-repeat]]'
- '[[middle-layers-share-representation-space]]'
relationships:
- type: supported_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[middle-layer-repeat]]'
  target_id: method:middle-layer-repeat
- type: related_to
  target: '[[middle-layers-share-representation-space]]'
  target_id: mechanism:middle-layers-share-representation-space
---

Even though middle layers share a common representation space and tolerate
being skipped, they are not functionally redundant copies of one another:
forcing a span of middle layers to all execute the single center layer's
weights (Middle Repeat) degrades benchmark performance to random-baseline
levels far more quickly, as a function of span length, than skipping the
same span entirely. This holds for both Llama2-7B and BERT-Large.

**Why it matters here:** This mechanism is the necessary qualifier on
[[middle-layers-share-representation-space]]: shared representation space
supports substitutability and graceful omission, but it does not imply the
layers compute the same function. Weight sharing actively corrupts the
computation in a way that dropping it entirely does not, ruling out a naive
"the middle layers are all doing the same thing" reading of the skip-
tolerance results.
