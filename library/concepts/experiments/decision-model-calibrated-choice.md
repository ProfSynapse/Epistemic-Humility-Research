---
title: decision-model-calibrated-choice
aliases:
- Decision-model calibrated choice (dmcc)
- 'Does a never-refusing decision readout track what the base torso knows?'
- Decision model pointer-head confidence vs base known-unknown label on PopQA
- Calibrated option confidence of a decision model that cannot refuse
tags:
- kg/experiment
- experiment
- calibration
- known-unknown-readout
kg:
  id: experiment:decision-model-calibrated-choice
  type: experiment
  status: canonical
  recorded_at: 2026-10-05
related:
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[internal-twosignal-readout--training-free]]'
- '[[stated-confidence-under-pstruct]]'
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[decision-model-readout-tracks-base-known-unknown-axis]]'
- '[[decision-model-state-carries-more-ku-signal-than-its-readout]]'
- '[[decision-model-unknown-confidence-above-chance-reflects-recognition]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
- '[[known-unknown-direction]]'
- '[[popqa]]'
- '[[qwen]]'
- '[[temperature-scaling]]'
- '[[linear-probe]]'
- '[[conformal-prediction-for-llm-uncertainty]]'
- '[[auroc]]'
relationships:
- type: builds_on
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Motivation and
    posture; paper 3's represented-but-not-reported result, internal KU readout
    AUROC 0.997 vs stated confidence 0.52 to 0.56 on SelfAware, is the context
    the cell asks a never-refusing readout about; not a matched comparison)
- type: builds_on
  target: '[[stated-confidence-under-pstruct]]'
  target_id: experiment:stated-confidence-under-pstruct
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Motivation and
    posture; the stated channel is severely miscalibrated on every trained arm,
    which motivates removing the verbalized channel entirely)
- type: builds_on
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Relationship to
    existing protocols; Stage 0 fits gate and dial KU directions in the pattern
    of the frozen two-signal directions, which have no Qwen3.5-2B entry)
- type: builds_on
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Stage 0 tier
    ruling; extract, fit and freeze inside the cell, as rawbase-ambigqa-boundary-readout
    does)
- type: supports
  target: '[[decision-model-readout-tracks-base-known-unknown-axis]]'
  target_id: mechanism:decision-model-readout-tracks-base-known-unknown-axis
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/experiment.yaml (verdict field)
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-pointer-popqa_gate_summary.json
    (H-C, H-D1, interpretation)
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Stage 1
    gate results; Interpretation matrix)
- type: supports
  target: '[[decision-model-state-carries-more-ku-signal-than-its-readout]]'
  target_id: mechanism:decision-model-state-carries-more-ku-signal-than-its-readout
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-pointer-popqa_gate_summary.json
    (H-D2)
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (H-D2
    detail; H-D1 registered comparison with the readout)
- type: supports
  target: '[[decision-model-unknown-confidence-above-chance-reflects-recognition]]'
  target_id: mechanism:decision-model-unknown-confidence-above-chance-reflects-recognition
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-pointer-popqa_gate_summary.json
    (H-A a1, a2)
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Falsifier
    adjudication; Post-hoc descriptive note on H-A)
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Motivation and
    posture; a decision model removes the verbalized channel, so the cell asks
    whether a non-LM-head readout carries the KU signal; no LM-head arm is run,
    so this is context, not a test of the bottleneck)
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Stage 0;
    the raw Qwen3.5-2B-Base gate direction reads CAL known vs unknown at AUROC
    0.9792)
- type: related_to
  target: '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
  target_id: mechanism:known-unknown-direction-transfers-partially-across-prompt-contracts
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (H-D1; the
    frozen base direction is carried across a LoRA, a new prompt and a new
    position at 0.9762 against a fresh in-state probe at 0.9916)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Stage 0; the base
    KU direction fit, validated and frozen before Stage 1)
- type: evaluates_on
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/experiment.yaml (inputs;
    akariasai/PopQA test.tsv, 4-way multiple-choice rows)
- type: related_to
  target: '[[qwen]]'
  target_id: model:qwen
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/experiment.yaml (checkpoint;
    Qwen/Qwen3.5-2B-Base torso)
- type: uses
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: uses
  target: '[[conformal-prediction-for-llm-uncertainty]]'
  target_id: method:conformal-prediction-for-llm-uncertainty
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Secondary;
    split-conformal LAC sets, descriptive only)
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

