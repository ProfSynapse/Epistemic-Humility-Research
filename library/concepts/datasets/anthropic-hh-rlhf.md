---
aliases:
- Anthropic hh-rlhf
- HH-RLHF
- Helpful and Harmless RLHF
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:anthropic-hh-rlhf
  type: dataset
  status: canonical
area: datasets
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: used_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
---

Anthropic HH-RLHF contains helpfulness and harmlessness preference data. The
paper uses its prompts for PPO training with an external reward model.

**Why it matters here:** The reward signal provides sparse pressure against
harmful compliance without directly training on refusal completions.

**Lineage:** It is a standard dataset for
[[reinforcement-learning-from-human-feedback]].
