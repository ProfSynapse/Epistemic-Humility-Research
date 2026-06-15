---
aliases:
- GRPO critic elimination reduces training memory
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:grpo-eliminates-critic-reduces-memory
  type: mechanism
  status: canonical
cause: Replacing the PPO value/critic model with a group-score baseline in [[group-relative-policy-optimization]]
effect: Significant reduction in training memory and compute without sacrificing performance
polarity: decreases
related:
- '[[2402.03300--deepseekmath-grpo]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: supported_by
  target: '[[2402.03300--deepseekmath-grpo]]'
  target_id: paper:2402.03300
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
---

[[group-relative-policy-optimization]] estimates advantages by comparing each response's reward against the mean reward of a group sampled from the same prompt, removing the need for a separate value network. Eliminating the critic model halves the number of model copies held in GPU memory during training. The DeepSeekMath paper (arXiv:2402.03300) shows this reduces memory pressure substantially while matching or exceeding PPO performance on mathematical reasoning benchmarks.
