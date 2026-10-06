---
title: decision-model-idk-option-under-used-despite-tracking-unknowns
aliases:
- An untrained decision model rarely picks an explicit I don't know option
- IDK option under-used although its probability rises on unknowns
- Decision model keeps answering on true unknowns when given an IDK option
- dmio matrix cell, IDK under-used
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decision-model-idk-option-under-used-despite-tracking-unknowns
  type: mechanism
  status: canonical
  recorded_at: 2026-10-06
cause: "In the decision-model-idk-option experiment, an \"I don't know\" option line is added at analysis time, with no training on it, to the PopQA 4-way choice list of a trained decision model (Qwen3.5-2B-Base torso, LoRA r16 + pointer head) that otherwise always answers; each question is run with the option at all 5 positions, and IDK is picked when it wins the argmax. Populations come from the base torso with no adapter: unknown-true (0 of 32 sampled generations correct and gold picked in 0 of 4 multiple-choice orderings) vs known."
effect: "The pointer model almost never picks the option: mean question IDK rate 0.0185 [0.0138, 0.0238] on unknown-true (n 1,860; H1 FAIL against 0.50) and 0.0066 [0.0012, 0.0140] on known (n 514; H2 PASS against 0.10), so it keeps answering on true unknowns (unknown-true breakdown: IDK 0.0185, right 0.2119, wrong 0.7696). The option's calibrated probability still tracks unknowns: mean P(IDK) is 0.1732 on unknown-true vs 0.0861 on known, and ranks unknown-true above known at AUROC 0.9298 [0.9121, 0.9472], but it is far too low as a probability (binary ECE 0.6377) and rarely wins the argmax. Registered interpretation-matrix cell: 'IDK under-used'."
polarity: limits
related:
- '[[decision-model-idk-option]]'
- '[[decision-model-confidence-threshold-abstention-beats-idk-option]]'
- '[[decision-model-letter-logit-idk-use-is-position-dependent]]'
- '[[base-recognition-explains-decision-model-unknown-row-accuracy]]'
- '[[extra-option-structurally-triggers-abstention]]'
- '[[abstention]]'
- '[[abstention-recall]]'
- '[[over-abstention]]'
- '[[false-option-rejection]]'
- '[[idk-sft]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
- '[[popqa]]'
relationships:
- type: supported_by
  target: '[[decision-model-idk-option]]'
  target_id: experiment:decision-model-idk-option
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/experiment.yaml (verdict field)
  - experiments/decision-model-idk-option/analysis-committed/dmio-pointer_gate_summary.json
    (gates h1, h2; interpretation; secondary per_group, unknown_true_breakdown,
    idk_distribution_calibration)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Gate results;
    Interpretation matrix; Secondary; Post-hoc descriptive interpretation)
- type: related_to
  target: '[[decision-model-confidence-threshold-abstention-beats-idk-option]]'
  target_id: mechanism:decision-model-confidence-threshold-abstention-beats-idk-option
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (H3; the same
    model's confidence abstains far more selectively than the option)
- type: related_to
  target: '[[decision-model-letter-logit-idk-use-is-position-dependent]]'
  target_id: mechanism:decision-model-letter-logit-idk-use-is-position-dependent
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (secondary arm
    lands in the same matrix cell with more, position-dependent IDK use)
- type: related_to
  target: '[[base-recognition-explains-decision-model-unknown-row-accuracy]]'
  target_id: mechanism:base-recognition-explains-decision-model-unknown-row-accuracy
  confidence: medium
- type: different_from
  target: '[[extra-option-structurally-triggers-abstention]]'
  target_id: mechanism:extra-option-structurally-triggers-abstention
  confidence: medium
  note: "Not opposing claims. The literature node reports that an extra Unknown option lifts abstention on True/False items for large instruct and reasoning models; this node reports near-zero option use by a 2B decision model with a pointer or letter head on 4-way PopQA with no training on the option. Different models, task format and readout; both can hold."
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Gate results)
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (H1 is IDK recall
    on unknown-true questions)
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (H2 over-IDK on
    known questions)
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
  confidence: medium
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Follow-up
    directions; training with IDK as a gold answer is the untested next step)
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
---

Given an "I don't know" option it was never trained on, the pointer decision
model nearly always answers instead. It picks IDK on under 2% of the questions
its base torso neither recalls nor recognizes, and on under 1% of known ones.
The option is not invisible to the model: its calibrated probability roughly
doubles on unknown-true questions (0.173 vs 0.086) and ranks them above known
questions at AUROC 0.93. It just almost never wins the argmax.

**Why it matters here:** listing an abstain option is the simplest way to let
a never-refusing decision readout abstain, and with no training it does not
work as an abstention channel on this model. The signal is present in the IDK
mass but not expressed as a choice, so an argmax over options limits how much
of it reaches behavior. Training with IDK as a gold answer ([[idk-sft]]-style)
is the obvious next test; it was not run.

**Caveats:** exploratory tier-2, no training, one checkpoint per arm, one 2B
model, PopQA 4-way multiple choice plus IDK, with labels and recognition from
the base model. The secondary letter-logit arm uses IDK more (0.3254 on
unknown-true) but position-dependently
([[decision-model-letter-logit-idk-use-is-position-dependent]]). Source of
truth: `experiments/decision-model-idk-option/AMENDMENT.md` (Outcome), resolved
2026-10-06 (falsified on H1).
