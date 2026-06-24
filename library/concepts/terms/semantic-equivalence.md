---
aliases:
- meaning equivalence
- semantic invariance
- shared meaning
tags:
- kg/term
- concept
- term
kg:
  id: term:semantic-equivalence
  type: term
  status: canonical
area: terms
related:
- '[[2302.09664--semantic-uncertainty-kuhn]]'
- '[[semantic-entropy]]'
- '[[bidirectional-entailment-clustering]]'
- '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
- '[[aleatoric-uncertainty]]'
relationships:
- type: proposed_by
  target: '[[2302.09664--semantic-uncertainty-kuhn]]'
  target_id: paper:2302.09664
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[bidirectional-entailment-clustering]]'
  target_id: method:bidirectional-entailment-clustering
  confidence: medium
- type: related_to
  target: '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
  target_id: mechanism:lexical-entropy-overestimates-uncertainty-under-paraphrase
  confidence: medium
- type: related_to
  target: '[[aleatoric-uncertainty]]'
  target_id: term:aleatoric-uncertainty
  confidence: medium
---

The property that two distinct token sequences express the same meaning or semantic content. Formally defined as a reflexive, symmetric, and transitive equivalence relation on text sequences. Linguists distinguish semantic equivalence from syntactic equivalence (same grammatical form) and lexical equivalence (same tokens); semantic equivalence is the most permissive and the level that matters for most NLG applications.

**Why it matters here:** The root cause of lexical entropy inflation in NLG uncertainty estimation. Standard entropy treats semantically equivalent paraphrases as distinct outcomes, overstating uncertainty on questions where the model confidently generates one meaning in many forms.

**Lineage:** Classical concept in linguistics and NLP. Operationalized for NLG uncertainty by Kuhn, Gal, and Farquhar (arXiv:2302.09664) via bidirectional entailment clustering.
