---
aliases:
- logarithmic scoring rule calibrates direct confidence
- log-score RL confidence calibration
- proper scoring reward for direct confidence expression
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:logarithmic-scoring-rl-calibrates-direct-confidence
  type: mechanism
  status: canonical
cause: "Fine-tuning a model with an RL reward derived from a logarithmic scoring rule over the model's stated confidence and answer correctness"
effect: "The model is incentivized to state confidence equal to its empirical probability of being correct, reducing calibration error in generated confidence expressions"
polarity: enables
related:
- '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
- '[[rewarding-doubt]]'
- '[[proper-scoring-rule-rl-reward-calibrates-verbalized-confidence]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
  target_id: paper:2503.02623
  confidence: high
- type: related_to
  target: '[[rewarding-doubt]]'
  target_id: method:rewarding-doubt
  confidence: high
- type: related_to
  target: '[[proper-scoring-rule-rl-reward-calibrates-verbalized-confidence]]'
  target_id: mechanism:proper-scoring-rule-rl-reward-calibrates-verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

A strictly proper scoring rule gives the highest expected reward when a forecaster reports its true probability. Rewarding Doubt applies this idea to generated answers with explicit confidence estimates: if the model is correct, higher stated confidence is rewarded; if it is wrong, overconfidence is penalized. This creates a policy-gradient signal for calibrated direct confidence expression, unlike binary correctness rewards that do not distinguish calibrated and miscalibrated statements once the answer is fixed.

**Why it matters here:** This mechanism is factual-calibration focused. It complements but does not replace faithful-calibration mechanisms, because a model can be well calibrated to empirical correctness while still hiding or distorting its intrinsic uncertainty signal.
