---
aliases:
- CKA value can be forced high or low without changing model behavior
- linear CKA is sensitive to functionality-preserving transformations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:cka-similarity-manipulable-without-functional-change
  type: mechanism
  status: canonical
cause: "Translating a subset of a set of representations along an arbitrary direction while leaving the rest fixed (Theorem 1), including the special cases of moving a single outlier point (Corollary 3) or moving one linearly-separable class in a direction that preserves the separating hyperplane and margins (Corollary 4); separately, directly optimizing a trained network's layer-by-layer CKA map toward an arbitrary target map via a joint distillation-plus-CKA-map loss while penalizing accuracy drift."
effect: "Linear (and empirically also RBF) CKA between the original and transformed representations drops toward 0 even though local structure, linear separability, and margins are fully preserved by construction; a single translated outlier point among tens of thousands can by itself crash the CKA value. Conversely, explicit CKA-map optimization on a CIFAR-10 ResNet can force near-identical CKA similarity between the first and last layer, or across all layers, or drive an arbitrary comical target map, while accuracy moves by at most about 1.5 points (baseline 85.9% vs. 84.3-85.5% across the three manipulated linear/RBF maps); early layers of a task-generalizing, a label-memorizing, and a randomly initialized network also report mutually high CKA despite having visibly different, unequally useful convolution filters. A raw CKA number therefore does not, on its own, distinguish genuine representational overlap from an artifact of these transformations."
polarity: complicates
related:
- '[[2210.16156--reliability-cka-as-similarity-measure-deep-learning]]'
- '[[centered-kernel-alignment]]'
relationships:
- type: supported_by
  target: '[[2210.16156--reliability-cka-as-similarity-measure-deep-learning]]'
  target_id: paper:2210.16156
  confidence: high
  evidence:
  - Theorem 1, Corollary 3, Corollary 4 (Sec. 3); Figure 4 (subset-translation
    and outlier sensitivity experiments, Sec. 4.2); Figures 5-7 (explicit CKA-map
    optimization, Sec. 4.3); Figure 2 (early-layer high-CKA/dissimilar-features
    result, Sec. 4.1)
- type: related_to
  target: '[[centered-kernel-alignment]]'
  target_id: method:centered-kernel-alignment
  confidence: high
---

Linear CKA's own invariances (to orthogonal transformations and isotropic scaling) do not extend to a much larger class of simple, functionality-preserving transformations: subset translation can be shown analytically to drive the CKA value toward zero regardless of whether the transformation changes what the network computes, and the same manipulability runs in the opposite direction too, since a network's CKA map can be optimized to match almost any target while barely moving its accuracy.

**Why it matters here:** any subspace-overlap estimator that reports a raw similarity score (CKA or otherwise) needs a reliability check beyond the score itself, because this paper shows both false negatives (low similarity despite behavior-preserving structure) and false positives (high similarity between representations with visibly different, unequally useful features) are achievable without any change in what the underlying model computes. A disjoint-split reliability check and a permutation-null baseline are the direct countermeasure: they establish what similarity value the estimator returns for representations known to be unrelated or known to be identical up to the transformations this paper characterizes, so an observed value can be judged against that null rather than trusted at face value.

**Lineage:** characterizes [[centered-kernel-alignment]], the linear-CKA similarity measure introduced by Kornblith et al. (2019, not yet in this vault); the outlier-sensitivity and block-structure results it revisits were first observed empirically in Ding et al. (2021) and Nguyen et al. (2021; 2022), also not yet in this vault.
