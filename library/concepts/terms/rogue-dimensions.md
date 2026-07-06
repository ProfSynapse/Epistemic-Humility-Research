---
aliases:
- rogue dimensions
- outlier dimensions
- representation anisotropy
tags:
- kg/term
- concept
- term
kg:
  id: term:rogue-dimensions
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2109.04404--all-bark-no-bite-rogue-dimensions-transformer]]'
- '[[massive-activations]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2109.04404--all-bark-no-bite-rogue-dimensions-transformer]]'
  target_id: paper:2109.04404
  confidence: high
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: medium
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Rogue dimensions are a small subset, often one to three and at most five, of
embedding dimensions centered far from the origin with disproportionately high
variance, which dominate any cosine or Euclidean similarity while contributing
little to model behavior. Timkey and van Schijndel show that in some layers a
single dimension supplies over 99% of expected cosine similarity, that removing
the top one to five dimensions collapses the explained variance of the
similarity measure (r-squared near zero), and that these dimensions correlate
with position and delimiter tokens rather than semantic content. They are the
source of representation anisotropy and are neutralized by per-dimension
standardization.

**Why it matters here:** rogue dimensions are the reason a raw cosine or
covariance over the census residual can be degenerate. If standardizing the
residual per dimension changes the picture, a few outlier axes were driving the
metric; report standardized geometry, not raw.

**Lineage:** the embedding-similarity manifestation of outlier coordinates,
closely related to but distinct from [[massive-activations]] (scalar at few
tokens versus a dimension large across most tokens); both live as persistent
large coordinates in the [[residual-stream]].
