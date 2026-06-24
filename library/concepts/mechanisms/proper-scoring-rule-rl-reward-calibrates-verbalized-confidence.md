---
aliases:
- log-likelihood RL reward calibrates forecast confidence
- decision-based RL calibrates long-form confidence
- proper scoring rule RL objective induces calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:proper-scoring-rule-rl-reward-calibrates-verbalized-confidence
  type: mechanism
  status: canonical
cause: "Using the log-likelihood of the correct answer under a surrogate forecaster as the PPO reward for a long-form generation policy (instead of binary correctness), combined with a KL penalty from the SFT policy"
effect: "The trained LM generates text whose verbalized confidence statements enable downstream forecasters to produce calibrated probabilistic predictions, yielding lower forecast ECE than binary-correctness RL baselines while matching or exceeding their accuracy"
polarity: enables
related:
- '[[2404.00474--linguistic-calibration-long-form]]'
- '[[linguistic-calibration-lc]]'
- '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
- '[[verbalization-improves-calibration-rlhf]]'
- '[[expected-calibration-error]]'
- '[[proximal-policy-optimization]]'
- '[[surrogate-confidence-estimation]]'
relationships:
- type: supported_by
  target: '[[2404.00474--linguistic-calibration-long-form]]'
  target_id: paper:2404.00474
  confidence: high
- type: related_to
  target: '[[linguistic-calibration-lc]]'
  target_id: method:linguistic-calibration-lc
  confidence: high
- type: related_to
  target: '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
  target_id: mechanism:bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration
  confidence: high
- type: related_to
  target: '[[verbalization-improves-calibration-rlhf]]'
  target_id: mechanism:verbalization-improves-calibration-rlhf
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: high
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: high
---

When a strictly proper scoring rule (here log-likelihood) is used as the RL reward, its expected value is maximized when the surrogate forecaster's predictions are perfectly calibrated, which in turn is achieved when the LM's generated text faithfully conveys the probability that each claim is correct. Binary correctness rewards provide no such calibration gradient; they only reward whether the stated answer matches the ground truth, leaving the model free to express any confidence level. The LC result shows that the ECE gap between SFT and RL is larger under the proper scoring rule reward than under the binary reward, confirming the mechanism. The KL penalty from the SFT policy mitigates over-optimization of the surrogate.
