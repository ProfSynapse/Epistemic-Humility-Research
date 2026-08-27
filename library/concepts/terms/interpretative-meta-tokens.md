---
aliases:
- interpretive meta-tokens
- meta-tokens
- ambiguity meta-tokens
tags:
- kg/term
- concept
- term
kg:
  id: term:interpretative-meta-tokens
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[jacobian-lens]]'
- '[[cognitive-space]]'
- '[[qwen3]]'
- '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
relationships:
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[cognitive-space]]'
  target_id: term:cognitive-space
  confidence: high
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: medium
- type: related_to
  target: '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
  target_id: paper:tc-2026-workspace-commentary-nanda
  confidence: high
---

Interpretative meta-tokens are high-information tokens surfaced by a [[jacobian-lens]] readout that appear to name the kind of interpretive operation a model is performing, such as asking what an ambiguous sentence means. In Nanda's Qwen replication, several Chinese tokens with meanings like "what does it mean" appeared around ambiguous poetry, puns, crossword clues, and unclear text, and negative steering on those vectors reduced context disambiguation in preliminary tests.

**Why it matters here:** these tokens are a concrete example of J-lens moving from variable interpretability toward algorithm interpretability: the readout may expose not only what content is in working memory, but which interpretive subroutine the model is preparing to run.

**Lineage:** introduced in Neel Nanda's commentary as preliminary work by Nanda, Camila Blank, and Agam Bhatia while replicating J-lens on Qwen 3.6 27B.
