---
aliases:
- WEAT
- Word Embedding Association Test (WEAT)
- word embedding association test
- Word Embedding Association Test
- WEAT's d
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:weat
  type: metric
  status: canonical
area: fairness
related:
- '[[glove-word-embeddings]]'
relationships:
- type: related_to
  target: '[[glove-word-embeddings]]'
  target_id: model:glove-word-embeddings
---

The Word Embedding Association Test (Islam et al. 2016) quantifies stereotypical bias in static word embeddings by measuring the association between two sets of target words (e.g., career vs. family words) and two sets of attribute words (e.g., male vs. female names) using cosine-similarity effect size d. A positive d indicates the first target set is more associated with the first attribute set; d near zero indicates balanced association. Lower absolute WEAT d values after erasure indicate that the debiasing transformation has successfully reduced stereotypical geometric associations.

**Why it matters here:** WEAT provides an intrinsic, interpretable signal for whether gender structure has been removed from [[glove-word-embeddings]], complementing the extrinsic [[tpr-gap]] measured on downstream classifiers.

**Lineage:** applied to [[glove-word-embeddings]] to evaluate [[inlp]] and [[rlace]] in the concept-erasure literature.
