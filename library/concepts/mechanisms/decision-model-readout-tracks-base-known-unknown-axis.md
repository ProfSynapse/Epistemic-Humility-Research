---
title: decision-model-readout-tracks-base-known-unknown-axis
aliases:
- A never-refusing decision readout tracks the base known-unknown axis
- Decision model calibrated option confidence separates known from unknown
- Frozen base KU direction survives into the decision model answer state
- dmcc matrix cell, readout confidence tracks the base KU axis
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decision-model-readout-tracks-base-known-unknown-axis
  type: mechanism
  status: canonical
  recorded_at: 2026-10-05
cause: "In the decision-model-calibrated-choice experiment, a decision model (Qwen3.5-2B-Base torso, LoRA r16 + pointer head) that never refuses reports a CAL-temperature-calibrated softmax over 4 PopQA options at <answer> (R1), with no verbalized confidence channel; R1 and the base model's frozen known-unknown gate direction (prompt anchor, layer 14, fit on the raw base with no adapter) are scored against the base torso's own prior known/unknown label on TEST (514 known / 4,314 unknown)."
effect: "R1 ranks known vs unknown at AUROC 0.9407 [0.9266, 0.9526] (H-C PASS against 0.75), and the frozen base direction, applied without refitting to the decision <answer> state at the same layer index, reads known vs unknown at 0.9762 [0.9718, 0.9805] (H-D1 PASS), after Stage 0 validated it on base CAL at 0.9792 with a label-permuted twin at 0.4901. Known rows are confident and right (underconfident-right 0.0603, H-B PASS; known accuracy 0.969). The registered interpretation-matrix cell is 'readout confidence tracks the base known-unknown axis'; the secondary letter-logit arm lands in the same cell (H-C 0.9525, H-D1 0.9736). Ranking only: the same readout is not near chance on unknowns (H-A FAIL), and the decision state carries more KU signal than R1 expresses (H-D2 PASS)."
polarity: enables
related:
- '[[decision-model-calibrated-choice]]'
- '[[known-unknown-direction]]'
- '[[temperature-scaling]]'
- '[[popqa]]'
- '[[auroc]]'
- '[[decision-model-state-carries-more-ku-signal-than-its-readout]]'
- '[[decision-model-unknown-confidence-above-chance-reflects-recognition]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
- '[[answerability-axis-present-without-task-training]]'
relationships:
- type: supported_by
  target: '[[decision-model-calibrated-choice]]'
  target_id: experiment:decision-model-calibrated-choice
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/experiment.yaml (verdict field)
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-pointer-popqa_gate_summary.json
    (gates H-B, H-C, H-D1; interpretation)
  - experiments/decision-model-calibrated-choice/analysis-committed/stage0_freeze.json
    (S0-G1, S0-G2)
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Stage 0;
    Stage 1 gate results; Interpretation matrix)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Stage 0; base KU
    gate and dial directions fit on FIT, frozen before Stage 1)
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Stage 1; R1 is the
    option softmax at <answer> calibrated by a CAL-fit temperature)
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[decision-model-state-carries-more-ku-signal-than-its-readout]]'
  target_id: mechanism:decision-model-state-carries-more-ku-signal-than-its-readout
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome
    (Interpretation matrix; H-D2 adds that the state carries more than R1)
- type: related_to
  target: '[[decision-model-unknown-confidence-above-chance-reflects-recognition]]'
  target_id: mechanism:decision-model-unknown-confidence-above-chance-reflects-recognition
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Falsifier
    adjudication; the line is falsified on the calibration leg, not the ranking
    leg)
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Motivation and
    posture; a non-LM-head option readout as the alternative to the emitted
    scalar; different family, size and population, so context only)
- type: related_to
  target: '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
  target_id: mechanism:known-unknown-direction-transfers-partially-across-prompt-contracts
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (H-D1
    frozen base 0.9762 vs fresh in-state probe 0.9916, across a LoRA, a new
    prompt and a new position)
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Stage 0;
    raw base gate direction CAL AUROC 0.9792)
---

A decision model that cannot refuse still gives option confidence that ranks
what its base torso knows: calibrated R1 separates the base model's known from
unknown PopQA rows at AUROC 0.94, and the base model's own frozen KU direction,
fit with no adapter at the QA prompt end, still reads the decision model's
`<answer>` state at 0.976. Known rows are answered right (0.969) and rarely
with low confidence. Both the pointer and the letter-logit arms land in the
registered "readout confidence tracks the base known-unknown axis" cell.

**Why it matters here:** in the program's generative models the stated channel
does not report the KU signal ([[verbalized-confidence-channel-bottleneck]]).
A readout with no verbalized channel does rank by it on this model and
population. The result is about ranking only. Unknown-row confidence is well
above chance
([[decision-model-unknown-confidence-above-chance-reflects-recognition]]), and
an internal probe still sees more than R1 reports
([[decision-model-state-carries-more-ku-signal-than-its-readout]]).

**Caveats:** exploratory tier-2, single seed per arm, one 2B model, PopQA 4-way
multiple choice with base-model-generated labels. Not a matched comparison with
paper 3. A frozen label-permuted direction scores the decision states at 0.7632
(descriptive), so H-D1's margin over arbitrary mid-depth directions is smaller
than its margin over chance. Source of truth:
`experiments/decision-model-calibrated-choice/AMENDMENT.md` (Outcome),
resolved 2026-10-05 (falsified on H-A).
