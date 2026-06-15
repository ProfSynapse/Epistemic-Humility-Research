---
aliases:
- Code pre-training prior to math pre-training improves mathematical reasoning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:code-pretraining-benefits-math-reasoning
  type: mechanism
  status: canonical
cause: Pre-training on code tokens before math-domain continual pre-training on the [[deepseekmath-corpus]]
effect: Improved mathematical reasoning performance on [[math-benchmark]] and [[gsm8k]] both with and without tool use
polarity: increases
related:
- '[[2402.03300--deepseekmath-grpo]]'
- '[[deepseekmath-corpus]]'
- '[[math-benchmark]]'
- '[[gsm8k]]'
relationships:
- type: supported_by
  target: '[[2402.03300--deepseekmath-grpo]]'
  target_id: paper:2402.03300
  confidence: high
- type: related_to
  target: '[[deepseekmath-corpus]]'
  target_id: dataset:deepseekmath-corpus
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
---

Code data shares structural properties with mathematical reasoning: precise syntax, stepwise derivation, and formal logical structure. Pre-training on code before switching to mathematical text appears to prime the model's representations for the kind of structured procedural reasoning mathematics requires. The DeepSeekMath paper (arXiv:2402.03300) demonstrates that models with a code pre-training phase outperform those without it on both tool-assisted and tool-free math evaluations.
