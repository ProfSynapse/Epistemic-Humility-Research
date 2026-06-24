---
aliases:
- bounded proper scoring reward incentivizes accuracy and calibration
- Theorem 1 RLCR
- proper scoring calibration reward
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration
  type: mechanism
  status: canonical
cause: "Augmenting a binary correctness reward with a bounded proper scoring rule (e.g., Brier score) as the calibration term in an RL objective"
effect: "The combined reward is simultaneously maximized by (a) the answer with the highest success probability and (b) a confidence equal to the true success probability, yielding models that are both accurate and well-calibrated"
polarity: enables
related:
- '[[2507.16806--rlcr-beyond-binary-rewards]]'
- '[[rlcr]]'
- '[[brier-score]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[overconfidence]]'
- '[[uncertainty-training-improves-calibration]]'
relationships:
- type: supported_by
  target: '[[2507.16806--rlcr-beyond-binary-rewards]]'
  target_id: paper:2507.16806
  confidence: high
- type: related_to
  target: '[[rlcr]]'
  target_id: method:rlcr
  confidence: high
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: high
- type: related_to
  target: '[[binary-grading-reinforces-hallucination]]'
  target_id: mechanism:binary-grading-reinforces-hallucination
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[uncertainty-training-improves-calibration]]'
  target_id: mechanism:uncertainty-training-improves-calibration
  confidence: high
---

Theorem 1 (Damani et al. 2025) proves two properties for R_RLCR = 1[y=y*] - (q - 1[y=y*])^2: (1) for any fixed prediction y, expected reward is maximized when q equals the true probability of success p_y; (2) among all calibrated predictions, expected reward is highest for the y with the greatest p_y. The result generalizes to any bounded proper scoring rule satisfying S(p,1) - S(p,0) < lambda for some finite lambda. Log loss fails because it is unbounded: a model can obtain an arbitrarily negative calibration term by outputting a wrong answer with low confidence, which can outweigh the correctness term for some answer distributions.
