---
aliases:
- Universal Dependencies
- UD POS
- English Universal Dependencies
- English Universal Dependencies (POS tags)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:universal-dependencies-pos
  type: dataset
  status: canonical
area: NLP
related: []
relationships: []
---

Universal Dependencies (UD) is a cross-lingual treebank framework that provides
sentences annotated with coarse part-of-speech tags (18 universal categories such
as NOUN, VERB, ADJ). In concept-erasure experiments (LEACE), the English UD
subset is used to fit erasure projections that remove POS information from
transformer hidden states, and then to evaluate whether the erased representations
still carry decodable POS signal or degrade language-model perplexity.

**Why it matters here:** POS scrubbing serves as a reference task for assessing
the distortion cost of linear concept erasure: if removing a low-level syntactic
property raises perplexity sharply, that cost establishes an upper bound on how
much signal one can safely erase from representations, which is directly relevant
to efforts that aim to erase epistemic-uncertainty axes without collateral damage.

**Lineage:** no atom-level predecessors.
