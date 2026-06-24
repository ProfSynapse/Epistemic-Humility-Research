---
aliases:
- reinforcement learning with calibration rewards
- RLCR
tags:
- kg/method
- concept
- method
kg:
  id: method:rlcr
  type: method
  status: canonical
area: methods
related:
- '[[2507.16806--rlcr-beyond-binary-rewards]]'
- '[[group-relative-policy-optimization]]'
- '[[verbalized-confidence]]'
- '[[brier-score]]'
- '[[reasoning-fine-tuning]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[uncertainty-training-improves-calibration]]'
- '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
relationships:
- type: proposed_by
  target: '[[2507.16806--rlcr-beyond-binary-rewards]]'
  target_id: paper:2507.16806
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
- type: related_to
  target: '[[binary-grading-reinforces-hallucination]]'
  target_id: mechanism:binary-grading-reinforces-hallucination
  confidence: medium
- type: related_to
  target: '[[uncertainty-training-improves-calibration]]'
  target_id: mechanism:uncertainty-training-improves-calibration
  confidence: medium
- type: related_to
  target: '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
  target_id: mechanism:bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration
  confidence: medium
---

A training method for reasoning models that augments the standard binary correctness reward with a Brier score term: R_RLCR = 1[y=y*] - (q - 1[y=y*])^2. The model generates a chain-of-thought trace, an answer, an optional uncertainty analysis, and a verbalized numerical confidence q. Proved (Theorem 1) to simultaneously incentivize both accuracy and calibration when any bounded proper scoring rule is used for the calibration term.

**Why it matters here:** Addresses the empirical finding that RLVR degrades calibration by providing a theoretically grounded reward that preserves accuracy while substantially improving calibration in-domain and OOD, outperforming post-hoc confidence classifiers without requiring a second model.

**Lineage:** Extends RLVR (binary correctness RL) by adding a proper scoring calibration signal; uses GRPO on Qwen2.5-7B base with no KL regularization; relates to SaySelf and Rewarding Doubt which optimize calibration alone (and thus risk reward hacking by incorrect confident predictions).
