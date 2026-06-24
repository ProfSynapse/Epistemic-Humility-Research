---
aliases:
- joint calibration-preference training prevents logit inflation
- CATTO prevents confidence drift during DPO
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:calibration-aware-training-prevents-confidence-drift
  type: mechanism
  status: canonical
cause: "Augmenting the DPO objective with a per-token L1 calibration loss that penalizes deviations between predicted confidence and a probability-margin correctness surrogate during preference alignment training."
effect: "Token-level confidence remains anchored to empirical correctness throughout alignment; post-training ECE is substantially lower than DPO alone and comparable to or better than post-hoc calibration methods (RCFT, DPO+BCE), while task accuracy is preserved or improved."
polarity: prevents
related:
- '[[2601.23096--catto-per-token-calibration]]'
- '[[catto]]'
- '[[preference-collapse-causes-alignment-overconfidence]]'
- '[[direct-preference-optimization]]'
- '[[expected-calibration-error]]'
- '[[regularized-calibration-aware-fine-tuning]]'
- '[[calibration]]'
- '[[overconfidence]]'
relationships:
- type: supported_by
  target: '[[2601.23096--catto-per-token-calibration]]'
  target_id: paper:2601.23096
  confidence: high
- type: related_to
  target: '[[catto]]'
  target_id: method:catto
  confidence: high
- type: related_to
  target: '[[preference-collapse-causes-alignment-overconfidence]]'
  target_id: mechanism:preference-collapse-causes-alignment-overconfidence
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[regularized-calibration-aware-fine-tuning]]'
  target_id: method:regularized-calibration-aware-fine-tuning
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
---

DPO training leaves absolute token probability scales unconstrained, allowing logit magnitudes to drift toward extreme overconfidence. CATTO adds a bounded calibration gradient that pulls each token's predicted confidence toward a smooth correctness target derived from the probability margin (sigma(p_correct - p_best_wrong)). Because the calibration gradient is bounded (Proposition E.11 in Appendix E), it does not disrupt the preference ordering established by the DPO term, so preference alignment and calibration are jointly compatible. The result is that confidence drift is suppressed at training time rather than corrected post-hoc. Validated across five benchmarks (Reward Bench 2, SNLI, ANLI, TLDR, CommonsenseQA) in in-distribution and OOD regimes using Qwen3-4B; OOD generalization is substantially better than RCFT and DPO+BCE.
