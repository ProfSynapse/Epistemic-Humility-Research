---
aliases:
- bias subspace hypothesis
- linear concept subspace
tags:
- kg/term
- concept
- term
kg:
  id: term:linear-bias-subspace-hypothesis
  type: term
  status: canonical
area: interpretability
related:
- '[[inlp]]'
- '[[rlace]]'
- '[[leace]]'
- '[[linear-concept-erasure]]'
relationships:
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
- type: related_to
  target: '[[rlace]]'
  target_id: method:rlace
- type: related_to
  target: '[[leace]]'
  target_id: method:leace
- type: related_to
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
---

The linear bias subspace hypothesis (Bolukbasi et al. 2016; Vargas and Cotterell
2020) states that all concept or demographic information present in an embedding
is contained within a low-dimensional linear subspace B, so that projecting
representations onto the orthogonal complement of B is sufficient to remove that
information. RLACE operationalises this as a maximin game: the solution finds the
minimal such subspace whose removal provably blocks any linear classifier, and
LEACE produces the unique distortion-minimising projection onto that subspace's
complement.

**Why it matters here:** The hypothesis is the geometric precondition for all
linear-erasure probing methods; if concept information does not lie in a linear
subspace, methods like [[inlp]], [[rlace]], and [[leace]] would be incomplete
even in theory, which has direct implications for whether erasing one epistemic
axis (such as doubt) can be done without corrupting others.

**Lineage:** foundational assumption underlying [[inlp]], [[rlace]], and
[[leace]]; tested empirically by [[linear-erasure-ineffective-against-nonlinear-classifiers]].
