---
aliases:
- CKA
- linear CKA
- Centered Kernel Alignment
tags:
- kg/method
- concept
- method
kg:
  id: method:centered-kernel-alignment
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2210.16156--reliability-cka-as-similarity-measure-deep-learning]]'
- '[[cka-similarity-manipulable-without-functional-change]]'
relationships:
- type: related_to
  target: '[[2210.16156--reliability-cka-as-similarity-measure-deep-learning]]'
  target_id: paper:2210.16156
  confidence: high
- type: related_to
  target: '[[cka-similarity-manipulable-without-functional-change]]'
  target_id: mechanism:cka-similarity-manipulable-without-functional-change
  confidence: high
---

Centered Kernel Alignment (CKA) is a scalar representation-similarity measure between two sets of neural activations X and Y, computed as the normalized Hilbert-Schmidt Independence Criterion between their (typically linear) kernel matrices: CKA(K, L) = HSIC(K, L) / sqrt(HSIC(K, K) HSIC(L, L)). It is invariant to orthogonal transformations (rotation, permutation, reflection) and isotropic scaling, and returns a value in [0, 1] intended to summarize how similar two layers, models, or checkpoints are.

**Why it matters here:** CKA is the default off-the-shelf tool a correctness-subspace-overlap estimator might reach for, but Kornblith et al.'s original invariance guarantees do not imply the measure is reliable outside those invariances; the atom it is reused across is [[cka-similarity-manipulable-without-functional-change]], which characterizes exactly where linear CKA breaks down.

**Lineage:** introduced by Kornblith et al. (2019), not yet ingested into this vault; its reliability is characterized in [[2210.16156--reliability-cka-as-similarity-measure-deep-learning]].
