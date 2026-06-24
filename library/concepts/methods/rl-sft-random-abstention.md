---
aliases:
- SFT-Random
- random abstention pretraining before RL
tags:
- kg/method
- concept
- method
kg:
  id: method:rl-sft-random-abstention
  type: method
  status: canonical
area: methods
related:
- '[[2601.20126--rewarding-intellectual-humility]]'
- '[[ternary-reward-design]]'
- '[[idk-sft]]'
- '[[supervised-finetuning]]'
- '[[group-relative-policy-optimization]]'
- '[[abstention-recall]]'
- '[[medmcqa]]'
- '[[math-benchmark]]'
relationships:
- type: proposed_by
  target: '[[2601.20126--rewarding-intellectual-humility]]'
  target_id: paper:2601.20126
  confidence: high
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: medium
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
  confidence: medium
- type: related_to
  target: '[[medmcqa]]'
  target_id: dataset:medmcqa
  confidence: medium
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
  confidence: medium
---

A two-stage abstention training pipeline in which a random subset (approximately 30%) of ground-truth answers in the SFT training set are relabeled as IDK responses before supervised fine-tuning, providing the model with an abstention warm-up; the resulting SFT checkpoint is then further fine-tuned with RLVR using a ternary reward. The random relabeling rate is a hyperparameter.

**Why it matters here:** RL-SFT-Random breaks the exploration bottleneck that prevents RL-only from inducing abstention on open-ended QA. The paper shows it achieves better abstention recall than RTuning on both MedMCQA and MATH, and can cut incorrect answers by roughly half on MATH when r_abs is tuned appropriately.

**Lineage:** Introduced in this paper as a baseline ablation against RL-RTuning; builds on the general idea of answer relabeling from idk-sft and r-tuning, but uses random rather than error-based selection.
