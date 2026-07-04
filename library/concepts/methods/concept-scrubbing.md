---
aliases:
- layer-wise concept erasure
tags:
- kg/method
- concept
- method
kg:
  id: method:concept-scrubbing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
- '[[leace]]'
- '[[linear-guardedness]]'
- '[[amnesic-probing]]'
relationships:
- type: proposed_by
  target: '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
  target_id: paper:2306.03819
  confidence: high
- type: derived_from
  target: '[[leace]]'
  target_id: method:leace
- type: related_to
  target: '[[linear-guardedness]]'
  target_id: term:linear-guardedness
- type: related_to
  target: '[[amnesic-probing]]'
  target_id: method:amnesic-probing
---

Concept scrubbing applies [[leace]] sequentially at every transformer layer,
erasing all linearly available information about a target concept from the hidden
states throughout the entire forward pass. Because each layer's output feeds into
the next, a single projection at one layer is insufficient if later layers
reconstruct the concept; layer-wise application closes this loophole and enables
clean causal analysis of which computations genuinely depend on the concept.

**Why it matters here:** Applying concept scrubbing to an epistemic axis such as
the answerability subspace or the doubt direction is the strongest available test
of causal reliance: if behaviour changes materially after scrubbing, the axis is
causally upstream of that behaviour, not merely correlated with it, which is
central to claims about whether models use their own uncertainty readouts.

**Lineage:** derives from [[leace]]; related to [[amnesic-probing]], which
performs a similar causal test using iterative projection rather than the
closed-form LEACE operator.
