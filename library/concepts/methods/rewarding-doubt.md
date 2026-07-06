---
aliases:
- Rewarding Doubt
- rewarding doubt confidence RL
- logarithmic confidence RL
tags:
- kg/method
- concept
- method
kg:
  id: method:rewarding-doubt
  type: method
  status: canonical
area: methods
related:
- '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[logarithmic-scoring-rl-calibrates-direct-confidence]]'
relationships:
- type: proposed_by
  target: '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
  target_id: paper:2503.02623
  confidence: high
- type: uses
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: measures
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[logarithmic-scoring-rl-calibrates-direct-confidence]]'
  target_id: mechanism:logarithmic-scoring-rl-calibrates-direct-confidence
  confidence: high
---

Rewarding Doubt is a reinforcement-learning method that fine-tunes an LLM to answer factual questions while emitting an explicit confidence estimate. Its reward is based on a logarithmic scoring rule, so confidence is rewarded when the answer is correct and penalized when the answer is wrong in a way that makes truthful probability reporting optimal.

**Why it matters here:** It is a direct factual-calibration predecessor for later uncertainty-expression training work. Unlike post-hoc probes, it trains the model's generative policy to express confidence directly, making it a useful comparison point for RLMF-style faithful uncertainty objectives.

**Lineage:** proposed in [[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]; related to [[verbalized-confidence]], [[expected-calibration-error]], and [[auroc]].
