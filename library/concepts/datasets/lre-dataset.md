---
aliases:
- Linear Relation Extraction dataset
- LRE
- Hernandez LRE
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:lre-dataset
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[linear-relation-embedding]]'
- '[[factual-recall-localization]]'
- '[[pararel]]'
relationships:
- type: related_to
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
- type: related_to
  target: '[[pararel]]'
  target_id: dataset:pararel
---

The LRE dataset (Hernandez et al.) is a factual-recall benchmark covering
linguistic, commonsense, factual, and bias knowledge types as subject-relation-object
triples, designed to probe what relational knowledge is stored in LLM parameters
under zero-shot conditions. Each triple encodes a single fact retrievable by
completing a short natural-language prompt, and the dataset is stratified across
diverse relation types to test generalization beyond narrow factual domains.
The benchmark is used to evaluate linear relation embedding (LRE) methods and
to audit where and how relational knowledge is encoded in model weights.

**Why it matters here:** Understanding which model components encode specific
relational facts helps diagnose why models hallucinate or abstain incorrectly,
directly informing mechanistic accounts of the knowledge boundary.

**Lineage:** related to [[linear-relation-embedding]] (the method the dataset
primarily evaluates), [[factual-recall-localization]] (the broader task framing),
and [[pararel]] (a parallel paraphrase benchmark covering overlapping factual
triples).
