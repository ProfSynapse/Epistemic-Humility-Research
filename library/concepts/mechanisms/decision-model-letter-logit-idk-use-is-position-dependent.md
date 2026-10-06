---
title: decision-model-letter-logit-idk-use-is-position-dependent
aliases:
- Letter-logit decision model IDK picks depend on where the option sits
- IDK option position effect, peak at the middle option
- Option-pick rates are not awareness readouts
- dmio secondary arm position-bias flag
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decision-model-letter-logit-idk-use-is-position-dependent
  type: mechanism
  status: canonical
  recorded_at: 2026-10-06
cause: "In the decision-model-idk-option experiment, the secondary letter-logit decision model (Qwen3.5-2B-Base torso, LoRA r16 + letter-logit head, untrained on any IDK option) is given an added \"I don't know\" option at each of 5 positions on PopQA 4-way questions, and its pick-IDK rate is read per position and averaged per question."
effect: "It picks IDK far more than the pointer model (unknown-true 0.3254 [0.3092, 0.3423], H1 FAIL against 0.50; known 0.0230, H2 PASS), but the rate depends strongly on position: on unknown-true, 0.1290, 0.3156, 0.5704, 0.3226, 0.2892 for positions 1 to 5 (range 0.4414, peak at position 3, the middle option C.), pooled range 0.3426; the registered position-bias flag fires on pooled and unknown-true rows and is carried as a caveat beside H1 and H2, changing no verdict. Known rows are unflagged (range 0.0136). Its H3 is NOT-ADJUDICABLE (over-IDK 0.0230 vs baseline over-abstention 0.0039, operating points not matched). The pointer arm shows no position flag (ranges all under 0.10)."
polarity: complicates
related:
- '[[decision-model-idk-option]]'
- '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
- '[[extra-option-structurally-triggers-abstention]]'
- '[[abstention]]'
- '[[abstention-rate]]'
- '[[popqa]]'
relationships:
- type: supported_by
  target: '[[decision-model-idk-option]]'
  target_id: experiment:decision-model-idk-option
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/experiment.yaml (verdict field)
  - experiments/decision-model-idk-option/analysis-committed/dmio-letter_logits_gate_summary.json
    (gates h1, h2, h3; secondary position_bias, position_bias_caveat_h1_h2)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Caveats and
    sensitivities, position bias; Post-hoc descriptive interpretation)
- type: related_to
  target: '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
  target_id: mechanism:decision-model-idk-option-under-used-despite-tracking-unknowns
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Interpretation
    matrix; both arms land in the IDK under-used cell)
- type: related_to
  target: '[[extra-option-structurally-triggers-abstention]]'
  target_id: mechanism:extra-option-structurally-triggers-abstention
  confidence: low
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (an option-pick
    rate that moves with the option's slot is partly structural; different
    models and task, so context only)
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
---

The letter-logit decision model uses the "I don't know" option much more than
the pointer model, but how often depends on where the option is listed. On
questions the base torso truly does not know, it picks IDK 13% of the time in
first position and 57% in the middle position. Averaging over all five
positions folds this effect into each question's rate but does not remove it.

**Why it matters here:** an option-pick rate is not a clean readout of
awareness. A large IDK rate on unknowns can come partly from where the option
sits in the list rather than from what the model knows. Any IDK-option result
should report per-position rates and not read a pooled pick rate as evidence
that the model knows it does not know.

**Caveats:** secondary, exploratory arm with no confirmatory claim. Exploratory
tier-2, no training, one checkpoint, one 2B model, PopQA 4-way multiple choice
plus IDK. Source of truth:
`experiments/decision-model-idk-option/AMENDMENT.md` (Outcome, Caveats and
sensitivities), resolved 2026-10-06.
