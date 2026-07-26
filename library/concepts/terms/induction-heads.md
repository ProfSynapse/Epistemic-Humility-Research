---
aliases:
- Induction Heads
- induction head
tags:
- kg/term
- concept
- term
kg:
  id: term:induction-heads
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[entropy-neurons]]'
relationships:
- type: studied_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[entropy-neurons]]'
  target_id: term:entropy-neurons
  confidence: high
---

Induction heads are attention heads that implement the pattern "if token B
followed token A earlier in context, and the current token is A, predict B
again," letting a model detect and continue repeated subsequences. They are a
canonical in-context-learning circuit identified in mechanistic-interpretability
work on small transformers.

**Why it matters here:** In Stolfo et al.'s induction case study, the top
induction heads in GPT-2 Small (L5H1, L5H5, L6H9) drive the activation of a
specific [[entropy-neurons|entropy neuron]] during repeated sequences; BOS-ablating
those heads substantially reduces the neuron's activation, giving a causal link
from induction-head activity to the entropy-regulation mechanism.

**Lineage:** no formal derivation edges recorded in this vault yet.
