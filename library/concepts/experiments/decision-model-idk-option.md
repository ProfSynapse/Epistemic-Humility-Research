---
title: decision-model-idk-option
aliases:
- Decision-model IDK option (dmio)
- 'Does an untrained decision model pick an explicit "I don''t know" option when the base torso truly does not know?'
- Explicit IDK option vs calibrated-confidence threshold abstention on PopQA
- Decision model IDK option under-used on unknown-and-unrecognized questions
- Adding an I don't know option to a never-refusing decision readout
tags:
- kg/experiment
- experiment
- abstention
- calibration
- known-unknown-readout
kg:
  id: experiment:decision-model-idk-option
  type: experiment
  status: canonical
  recorded_at: 2026-10-06
related:
- '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
- '[[decision-model-confidence-threshold-abstention-beats-idk-option]]'
- '[[decision-model-letter-logit-idk-use-is-position-dependent]]'
- '[[base-recognition-explains-decision-model-unknown-row-accuracy]]'
- '[[pretrain-only-base-readout]]'
- '[[extra-option-structurally-triggers-abstention]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[idk-switch]]'
- '[[false-option-rejection]]'
- '[[abstention]]'
- '[[over-abstention]]'
- '[[selective-prediction]]'
- '[[idk-sft]]'
- '[[popqa]]'
- '[[qwen]]'
- '[[temperature-scaling]]'
- '[[abstention-recall]]'
- '[[abstention-rate]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
relationships:
- type: builds_on
  target: '[[pretrain-only-base-readout]]'
  target_id: experiment:pretrain-only-base-readout
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md (Relationship to existing
    protocols; the base-model recognition stage uses Amendment Y's base-mode
    5-shot surface in multiple-choice form, exemplars byte-identical)
- type: supports
  target: '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
  target_id: mechanism:decision-model-idk-option-under-used-despite-tracking-unknowns
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/experiment.yaml (verdict field)
  - experiments/decision-model-idk-option/analysis-committed/dmio-pointer_gate_summary.json
    (gates h1, h2; interpretation; secondary per_group, idk_distribution_calibration)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Gate results;
    Interpretation matrix; Secondary)
- type: supports
  target: '[[decision-model-confidence-threshold-abstention-beats-idk-option]]'
  target_id: mechanism:decision-model-confidence-threshold-abstention-beats-idk-option
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/analysis-committed/dmio-pointer_gate_summary.json
    (gate h3; secondary test_matched_comparison, threshold_curve)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Gate results, H3
    detail; Falsifier adjudication; Caveats, H3 operating point)
- type: supports
  target: '[[decision-model-letter-logit-idk-use-is-position-dependent]]'
  target_id: mechanism:decision-model-letter-logit-idk-use-is-position-dependent
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/analysis-committed/dmio-letter_logits_gate_summary.json
    (gates h1, h2, h3; secondary position_bias, position_bias_caveat_h1_h2)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Caveats and
    sensitivities, position bias)
- type: supports
  target: '[[base-recognition-explains-decision-model-unknown-row-accuracy]]'
  target_id: mechanism:base-recognition-explains-decision-model-unknown-row-accuracy
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/analysis-committed/dmio-pointer_gate_summary.json
    (gate h4; secondary per_group, unknown_true_breakdown)
  - experiments/decision-model-idk-option/analysis-committed/recognition_freeze.json
    (r0, groups_by_split, chance_reference)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Secondary, chance
    reference; post-hoc and descriptive, no gate)
- type: related_to
  target: '[[extra-option-structurally-triggers-abstention]]'
  target_id: mechanism:extra-option-structurally-triggers-abstention
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Gate results; an
    added IDK option is rarely picked by the untrained pointer model, 0.0066 to
    0.0253 across groups, the opposite of the literature's extra-option
    abstention lift on large instruct models; different models, task and
    readout, so context only)
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md (Motivation and posture; a
    decision model has no verbalized channel and cannot refuse unless an option
    is listed)
- type: different_from
  target: '[[idk-switch]]'
  target_id: term:idk-switch
  confidence: high
  note: "The IDK option here is a closed-class option line added at analysis time to a decision model's choice list. It is not the IDK switch, the validated Qwen3.5-4B causal write actuator; the cell reserves that name per papers/common/terminology.md."
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md (Design, The intervention)
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md (Design, The
    intervention; an explicit IDK option in a forced-choice setting)
- type: studies
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: studies
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (H2 over-IDK on
    known questions; H3 matched over-abstention check)
- type: studies
  target: '[[selective-prediction]]'
  target_id: term:selective-prediction
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (H3 threshold
    abstention; Secondary, threshold curve)
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Follow-up
    directions; train with IDK as a gold answer, not run here)
- type: evaluates_on
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/experiment.yaml (inputs; dmcc's PopQA
    4-way decision rows and split, reused unchanged)
