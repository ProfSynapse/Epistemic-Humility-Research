---
aliases:
- Unembedding Null Space
- effective null space of the unembedding matrix
tags:
- kg/term
- concept
- term
kg:
  id: term:unembedding-null-space
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[unembedding-matrix]]'
- '[[entropy-neurons]]'
relationships:
- type: proposed_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[unembedding-matrix]]'
  target_id: term:unembedding-matrix
  confidence: high
- type: related_to
  target: '[[entropy-neurons]]'
  target_id: term:entropy-neurons
  confidence: high
---

The unembedding null space is an effective low-rank subspace of the
[[unembedding-matrix]] where writing residual-stream mass produces almost no
direct change to the logits, evidenced empirically by a sharp singular-value
drop in the unembedding matrix (e.g. around index ~755 of 768 in GPT-2 Small).

**Why it matters here:** Stolfo et al. show entropy neurons write their output
weights almost exclusively into this null space, which is precisely what lets
them increase residual-stream norm (and so shrink the final LayerNorm scale)
while leaving individual logits nearly unchanged. The fraction of a neuron's
output norm projected into the null space predicts the size of its
LayerNorm-mediated effect on entropy.

**Lineage:** introduced by this paper as the geometric explanation for how
entropy neurons achieve a norm-only effect.
