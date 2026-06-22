---
aliases:
- lm_head
- W^T projection
- tied embedding weights
tags:
- kg/term
- concept
- term
kg:
  id: term:unembedding-matrix
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[logit-lens]]'
- '[[residual-stream]]'
- '[[gpt-2]]'
relationships:
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[gpt-2]]'
  target_id: model:gpt-2
---

The unembedding matrix is the weight matrix used to project from the model's
internal hidden-state space to a vocabulary-sized logit vector, from which output
token probabilities are computed via softmax. In models such as GPT-2 this matrix
is tied to (the transpose of) the input embedding matrix, so input and output
representations share the same geometric space. Applying this matrix to
intermediate layer activations converts them into interpretable probability
distributions over the vocabulary.

**Why it matters here:** The unembedding matrix is what makes the logit lens
possible: intermediate residual-stream states can be decoded into token
distributions at any layer, revealing how the model's internal representation
evolves across depth and exposing where calibration or factual associations
crystallize.

**Lineage:** used by [[logit-lens]] to decode [[residual-stream]] states at
intermediate layers; studied in [[gpt-2]] where input and unembedding weights
are tied.