- type: related_to
  target: '[[qwen]]'
  target_id: model:qwen
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/experiment.yaml (checkpoint;
    Qwen/Qwen3.5-2B-Base torso)
- type: uses
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: high
- type: measures
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
  confidence: high
- type: measures
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: measures
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

Tier-2 exploratory, read-only evidence cell. It reuses the two
`decision-model-calibrated-choice` (dmcc) decision models (Qwen3.5-2B-Base
torso with a LoRA r16 adapter; pointer head PRIMARY, letter-logit head
SECONDARY) with no further training. At analysis time it adds one option line,
"I don't know", to every PopQA 4-way question. Each question is run five times,
with the option at each position, and its IDK rate is the mean of the five
picks. A new base-model recognition instrument (no adapter; 4 cyclic option
orderings; c = number of orderings in which the base picks gold) splits dmcc's
unknown rows into unknown-true (c = 0), known-recognized (c >= 3) and
recognition-ambiguous (c in 1 to 2). The cell asks whether the models pick IDK
on unknown-true questions and not on known ones. It also asks whether the
option beats a calibrated-confidence threshold at matched over-abstention.

Resolved 2026-10-06 (falsified). Recognition instrument valid (V1 positive
control 0.9227 [0.9070, 0.9360] against 0.80; V2 letter-format adherence
1.0000). On TEST (known 514, unknown-true 1,860, known-recognized 1,283),
primary pointer arm:

- **H1 FAIL.** Mean question IDK rate on unknown-true is 0.0185
  [0.0138, 0.0238] against 0.50.
- **H2 PASS.** Over-IDK on known is 0.0066 [0.0012, 0.0140] against a 0.10 cap.
- **H3 THRESHOLD_BETTER.** At matched over-abstention (check 0.0031
  [-0.0074, 0.0140]), a CAL-fit confidence threshold (tau 0.3354) abstains on
  0.1849 of unknown-true questions against 0.0185 for the option, delta -0.1665
  [-0.1848, -0.1480].
- **H4 (descriptive).** Known-recognized IDK rate is 0.0235, with answered
  accuracy 0.6391.

The interpretation-matrix cell is "IDK under-used: the model keeps answering on
true unknowns", on both arms. Both registered lines are falsified: the
selective-IDK-use line on its recall leg (H1), not its cost leg (H2), and the
IDK-beats-threshold line on H3. Secondary letter-logit arm: H1 FAIL (0.3254),
H2 PASS (0.0230), H3 NOT-ADJUDICABLE (operating points not matched), with a
flagged IDK position effect. Detailed in
[[decision-model-idk-option-under-used-despite-tracking-unknowns]],
[[decision-model-confidence-threshold-abstention-beats-idk-option]],
[[decision-model-letter-logit-idk-use-is-position-dependent]] and
[[base-recognition-explains-decision-model-unknown-row-accuracy]].

Post-hoc and descriptive, not a verdict: pointer answered accuracy on
unknown-true is 0.2168 [0.1989, 0.2346], below the 0.25 four-option chance
level. This is consistent with the c = 0 selection picking rows whose
distractor lures the shared torso.

Predictions scoreboard: the orchestrator's over-IDK, known-recognized and
"threshold better" calls were realized; its IDK-recall call ("sometimes") and
all of the PI's calls except known-recognized were not. Scores are ratified in
`docs/prediction-scoreboard.md`, not here.

**Scope, binding for any write-up.** Exploratory tier-2, no training, one
checkpoint per arm, one 2B model, PopQA 4-way multiple choice plus an IDK
option, known/unknown labels and recognition both from the base model. Reported
separately from the locked headline matrix and never pooled with it.
Confirmatory claims rest on the pointer arm alone. The H3 operating point is
very low (about 1% over-abstention; tau fit from 1 of 268 CAL known questions
and held fixed in the bootstrap). The no-IDK arm reproduces dmcc's TEST outputs
exactly.

**Lineage:** follows up dmcc (`experiment:decision-model-calibrated-choice`,
not yet on main when this node was written), whose post-hoc reading of its
H-A failure (recognition without recall) motivated the recognition
instrument. The recognition stage uses the base-mode surface of
[[pretrain-only-base-readout]] (Amendment Y). The near-zero IDK use contrasts
with the extra-option abstention lift in
[[extra-option-structurally-triggers-abstention]]. The "IDK option" is
an option line, not the [[idk-switch]] actuator. Supersedes
nothing; dmcc's verdicts are not revisited. Source of truth:
`experiments/decision-model-idk-option/AMENDMENT.md` (Outcome),
`experiments/decision-model-idk-option/experiment.yaml`,
`experiments/decision-model-idk-option/analysis-committed/`, resolved
2026-10-06.
