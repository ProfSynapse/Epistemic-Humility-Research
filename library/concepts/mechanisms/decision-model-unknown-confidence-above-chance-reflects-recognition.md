---
title: decision-model-unknown-confidence-above-chance-reflects-recognition
aliases:
- Decision model confidence on base-unknown rows sits well above chance (dmcc H-A FAIL)
- Recognition without recall on a 4-way choice
- Generation-unknown is not choice-unknown
- Unknown-row confidence is not near chance on a multiple-choice decision readout
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decision-model-unknown-confidence-above-chance-reflects-recognition
  type: mechanism
  status: canonical
  recorded_at: 2026-10-05
cause: "In the decision-model-calibrated-choice experiment, a never-refusing decision model (Qwen3.5-2B-Base torso, LoRA r16 + pointer head) answers PopQA 4-way multiple-choice rows that its base torso labeled unknown under the EH knowledge-probe protocol (the base model cannot generate the answer: 0 of 32 sampled answers correct), with its option confidence R1 calibrated by a temperature fit on a CAL pool that is mostly unknown; the registered H-A gate requires unknown-row confidence near chance, mean(R1 - 0.25) <= 0.10."
effect: "On 4,314 TEST unknown rows the pointer-arm gap is 0.1769 [0.1737, 0.1798], above the 0.10 cap, so H-A FAILS and falsifies the readout-tracks-knowledge line on its calibration leg (the confident-wrong leg passes at 3 / 4,314 = 0.0007; the letter-logit arm fails the same way at 0.1719). Post-hoc and descriptive, not a verdict and not pre-registered: unknown-row accuracy is 0.3832 [0.3688, 0.3978] against 0.25 chance, and mean R1 on unknowns is 0.4269, so confidence exceeds the model's own unknown-row accuracy by only 0.044. Read this way, 'unknown' marks recall failure, and on a 4-way choice the model still recognizes the answer or eliminates distractors; the near-chance ideal conflates recall with recognition. This does not rescue H-A."
polarity: complicates
related:
- '[[decision-model-calibrated-choice]]'
- '[[decision-model-readout-tracks-base-known-unknown-axis]]'
- '[[temperature-scaling]]'
- '[[popqa]]'
- '[[known-unknown-direction]]'
- '[[calibration]]'
relationships:
- type: supported_by
  target: '[[decision-model-calibrated-choice]]'
  target_id: experiment:decision-model-calibrated-choice
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/experiment.yaml (verdict field)
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-pointer-popqa_gate_summary.json
    (H-A a1 and a2; companions)
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Falsifier
    adjudication; Secondary, recall vs recognition; Post-hoc descriptive note on
    H-A)
- type: related_to
  target: '[[decision-model-readout-tracks-base-known-unknown-axis]]'
  target_id: mechanism:decision-model-readout-tracks-base-known-unknown-axis
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Falsifier
    adjudication; ranking passes, calibration to chance fails)
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (predictions,
    orchestrator basis; a CAL-fit temperature leaves unknown-row confidence near
    pooled 4-way accuracy rather than near 0.25)
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

The decision model's confidence on rows its base torso cannot answer is not
near chance: it sits about 0.18 above 1/4, failing the registered H-A cap.
The model is also right on those rows far more often than chance (0.383), and
its confidence is close to that accuracy. The base-model label measures
whether the model can generate the answer, not whether it can pick it from
four options.

**Why it matters here:** a "near chance on unknowns" target for a
multiple-choice readout treats recall failure as total ignorance. Any
follow-up should gate on an unknown-and-unrecognized subset, or judge
unknown-row confidence against the model's own unknown-row accuracy. Either
needs its own registration. The registered verdict stands: H-A FAIL.

**Caveats:** the recognition reading is post-hoc arithmetic on two reported
companions, not a registered statistic. Exploratory tier-2, single seed per
arm, one 2B model, PopQA 4-way multiple choice. Source of truth:
`experiments/decision-model-calibrated-choice/AMENDMENT.md` (Outcome, Post-hoc
descriptive note on H-A), resolved 2026-10-05 (falsified).
