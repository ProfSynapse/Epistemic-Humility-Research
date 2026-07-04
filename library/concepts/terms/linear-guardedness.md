---
aliases:
- linearly guarded
- guarded representation
- linear guarding
- linear concept erasure guarantee
tags:
- kg/term
- concept
- term
kg:
  id: term:linear-guardedness
  type: term
  status: canonical
area: fairness
related:
- '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
relationships:
- type: proposed_by
  target: '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
  target_id: paper:2004.07667
  confidence: high
---

Linear guardedness is a formal property of a set of representation vectors X with respect to a discrete attribute Z: X is linearly guarded for Z if no linear classifier can predict Z from X at better than majority-class accuracy. The definition formalises the erasure target: a transformation g achieves linear guardedness when the maximum linear predictability of Z from g(X) collapses to chance. INLP, RLACE, and LEACE all aim at this property, but differ in how many dimensions they remove and how much residual distortion they introduce in the process.

**Why it matters here:** Linear guardedness is the formal criterion used to evaluate concept-erasure success and to distinguish methods that achieve the minimum-rank solution from those that over-erase.

**Lineage:** operationalised in [[inlp]] and sharpened into a closed-form guarantee by [[rlace]] and [[leace]].
