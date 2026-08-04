---
aliases:
- cosine similarity
- directional agreement
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:cosine-similarity
  type: metric
  status: canonical
area: metrics
related:
- '[[2505.22637--understanding-un-reliability-steering-vectors-language-models]]'
- '[[steering-vector]]'
relationships:
- type: measured_by
  target: '[[2505.22637--understanding-un-reliability-steering-vectors-language-models]]'
  target_id: paper:2505.22637
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Cosine similarity is the normalized dot product between two vectors, used
throughout the steering-vector literature both to compare steering vectors
produced under different conditions and to measure how tightly a set of
per-sample activation differences agree with each other (or with their mean).
A value near 1 indicates near-identical direction; a value near 0 indicates
near-orthogonality; a value near -1 indicates opposition.

**Why it matters here:** used two ways in the steering literature captured by
this library: (1) as a cross-condition comparison metric (e.g. do steering
vectors built from different prompt types point the same way), and (2) as a
within-dataset agreement metric (do individual samples' activation differences
point the same way as the aggregate steering vector). The second usage is what
predicts per-dataset steerability.

**Lineage:** a generic linear-algebra quantity, not proposed by any one paper;
[[2505.22637--understanding-un-reliability-steering-vectors-language-models]]
uses it both to report pairwise steering-vector similarity across prompt types
and to show that higher average cosine similarity between per-sample
activation differences and the aggregate steering vector predicts higher
steerability.
