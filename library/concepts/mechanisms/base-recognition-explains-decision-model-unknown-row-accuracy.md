---
title: base-recognition-explains-decision-model-unknown-row-accuracy
aliases:
- Decision model answers below chance on questions the base neither recalls nor recognizes
- Unknown-true accuracy below 4-way chance, distractor attraction
- Recognition, not recall, sets decision-model accuracy on base-unknown rows
- Generation-unknown splits into recognized and unrecognized
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:base-recognition-explains-decision-model-unknown-row-accuracy
  type: mechanism
  status: canonical
  recorded_at: 2026-10-06
cause: "In the decision-model-idk-option experiment, the base-model 'unknown' PopQA rows (0 of 32 sampled generations correct) are split by a pre-registered base-model recognition instrument (Qwen3.5-2B-Base, no adapter, Amendment Y base-mode 5-shot multiple-choice surface, 4 cyclic option orderings, c = orderings in which the base picks gold; valid: V1 positive control 0.9227 [0.9070, 0.9360], V2 format adherence 1.0000) into unknown-true (c = 0), recognition-ambiguous (c 1 to 2) and known-recognized (c >= 3), and the trained pointer decision model's answered accuracy is read per group."
effect: "Descriptive, no gate: pointer answered accuracy is 0.2168 [0.1989, 0.2346] on unknown-true (n 1,860), 0.3659 on recognition-ambiguous and 0.6391 [0.6136, 0.6643] on known-recognized (n 1,283; H4, descriptive), against 0.3825 over all dmcc-unknown rows and 0.9719 on known. Post-hoc and not pre-registered: unknown-true accuracy sits below the 0.25 four-option chance level (CI upper bound 0.2346), consistent with c = 0 selecting rows whose distractor lures the shared torso. The letter-logit arm shows the same gradient (0.1540, 0.4094, 0.7510)."
polarity: explains
related:
- '[[decision-model-idk-option]]'
- '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
- '[[pretrain-only-base-readout]]'
- '[[knowledge-boundary]]'
- '[[popqa]]'
relationships:
- type: supported_by
  target: '[[decision-model-idk-option]]'
  target_id: experiment:decision-model-idk-option
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/analysis-committed/dmio-pointer_gate_summary.json
    (gate h4; secondary per_group, unknown_true_breakdown)
  - experiments/decision-model-idk-option/analysis-committed/recognition_freeze.json
    (r0, groups_by_split, c_distribution, chance_reference)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Recognition,
    populations and G0; Secondary, per group and chance reference)
- type: related_to
  target: '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
  target_id: mechanism:decision-model-idk-option-under-used-despite-tracking-unknowns
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (on unknown-true
    the model answers 0.98 of the time and is wrong on 0.7696)
- type: derived_from
  target: '[[pretrain-only-base-readout]]'
  target_id: experiment:pretrain-only-base-readout
  confidence: medium
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md (Relationship to existing
    protocols; recognition prompts use Amendment Y's base-mode surface)
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
---

A base-model "unknown" label (cannot generate the answer) is not one
population. Split by whether the base model can pick the answer from four
options, the decision model's accuracy runs from 0.22 on unrecognized rows to
0.64 on recognized ones. The pooled unknown-row figure, 0.38, mixes the two.
On rows the base neither recalls nor recognizes, accuracy is slightly below
chance, which fits a distractor that attracts the shared torso.

**Why it matters here:** this is a direct, registered-instrument check on the
predecessor cell's post-hoc reading of its H-A failure (recognition without
recall) in `decision-model-calibrated-choice`. Removing recognized rows removes
the above-chance accuracy. A "truly unknown" population for a multiple-choice
readout needs a recognition cut, not only a recall cut.

**Caveats:** the per-group accuracies are registered descriptive outputs; the
below-chance reading and the distractor-attraction explanation are post-hoc and
change no verdict. c = 0 is partly a chance event (P(c = 0) under uniform
guessing is 0.3164), so unknown-true also absorbs rows where the base guessed
wrong four times. Exploratory tier-2, no training, one checkpoint per arm, one
2B model, PopQA 4-way multiple choice. Source of truth:
`experiments/decision-model-idk-option/AMENDMENT.md` (Outcome), resolved
2026-10-06.
