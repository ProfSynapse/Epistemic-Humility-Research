---
aliases:
- mover heads
- extract head
- argument-parser head
tags:
- kg/term
- concept
- term
kg:
  id: term:mover-head
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[relation-head]]'
- '[[factual-association-recall-mechanism]]'
- '[[hallucination]]'
- '[[mover-head-failure-drives-hallucination]]'
- '[[residual-stream]]'
relationships:
- type: related_to
  target: '[[relation-head]]'
  target_id: term:relation-head
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
- type: related_to
  target: '[[mover-head-failure-drives-hallucination]]'
  target_id: mechanism:mover-head-failure-drives-hallucination
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

A mover head is an attention head in a transformer that copies or "moves"
information from the subject token position to the final prediction position in
the residual stream, surfacing the correct object token during factual-recall
queries. It operates in the upper layers of the network and is the last major
routing step before the unembedding: the head attends to the subject, extracts
the enriched subject representation, and writes it into the query position so the
MLP or unembedding can project it to a vocabulary token. Failure of the mover
head to select the correct subject representation is the proximate mechanistic
cause of factual hallucination.

**Why it matters here:** If mover heads are the proximate cause of hallucination
([[mover-head-failure-drives-hallucination]]), targeted interventions on these
heads are a high-leverage point for improving factual reliability without
wholesale retraining.

**Lineage:** works in tandem with [[relation-head]] (which supplies relational
signal to the MLP) and depends on [[factual-association-recall-mechanism]]
(the full subject-enrichment pipeline that feeds mover heads their input).
