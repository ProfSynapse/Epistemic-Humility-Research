---
aliases:
- position-context decomposition
- positional basis
- positional spiral
- mean decomposition of hidden states
tags:
- kg/method
- concept
- method
kg:
  id: method:position-context-decomposition
  type: method
  status: canonical
area: methods
related:
- '[[2310.04861--uncovering-hidden-geometry-transformers-disentangling-position-context]]'
- '[[residual-stream]]'
- '[[intrinsic-dimension]]'
relationships:
- type: proposed_by
  target: '[[2310.04861--uncovering-hidden-geometry-transformers-disentangling-position-context]]'
  target_id: paper:2310.04861
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
- type: related_to
  target: '[[intrinsic-dimension]]'
  target_id: metric:intrinsic-dimension
  confidence: low
---

The position-context decomposition splits every transformer hidden state into a
global mean, a positional mean, a context mean, and a residual, framed as a
two-way ANOVA with position and context as factors. Song and Zhong find the
positional basis is low-rank (estimated rank 8 to 12 out of hundreds to
thousands of dimensions) and low-frequency, tracing a continuous spiral across
layers; the context basis clusters by document topic; and the two are nearly
orthogonal, so they can be estimated and subtracted independently. The residual
is what remains after this structural bookkeeping is removed.

**Why it matters here:** this is the direct methodological precedent for our
census. It says a large fraction of raw hidden-state displacement is boring
structure: a global-mean offset (anisotropy, norms that grow more than
100-fold across layers), a smooth positional component monotone or spiral in
token index, and a per-context topic offset. A census that skips this
subtraction will mistake mean-drift plus positional smoothness plus topic offset
for signal; only the leftover residual is candidate dark structure.

**Lineage:** an ANOVA-style mean subtraction on the [[residual-stream]]; the
subtract-known-structure-then-characterize-the-remainder move that the
displacement census generalizes; the residual's effective
[[intrinsic-dimension]] is the natural follow-on measurement.
