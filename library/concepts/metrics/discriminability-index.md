---
aliases:
- discriminability index
- d-prime
- d'
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:discriminability-index
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

The discriminability index (d') is a signal-detection-theory statistic that
quantifies how well two distributions are separated relative to their spread:
the difference between their means divided by a pooled measure of their
standard deviations. Applied to activations, it measures how cleanly positive
and negative examples separate when projected onto a chosen axis (e.g. the
difference-of-means line used to build a steering vector).

**Why it matters here:** [[2505.22637--understanding-un-reliability-steering-vectors-language-models]]
uses d' along the difference-of-means line as a second, correlated predictor of
[[steerability]]: datasets with tight, well-separated positive/negative
activation clusters (high d') are more steerable than datasets with
overlapping, high-variance activations (low d').

**Lineage:** a standard signal-detection statistic, not proposed by any one
paper; applied to activation geometry by
[[2505.22637--understanding-un-reliability-steering-vectors-language-models]]
alongside [[cosine-similarity]]-based directional agreement.
