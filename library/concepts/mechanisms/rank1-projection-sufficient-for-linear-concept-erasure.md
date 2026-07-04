---
aliases:
- Rank-1 projection suffices to fully erase a linearly-encoded concept
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rank1-projection-sufficient-for-linear-concept-erasure
  type: mechanism
  status: canonical
cause: Applying a rank-1 orthogonal projection (removing a single direction found by [[rlace]]) to GloVe or BERT representations
effect: Any linear classifier's gender-prediction accuracy drops to majority-class chance (~50%), fully blocking linear recovery of the concept
polarity: enables
related:
- '[[2201.12091--linear-adversarial-concept-erasure]]'
- '[[rlace]]'
- '[[linear-concept-erasure]]'
- '[[glove-word-embeddings]]'
relationships:
- type: supported_by
  target: '[[2201.12091--linear-adversarial-concept-erasure]]'
  target_id: paper:2201.12091
  confidence: high
- type: related_to
  target: '[[rlace]]'
  target_id: method:rlace
- type: related_to
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
contradicted-by: []
---

[[rlace]] finds the single worst-case direction a linear adversary exploits to predict a protected attribute, then projects it out; dropping only this rank-1 subspace from GloVe or BERT representations reduces any linear classifier's gender-prediction accuracy to chance. This is a strictly tighter erasure than [[inlp]], which requires many more projection rounds to reach the same goal. The result is proven analytically and verified empirically in arXiv:2201.12091, establishing that a single direction is both necessary and sufficient for linear concept erasure when the concept occupies a one-dimensional subspace.
