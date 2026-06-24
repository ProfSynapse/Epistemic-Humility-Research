---
aliases:
- IDK domination in SFT collapses RL recovery
- RTuning SFT overloads abstention and prevents RL repair
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:excess-sft-idk-causes-capability-collapse
  type: mechanism
  status: canonical
cause: "An SFT warm-up in which the proportion of IDK-labeled training examples is too high (approximately 60% in RL-RTuning vs approximately 30% in RL-SFT-Random)"
effect: "The model's general task capability collapses after SFT and the subsequent RL stage cannot recover useful accuracy, so RL-RTuning underperforms the simpler RL-SFT-Random despite its theoretically superior error-aware data curation"
polarity: prevents
related:
- '[[2601.20126--rewarding-intellectual-humility]]'
- '[[answer-relabeling-enables-abstention]]'
- '[[narrow-sft-data-collapses-output-diversity]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[idk-sft]]'
- '[[rl-sft-random-abstention]]'
- '[[abstention]]'
- '[[over-abstention]]'
relationships:
- type: supported_by
  target: '[[2601.20126--rewarding-intellectual-humility]]'
  target_id: paper:2601.20126
  confidence: high
- type: related_to
  target: '[[answer-relabeling-enables-abstention]]'
  target_id: mechanism:answer-relabeling-enables-abstention
  confidence: high
- type: related_to
  target: '[[narrow-sft-data-collapses-output-diversity]]'
  target_id: mechanism:narrow-sft-data-collapses-output-diversity
  confidence: high
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: high
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: high
- type: related_to
  target: '[[rl-sft-random-abstention]]'
  target_id: method:rl-sft-random-abstention
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
---

RTuning labels every question the base model answered incorrectly as IDK in the SFT set. Because the Granite base model errors on approximately 53% of MedMCQA questions, the SFT corpus ends up with approximately 60% IDK labels. After SFT the model has lost its ability to produce meaningful answers; the RL phase rewarding correct answers only partially reverses this, leaving RL-RTuning at 47% correct and 45% incorrect (Table 1, r_abs = -0.25) versus RL-SFT-Random at 39% correct and 40% incorrect with much higher 21% IDK. The paper proposes capping the SFT IDK ratio at 20-30% as a fix (Section 6). This mechanism is a specific instance of SFT data imbalance causing capability regression, distinct from narrow-sft-data-collapses-output-diversity in that the problem is label-class dominance rather than topic narrowness.
