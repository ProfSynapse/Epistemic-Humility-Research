---
aliases:
- ConfTuner fine-tuning
- tokenized Brier score fine-tuning
- proper-scoring verbalized calibration SFT
tags:
- kg/method
- concept
- method
kg:
  id: method:conftuner
  type: method
  status: canonical
area: methods
related:
- '[[2508.18847--conftuner]]'
- '[[verbalized-confidence]]'
- '[[brier-score]]'
- '[[supervised-finetuning]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
- '[[surrogate-confidence-estimation]]'
- '[[hotpotqa]]'
- '[[triviaqa]]'
- '[[truthfulqa]]'
- '[[strategyqa]]'
- '[[gsm8k]]'
relationships:
- type: proposed_by
  target: '[[2508.18847--conftuner]]'
  target_id: paper:2508.18847
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
  target_id: mechanism:bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration
  confidence: medium
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: medium
- type: related_to
  target: '[[hotpotqa]]'
  target_id: dataset:hotpotqa
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[strategyqa]]'
  target_id: dataset:strategyqa
  confidence: medium
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
---

A supervised fine-tuning method that calibrates LLM verbalized confidence by computing a probability distribution over a discrete set of confidence tokens from output logits and minimizing the tokenized Brier score against the binary correctness indicator, without requiring ground-truth confidence scores, proxy estimates, or repeated sampling.

**Why it matters here:** Provides a principled, data-efficient SFT baseline for verbalized calibration grounded in proper scoring theory, directly comparable to the Phase 1 SFT arm; trains in 4 minutes on 2,000 examples yet outperforms sampling-heavy proxy methods (SaySelf, LACIE) on ECE and AUROC across five diverse datasets.

**Lineage:** Proposed in 2508.18847 (Li et al., NUS 2025); extends the classical Brier proper scoring rule into the verbalized-token setting; contrasts with RLCR (2507.16806) which applies the same Brier guarantee inside an RL reward; competes with SaySelf and LACIE as training-based verbalized calibration methods.
