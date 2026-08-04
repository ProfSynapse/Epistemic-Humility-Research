---
aliases:
- Angular Distance
- normalized angular distance
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:angular-distance
  type: metric
  status: canonical
area: metrics
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[layer-pruning]]'
- '[[residual-stream]]'
relationships:
- type: measured_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: related_to
  target: '[[layer-pruning]]'
  target_id: method:layer-pruning
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Angular distance is a normalized dissimilarity between two residual-stream
hidden-state vectors, computed as the arccosine of their cosine similarity
divided by pi: d(x, y) = arccos(x . y / (|x||y|)) / pi. Unlike raw cosine
similarity it behaves as a proper metric (satisfies the triangle inequality),
which makes it suitable for ranking candidate layer blocks by how little
their input and output states differ.

**Why it matters here:** The core selection criterion for [[layer-pruning]]:
for each candidate block size, the paper computes the angular distance
between the hidden state entering the block and the hidden state leaving it
across a sample of tokens, and prunes the block whose endpoints are most
similar (lowest angular distance), on the assumption that such a block is
doing the least computational work.

**Lineage:** reported in arXiv:2403.17887 (Figure 4, Figure 5) as the
layer-similarity heatmap that drives block selection across all seven
evaluated models.
