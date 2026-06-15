---
aliases:
- PPO-ptx model
tags:
- kg/model
- concept
- model
kg:
  id: model:instructgpt
  type: model
  status: canonical
area: models
related:
- '[[2203.02155--instructgpt-rlhf]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[reward-model]]'
- '[[proximal-policy-optimization]]'
- '[[gpt-3]]'
relationships:
- type: proposed_by
  target: '[[2203.02155--instructgpt-rlhf]]'
  target_id: paper:2203.02155
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
---

InstructGPT is a family of GPT-3 models (1.3B, 6B, and 175B parameters) fine-tuned via the three-step RLHF pipeline: supervised fine-tuning on labeler demonstrations, reward model training on pairwise comparisons, and PPO-ptx optimization against that reward model with a pretraining mix to mitigate the alignment tax. Human evaluators strongly preferred InstructGPT outputs to GPT-3 outputs of similar or larger parameter count, and the models showed reduced hallucination and improved truthfulness on TruthfulQA.

**Why it matters here:** InstructGPT established the RLHF template that later abstention and calibration work either builds on or reacts against. The [[ppo-ptx-mitigates-alignment-tax]] mechanism and the [[rlhf-reduces-closed-domain-hallucination]] finding both originate here, providing the baseline against which SFT, DPO, and KTO approaches to honesty are compared.

**Lineage:** related to [[reinforcement-learning-from-human-feedback]], [[supervised-finetuning]], [[reward-model]], [[proximal-policy-optimization]], and [[gpt-3]].
