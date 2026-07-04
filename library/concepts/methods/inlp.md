---
aliases:
- INLP
- Null It Out
- nullspace projection debiasing
- Iterative Nullspace Projection (INLP)
- nullspace projection
- iterative nullspace projection
- Iterative Nullspace Projection
- INLP (Iterative Nullspace Projection)
tags:
- kg/method
- concept
- method
kg:
  id: method:inlp
  type: method
  status: canonical
area: methods
related:
- '[[linear-concept-erasure]]'
- '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
- '[[adversarial-debiasing]]'
- '[[linear-bias-subspace-hypothesis]]'
relationships:
- type: proposed_by
  target: '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
  target_id: paper:2004.07667
  confidence: high
- type: derived_from
  target: '[[adversarial-debiasing]]'
  target_id: method:adversarial-debiasing
- type: related_to
  target: '[[linear-bias-subspace-hypothesis]]'
  target_id: term:linear-bias-subspace-hypothesis
- type: related_to
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
  confidence: high
---

Iterative Nullspace Projection (INLP) is a sequential linear concept-erasure method (Ravfogel et al. 2020) that trains a linear classifier to predict a protected attribute, projects representations onto the null space of the classifier's weight vector, and repeats for K iterations, returning a rank-(D-K) orthogonal projection matrix. Each iteration removes one direction that is predictive of the concept, accumulating a basis of erased directions. The method is shown to be optimal for partial least squares (Rayleigh quotient) objectives but sub-optimal for linear regression and logistic regression, removing more dimensions than strictly necessary.

**Why it matters here:** INLP is the principal baseline against which closed-form erasure methods (RLACE, LEACE) are compared; understanding where it over-erases relative to the minimum rank needed for linear guardedness is central to the paper's contribution.

**Lineage:** derived from [[adversarial-debiasing]]; related to [[linear-bias-subspace-hypothesis]]; superseded in efficiency and distortion by [[rlace]] and [[leace]].
