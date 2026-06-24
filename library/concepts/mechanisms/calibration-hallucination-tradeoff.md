---
aliases:
- calibration-factuality tradeoff
- post-training calibration-hallucination tradeoff
- calibration cost of reducing hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:calibration-hallucination-tradeoff
  type: mechanism
  status: canonical
cause: "Post-training alignment (RLHF or similar) applied to a calibrated pretrained language model to reduce hallucination on arbitrary facts"
effect: "Calibration error increases relative to the pre-alignment model, as the model's probability estimates become less faithful to empirical fact frequencies"
polarity: mediates
related:
- '[[2311.14648--calibrated-lms-must-hallucinate]]'
- '[[calibration]]'
- '[[hallucination]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[rlhf-degrades-conditional-calibration]]'
- '[[monofact-estimator]]'
relationships:
- type: supported_by
  target: '[[2311.14648--calibrated-lms-must-hallucinate]]'
  target_id: paper:2311.14648
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
- type: related_to
  target: '[[monofact-estimator]]'
  target_id: term:monofact-estimator
  confidence: high
---

Kalai and Vempala (2023) prove that a calibrated pretrained LM must hallucinate at a rate near the monofact estimate; the only way to reduce this rate below the statistical floor is to sacrifice calibration. Figure 1 (reproduced from OpenAI 2023 GPT-4 Technical Report) shows GPT-4 calibration curves on a multiple-choice exam before and after RLHF: the post-RLHF curve is more bowed, indicating visibly increased calibration error. The paper's caption explicitly notes the figure measures calibration on a classification task, not generative hallucination rates directly; the hallucination inference is the paper's argument consistent with its theory (Section 1, lines 152-155).
