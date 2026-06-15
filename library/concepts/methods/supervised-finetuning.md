---
aliases:
- SFT
- Supervised Fine-Tuning
- Supervised Fine-Tuning (SFT)
- supervised fine-tuning
- behavior cloning
- instruction tuning
- vanilla finetuning
- Supervised Finetuning (SFT)
- supervised learning finetuning
- instruction fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:supervised-finetuning
  type: method
  status: canonical
area: methods
related:
- '[[reinforcement-learning-from-human-feedback]]'
- '[[instruction-tuning]]'
- '[[idk-sft]]'
relationships:
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
---

Supervised fine-tuning adapts a pretrained language model to a target behavior by minimizing cross-entropy loss on a labeled dataset of (input, output) pairs. It is both the first alignment stage in the RLHF pipeline and a standalone technique: in the abstention literature it is used to teach "I don't know" responses via [[idk-sft]], and in verbalized-confidence work it trains the model to output calibrated probability estimates labeled from empirical per-task accuracy.

**Why it matters here:** SFT is one of the three training arms in the Phase 1 experiment and serves as the baseline and prerequisite for DPO and KTO initialization. Prior work shows SFT alone can induce over-refusal ([[sft-abstention-causes-over-refusal]]), motivating the preference-optimization alternatives.

**Lineage:** prerequisite for [[reinforcement-learning-from-human-feedback]]; [[direct-preference-optimization]] and [[kahneman-tversky-optimization]] both initialize from an SFT checkpoint.
