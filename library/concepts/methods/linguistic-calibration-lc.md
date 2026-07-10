---
aliases:
- LC
- LC RL
- LC SFT
- linguistic calibration of long-form generations
- decision-based linguistic calibration
tags:
- kg/method
- concept
- method
kg:
  id: method:linguistic-calibration-lc
  type: method
  status: canonical
area: methods
related:
- '[[2404.00474--linguistic-calibration-long-form]]'
- '[[summary-distillation]]'
- '[[proximal-policy-optimization]]'
- '[[supervised-finetuning]]'
- '[[expected-calibration-error]]'
- '[[verbalized-confidence]]'
- '[[triviaqa]]'
- '[[factscore]]'
- '[[proper-scoring-rule-rl-reward-calibrates-verbalized-confidence]]'
relationships:
- type: proposed_by
  target: '[[2404.00474--linguistic-calibration-long-form]]'
  target_id: paper:2404.00474
  confidence: high
- type: related_to
  target: '[[summary-distillation]]'
  target_id: method:summary-distillation
  confidence: medium
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
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
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[proper-scoring-rule-rl-reward-calibrates-verbalized-confidence]]'
  target_id: mechanism:proper-scoring-rule-rl-reward-calibrates-verbalized-confidence
  confidence: medium
---

A two-stage training framework that calibrates verbalized confidence statements in long-form LM outputs by (1) summary distillation SFT to bootstrap confidence expression, followed by (2) PPO with a log-likelihood proper scoring rule reward computed by a neural-net surrogate forecaster conditioned on the model's generated context. An LM is linguistically calibrated if its generations enable downstream users to make calibrated probabilistic forecasts on related decision tasks.

**Why it matters here:** Provides a principled end-to-end objective for training LMs to express graded, calibrated confidence in natural-language paragraphs rather than short answers. Directly relevant to Phase 1 as a calibration-first alternative to binary-reward factuality RL (Factuality RL), and to mechanism program as a case where the training signal lives in forecast-space rather than output-correctness-space.

**Lineage:** proposed by Band et al. (2024); builds on proximal-policy-optimization, supervised-finetuning, and summary-distillation; evaluated on triviaqa, jeopardy-qa, factscore
