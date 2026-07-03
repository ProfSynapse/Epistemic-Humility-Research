---
aliases:
- co-occurrence frequency
- co-occurrence count
- pretraining co-occurrence
- Subject-Object Co-occurrence Frequency
tags:
- kg/term
- concept
- term
kg:
  id: term:subject-object-co-occurrence-frequency
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[pretraining-co-occurrence-threshold]]'
- '[[lre-based-frequency-estimation]]'
relationships:
- type: related_to
  target: '[[pretraining-co-occurrence-threshold]]'
  target_id: term:pretraining-co-occurrence-threshold
- type: related_to
  target: '[[lre-based-frequency-estimation]]'
  target_id: method:lre-based-frequency-estimation
---

Subject-object co-occurrence frequency is the count of how many times a subject token and the corresponding object token from a factual relation triplet appear together within the same pretraining sequence across the training corpus. It is measured using corpus-search tools such as WIMBD or a custom Batch Search API over corpora such as OLMo's Dolma or GPT-J's Pile. The measure operationalizes "how well did the model see this fact" at the level of text co-occurrence rather than document-level counting.

**Why it matters here:** Pretraining co-occurrence frequency is a primary driver of whether a model has reliably encoded a fact: facts below the linearity threshold tend to be recalled unreliably, so this term anchors the empirical grounding of the knowledge boundary concept central to epistemic humility.

**Lineage:** foundational input to [[pretraining-co-occurrence-threshold]] and the regression target for [[lre-based-frequency-estimation]].
