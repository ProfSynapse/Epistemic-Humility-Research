---
aliases:
- entity recognition direction
- knowledge-awareness direction
- entity-recognition latent
- entity-knowledge direction
tags:
- kg/term
- concept
- term
kg:
  id: term:entity-recognition-direction
  type: term
  status: canonical
area: terms
related:
- '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
- '[[known-unknown-direction]]'
- '[[self-knowledge]]'
- '[[sparse-autoencoder]]'
- '[[knowledge-boundary]]'
- '[[refusal-direction]]'
relationships:
- type: proposed_by
  target: '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
  target_id: paper:2411.14257
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
---

An entity-recognition direction is a linear direction in a language model's
representation space, recovered by sparse autoencoders, that fires according to
whether the model recognizes a queried entity as one it can recall facts about
(a "known" entity) versus one it cannot (an "unknown" entity). Ferrando et al.
read these directions as a form of self-knowledge: an internal representation of
the model's own knowledge boundary, separate from the truth-value of any stated
proposition. The directions generalize across entity types (players, films,
songs, cities) rather than being entity-specific.

**Why it matters here:** This is the closest prior precedent for the project's
own [[known-unknown-direction]] and for the H_monitor hypothesis. It establishes
that a knowledge-conditioned "do I know this?" signal exists as a low-dimensional
linear/attention-localized direction that can be both read (uncertainty monitor)
and steered (abstention dial), rather than a truth-of-statement direction in the
CCS / geometry-of-truth family.

**Lineage:** Recovered with [[sparse-autoencoder]] feature directions; conceptually
a knowledge-boundary signal, distinct from the statement [[truth-direction]] and
from the safety [[refusal-direction]] it downstream-controls.