Tier-2 exploratory, read-only evidence cell. A trained decision model
(Qwen3.5-2B-Base torso with a LoRA r16 adapter and a pointer head) never
refuses: it returns a temperature-calibrated softmax over the listed options at
`<answer>` and an argmax. The cell asks whether that calibrated confidence (R1)
tracks the base torso's own prior known/unknown label on PopQA 4-way
multiple-choice rows (labels from EH's knowledge-probe protocol, with the base
model as labeler), and whether the base model's frozen known-unknown (KU)
direction still reads known vs unknown in the decision model's `<answer>`
state. Stage 0 fits and freezes the base KU directions (gate at the prompt
anchor, dial at the answer end); Stage 1 scores the decision checkpoints. A
pointer arm is primary; a letter-logit arm is secondary and exploratory.

Resolved 2026-10-05 (falsified). On TEST (514 known / 4,314 unknown), primary
pointer arm:

- **H-A FAIL.** Unknown-row confidence over chance, mean(R1 - 0.25), is 0.1769
  [0.1737, 0.1798] against a 0.10 cap. The confident-wrong leg passes (0.0007).
- **H-B PASS.** Underconfident-right on known rows is 0.0603; known accuracy is
  0.969.
- **H-C PASS.** AUROC(R1 -> known) is 0.9407 [0.9266, 0.9526].
- **H-D1 PASS.** The frozen base gate direction reads the decision `<answer>`
  state at 0.9762 [0.9718, 0.9805]. Its margin over the readout is +0.0355
  [0.0245, 0.0482].
- **H-D2 PASS.** A fresh KU probe on `<answer>` states (0.9916) beats the
  readout by +0.0509 [0.0393, 0.0639].
- **Stage 0 valid.** The base gate direction reads CAL at 0.9792; its
  label-permuted twin reads 0.4901.

The interpretation-matrix cell is "readout confidence tracks the base
known-unknown axis". The readout-tracks-knowledge line is falsified on its
calibration leg (H-A), not on its ranking leg (H-C). The residual-signal and
base-axis-transfer predictions stand. The secondary letter-logit arm shows the
same verdict pattern. Detailed in
[[decision-model-readout-tracks-base-known-unknown-axis]],
[[decision-model-state-carries-more-ku-signal-than-its-readout]] and
[[decision-model-unknown-confidence-above-chance-reflects-recognition]].

Post-hoc and descriptive, not a verdict: unknown-row accuracy is 0.383 against
0.25 chance, so the H-A failure reads as recognition without recall. The
base-model "unknown" label measures failure to generate the answer, and on a
4-way choice the model can still recognize it.

Predictions scoreboard: the orchestrator's joint call (S0 passes; H-C and H-D2
pass; H-A fails on the gap leg; H-D1 passes) was realized. The user's
"blind to knowledge" readout call (H-C fails) was not realized; the "knows but
doesn't say" half (H-D1 and H-D2 pass) was. Scores are ratified in
`docs/prediction-scoreboard.md`, not here.

**Scope, binding for any write-up.** Exploratory tier-2, single seed per arm,
one 2B model, PopQA 4-way multiple choice, labels generated by the base model
itself. Reported separately from the locked headline matrix and never pooled
with it. Paper 3's numbers are context, not a matched comparison (different
family, size, population and readout). A descriptive control caution: the
frozen label-permuted direction scores decision states at 0.7632, so the H-D1
margin over arbitrary mid-depth directions is smaller than its margin over
chance.

**Lineage:** builds on [[internal-paper3--knows-but-doesnt-say]] and
[[stated-confidence-under-pstruct]] (the stated channel fails to report the
KU signal) and asks whether a decision readout, which has no verbalized
channel, does better; context for
[[verbalized-confidence-channel-bottleneck]]. Stage 0 follows the
[[rawbase-ambigqa-boundary-readout]] in-cell extract, fit and freeze pattern
and the two-signal gate/dial construction of
[[internal-twosignal-readout--training-free]]. Supersedes nothing. Source of
truth: `experiments/decision-model-calibrated-choice/AMENDMENT.md` (Outcome),
`experiments/decision-model-calibrated-choice/experiment.yaml`,
`experiments/decision-model-calibrated-choice/analysis-committed/`, resolved
2026-10-05.
