---
aliases:
- Reward model overestimation undermines RL factuality finetuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reward-model-overestimation-undermines-rl-factuality
  type: mechanism
  status: canonical
cause: Standard [[reward-model]] overestimates rewards for factually incorrect responses on unfamiliar inputs
effect: RL finetuning reinforces [[hallucination|hallucinated]] responses instead of abstaining ones, undermining factuality gains
polarity: increases
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
- '[[reward-model]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2403.05612--unfamiliar-finetuning-examples]]'
  target_id: paper:2403.05612
  confidence: high
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

Standard reward models are trained to prefer fluent, confident, and helpful-sounding responses, which means they can assign high rewards to factually incorrect but plausible-sounding answers on unfamiliar inputs. When RL optimization maximizes this reward, the policy is pushed toward hallucination rather than abstention. The unfamiliar-finetuning paper (arXiv:2403.05612) identifies this as the mechanism by which naive RL finetuning for factuality can backfire, and motivates the [[conservative-reward-model]] as a corrective.
