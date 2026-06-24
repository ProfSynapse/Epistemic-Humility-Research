---
aliases:
- preference collapse generalises to calibration
- alignment collapse drives overconfidence in multiple-choice
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:preference-collapse-causes-alignment-overconfidence
  type: mechanism
  status: canonical
cause: "Preference alignment via RLHF or direct-preference-optimization trains the model to assign disproportionately high probability to one response option, collapsing the preference ratio beyond human preference proportions."
effect: "On multiple-choice tasks the model assigns near-unit probability to one option regardless of correctness, producing systematic overconfidence and high ECE even when the base model was well-calibrated."
polarity: increases
related:
- '[[2505.01997--restoring-calibration-aligned-llms]]'
- '[[direct-preference-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[overconfidence]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[reward-model-confidence-bias-drives-rlhf-overconfidence]]'
- '[[rlhf-degrades-conditional-calibration]]'
relationships:
- type: supported_by
  target: '[[2505.01997--restoring-calibration-aligned-llms]]'
  target_id: paper:2505.01997
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[reward-model-confidence-bias-drives-rlhf-overconfidence]]'
  target_id: mechanism:reward-model-confidence-bias-drives-rlhf-overconfidence
  confidence: high
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
---

Xiao et al. (arXiv:2505.01997) observe that the preference collapse phenomenon documented in alignment work (models excessively favouring chosen responses) generalises from open-ended preference pairs to the fixed-option structure of multiple-choice questions. In that setting the model collapses its distribution onto one letter option across a range of questions, which directly inflates confidence on wrong answers and degrades calibration. The mechanism is causal in the paper's framing: removing the alignment step (using the pre-trained or SFT checkpoint) restores calibration, while adding it reinstates overconfidence. This is distinct from the reward-model-confidence-bias-drives-rlhf-overconfidence mechanism, which operates through verbalized confidence rather than token-level probability collapse.
