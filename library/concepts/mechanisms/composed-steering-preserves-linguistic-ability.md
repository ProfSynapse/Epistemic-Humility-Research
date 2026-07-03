---
aliases:
- Composed steering improves task performance while preserving general language ability
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:composed-steering-preserves-linguistic-ability
  type: mechanism
  status: canonical
cause: "Injecting a [[steer2adapt]] composed steering vector learned from ~12 examples via Bayesian optimisation over a domain-matched [[semantic-prior-subspace]]"
effect: "Average task performance gains of +7.5% while general syntactic ability degrades only -2.37%, yielding a 3.9x gain-to-cost trade-off ratio"
polarity: enables
related:
- '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
- '[[steer2adapt]]'
- '[[semantic-prior-subspace]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
  target_id: paper:2602.07276
  confidence: high
- type: related_to
  target: '[[steer2adapt]]'
  target_id: method:steer2adapt
- type: related_to
  target: '[[semantic-prior-subspace]]'
  target_id: term:semantic-prior-subspace
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
---

Steer2Adapt constrains the steering intervention to a low-dimensional semantic subspace matched to the target domain, which concentrates the intervention's energy in directions relevant to the task while leaving unrelated linguistic competencies intact. Bayesian optimisation over this subspace requires only a small calibration set (~12 examples) to identify the effective direction. The Steer2Adapt paper (arXiv:2602.07276) reports a 3.9x ratio of task gain (+7.5%) to linguistic cost (-2.37% on BLiMP), a substantially better tradeoff than unconstrained steering vectors that often damage general language ability.
