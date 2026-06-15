---
aliases:
- HALO inductive bias drives alignment gains over non-HALOs
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:halo-inductive-bias-drives-alignment-gains
  type: mechanism
  status: canonical
cause: Using a loss function that incorporates [[prospect-theory]] human biases (loss aversion, reference-point sensitivity) as an inductive bias
effect: Significantly better alignment performance at 13B+ scale, with only HALO-aligned models achieving win rates above 50% against SFT targets
polarity: increases
related:
- '[[2402.01306--kto-prospect-theoretic]]'
- '[[prospect-theory]]'
relationships:
- type: supported_by
  target: '[[2402.01306--kto-prospect-theoretic]]'
  target_id: paper:2402.01306
  confidence: high
- type: related_to
  target: '[[prospect-theory]]'
  target_id: term:prospect-theory
---

[[human-aware-loss-functions]] encode how humans actually evaluate outcomes (reference-point-relative utility, asymmetric loss aversion) rather than treating all preference signals as symmetric. This inductive bias matters most at larger scales, where the richer model capacity can exploit the more accurate supervision signal. The KTO paper (arXiv:2402.01306) shows only HALO-class methods exceed 50% win rate against SFT baselines in 13B+ evaluations.
