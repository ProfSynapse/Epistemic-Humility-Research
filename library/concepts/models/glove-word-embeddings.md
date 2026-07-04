---
aliases:
- GloVe
- Global Vectors for Word Representation
- GloVe Word Embeddings
- glove embeddings
tags:
- kg/model
- concept
- model
kg:
  id: model:glove-word-embeddings
  type: model
  status: canonical
area: representations
related:
- '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
- '[[2201.12091--linear-adversarial-concept-erasure]]'
relationships:
- type: related_to
  target: '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
  target_id: paper:2004.07667
- type: related_to
  target: '[[2201.12091--linear-adversarial-concept-erasure]]'
  target_id: paper:2201.12091
---

GloVe (Pennington et al. 2014) produces static word representations trained on large web-text corpora via global co-occurrence statistics, resulting in dense vectors in which geometric relationships encode semantic associations. Words can be annotated as male- or female-biased, and the effectiveness of erasure methods (INLP, RLACE) in removing linear gender-predictability is measured by post-projection classification accuracy and WEAT effect sizes. GloVe serves as an interpretable, well-understood testbed for intrinsic debiasing evaluation because gender structure is strongly linear in the embedding space.

**Why it matters here:** GloVe's known gender geometry makes it a controlled environment for confirming that erasure methods achieve linear guardedness without the confounds of a full language model.

**Lineage:** used as a probing surface alongside contextualized representations from [[gpt-2]] and BERT in the erasure literature.
