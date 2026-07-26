---
aliases:
- Middle Layers Share a Common Representation Space
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:middle-layers-share-representation-space
  type: mechanism
  status: canonical
cause: Position of a transformer layer in the middle portion of the layer stack, as opposed to the first or last few layers
effect: Hidden-state representations across middle layers occupy a common representation space -- evidenced by a high-cosine-similarity block in the all-layers similarity matrix -- so skipping or swapping the input source of a middle layer causes only graceful degradation, while the same treatment on outer layers is catastrophic
polarity: enables
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[residual-stream]]'
- '[[hidden-state-cosine-similarity]]'
relationships:
- type: supported_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[hidden-state-cosine-similarity]]'
  target_id: metric:hidden-state-cosine-similarity
---

For both Llama2-7B and BERT-Large, the middle layers of the transformer stack
produce hidden states with high pairwise cosine similarity, forming a
contiguous block in the all-layers similarity matrix that is visually and
numerically distinct from the first and last few layers. This shared
representation space means a middle layer's output can be substituted for
another middle layer's output, or a middle layer can be skipped outright,
with only graceful degradation in downstream benchmark performance --
whereas performing the same skip or swap on one of the first or last few
layers collapses performance toward random-baseline.

**Why it matters here:** This is the paper's central mechanism: it reframes
"depth" in a frozen pretrained transformer as three functionally distinct
regions (specialist beginning, interchangeable middle, specialist end) rather
than a uniform stack, and it is the finding that motivates every downstream
intervention (skipping, weight sharing, reordering, parallel execution)
tested in arXiv:2407.09298.
