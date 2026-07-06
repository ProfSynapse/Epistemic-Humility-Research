---
aliases:
- metacognitive advantage scaling improves faithful calibration
- self-judgment-scaled RL improves uncertainty faithfulness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:metacognitive-advantage-scaling-improves-faithful-calibration
  type: mechanism
  status: canonical
cause: "Scaling above-average faithful-calibration completions by the accuracy of the model's self-judgment during GRPO-style training."
effect: "Higher and more generalizable faithful calibration than standard RL while preserving task accuracy and factual calibration."
polarity: increases
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[reinforcement-learning-with-metacognitive-feedback]]'
- '[[group-relative-policy-optimization]]'
- '[[faithful-calibration]]'
- '[[cmfg-star-equal-mass]]'
relationships:
- type: supported_by
  target: '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
  target_id: paper:2606.32032
  confidence: high
  evidence:
  - "Table 1"
  - "Figure 25"
- type: related_to
  target: '[[reinforcement-learning-with-metacognitive-feedback]]'
  target_id: method:reinforcement-learning-with-metacognitive-feedback
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[cmfg-star-equal-mass]]'
  target_id: metric:cmfg-star-equal-mass
  confidence: high
---

The paper supports the claim that using self-judgment accuracy as a multiplier on the faithfulness component of the advantage signal strengthens faithful calibration relative to standard RL. Table 1 shows stronger average `cMFG*` for RLMF than the standard-RL ablation, and Figure 25 reports increasing metacognitive performance during RLMF training.
