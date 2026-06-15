---
aliases:
- RLHF reduces closed-domain hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-reduces-closed-domain-hallucination
  type: mechanism
  status: canonical
cause: '[[reinforcement-learning-from-human-feedback]] fine-tuning (PPO) of [[gpt-3]] on human preference data'
effect: '[[hallucination]] rate on closed-domain tasks drops from 41% to 21%'
polarity: decreases
related:
- '[[2203.02155--instructgpt-rlhf]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[gpt-3]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2203.02155--instructgpt-rlhf]]'
  target_id: paper:2203.02155
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

When human raters explicitly penalize fabricated or unsupported claims, RLHF trains the policy to avoid generating content that raters flag as hallucinated. The InstructGPT paper (arXiv:2203.02155) measures this directly on a closed-domain generation task, finding hallucination drops by roughly half relative to the SFT baseline. The effect is specific to closed-domain settings where source faithfulness can be evaluated; open-domain hallucination is harder to capture through preference labeling alone.
