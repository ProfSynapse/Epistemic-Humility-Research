---
aliases:
- RLHF OOD advantage scales with shift difficulty
- RLHF generalises better under hard distribution shift
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-generalisation-advantage-scales-with-shift-severity
  type: mechanism
  status: canonical
cause: "Training a language model with RLHF (on-policy RL with reward model) rather than SFT"
effect: "Larger absolute and relative generalisation advantage over SFT on harder OOD shifts; comparable or slightly worse relative generalisation gap on easy OOD shifts"
polarity: enables
related:
- '[[2310.06452--rlhf-generalisation-diversity]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[best-of-n-sampling]]'
- '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
- '[[abstention-generalization-failure]]'
- '[[p-ik-ood-generalization-gap]]'
relationships:
- type: supported_by
  target: '[[2310.06452--rlhf-generalisation-diversity]]'
  target_id: paper:2310.06452
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: high
- type: related_to
  target: '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
  target_id: mechanism:rlhf-rl-optimisation-collapses-per-input-diversity
  confidence: high
- type: related_to
  target: '[[abstention-generalization-failure]]'
  target_id: mechanism:abstention-generalization-failure
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
---

Kirk et al. (2023) find that on the easier AlpacaEval OOD shift, RLHF and SFT achieve similar generalisation gaps, and head-to-head metrics give RLHF only a ~3.5pp advantage over SFT. On the harder Sequential Instructions OOD task, RLHF generalises much better. The Discussion (Section 7) explicitly qualifies that 'in less difficult shifts RLHF generalises similarly or slightly worse than SFT as measured by generalisation gap.' The mechanism is hypothesised to relate to how reward-model training shapes a more robust task representation, but is not theoretically validated in this paper.
