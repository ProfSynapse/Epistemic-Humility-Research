---
schema_version: research-session/v1
session_id: jspace-jlens-r1-findings
title: J-space J-lens r1 findings
status: active
created_at: '2026-07-07T22:42:40Z'
updated_at: '2026-07-08T12:05:00Z'
phase: phase1
question: What did the full-corpus Qwen3-4B J-lens characterization say about epistemic
  directions, the workspace-like band, and the L34 write layer?
tags:
- j-space
- mech-interp
run_ids:
- jspace-jlens-r1
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Mechanistic bridge work between the portable epistemic-readout
    line and the fragile activation-write line.
  changed_by_session: >-
    Localized the Qwen3-4B workspace-like band to hs=23-29
    and placed the existing L34/hs34 write layer just after the peak, making
    a mid-band write-layer sweep the immediate next actuator test. The first
    sweep stopped at G0 because dose 200 collapsed hs23/hs26, so the immediate
    successor is layer-wise dose calibration on FIT rows. During that local
    calibration, the generic tuner gained a resumable config-driven dose
    calibration verb for future cells. The FIT calibration then recovered
    usable setpoints for every layer. The calibrated held-out layer contrast
    passed on the local RTX 3090: hs23 beat hs34 by +22.7pp clean_tighten with
    only +0.78pp known-correct cost, giving surface-local causal support for
    the layer-site account.
checkpoints:
- id: 001-result
  at: '2026-07-07T22:42:40Z'
  kind: result
  title: Full-corpus J-lens characterization resolved
  summary: Modal run jspace-jlens-r1 completed on 1000 prompts; the final-layer
    smoke matched the direct unembed baseline and the H1/profile artifacts were
    committed with no prompt text.
  evidence:
  - experiments/j-space-localization-qwen3-4b/AMENDMENT.md
  - experiments/j-space-localization-qwen3-4b/NOTEBOOK.md
  - experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/PROVENANCE.md
  run_ids:
  - jspace-jlens-r1
  commands:
  - modal run experiments/j-space-localization-qwen3-4b/cloud/modal_jlens.py
  decisions: []
  next_steps: []
  signals:
    smoke_mean_cosine_sim: 0.9811106324195862
    smoke_mean_top10_overlap: 0.82
    smoke_top1_match_count: 3
    n_prompts: 1000
- id: 002-interpretation
  at: '2026-07-07T22:42:40Z'
  kind: interpretation
  title: L34 is downstream of the workspace-like peak
  summary: The profile peaked at hs=26 with a broader hs=23-29 band; L34 maps
    to hs=34, so the existing write layer sits after the apparent workspace
    peak in a late/motor-adjacent declining regime.
  evidence:
  - experiments/j-space-localization-qwen3-4b/AMENDMENT.md
  - experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/profile_full.json
  run_ids:
  - jspace-jlens-r1
  commands: []
  decisions:
  - Treat this as a characterization, not a hard confirmatory pass/fail result.
  - Promote the next actuation question to a fresh registered design before
    spending GPU on causal writes.
  next_steps:
  - Register a mid-band vs late-layer write sweep on the two-signal both-tail
    surface, prioritizing hs=23/26/29 against hs=34.
  - Compare workspace/J-lens-derived abstention injection against the existing
    residual caution write on identical selectivity gates.
  signals:
    effective_dim_peak_hs: 26
    effective_dim_peak_frac: 0.010573471754988992
    workspace_band_hs: hs=23-29
    existing_write_hs: 34
- id: 003-interpretation
  at: '2026-07-07T22:42:40Z'
  kind: interpretation
  title: Caution directions verbalize, confab propensity does not
  summary: pos_ctrl_L34 and c_hat_L34 verbalized as self/absence/error/impossibility
    tokens, u_d_L34 verbalized as answer/reply tokens, and neg_ctrl_L34 was a
    noisy local null under the J-lens.
  evidence:
  - experiments/j-space-localization-qwen3-4b/AMENDMENT.md
  - experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/h1_full.json
  run_ids:
  - jspace-jlens-r1
  commands: []
  decisions:
  - Do not describe u_d_L34 as a pure "I do not know" verbalization axis; it
    is better described as answer/readout-like under this read.
  - Keep neg_ctrl_L34 as a local null for clean J-space verbalization.
  next_steps:
  - If confab propensity remains central, refit or decompose it before assuming
    it has a single clean verbalizable workspace direction.
  signals:
    u_d_theme: answer/reply
    pos_ctrl_theme: self/absence/impossibility
    c_hat_theme: self/absence/error/impossibility
    neg_ctrl_theme: noisy-local-null
- id: 004-result
  at: '2026-07-07T23:28:42Z'
  kind: result
  title: Mid-band write sweep stopped at G0
  summary: The signed hs23/hs26/hs29/hs34 dose-200 layer sweep prepared
    successfully, but smoke collapsed every dosed hs23 and hs26 row. The full
    held-out contrast was interrupted before completion, so this is a
    pre-outcome G0 null-result rather than evidence against the J-space
    layer-site hypothesis.
  evidence:
  - experiments/j-space-midband-write-sweep-qwen3-4b/AMENDMENT.md
  - experiments/j-space-midband-write-sweep-qwen3-4b/NOTEBOOK.md
  - experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/smoke_summary.json
  run_ids:
  - jspace-midband-write-sweep-r1
  commands:
  - python3 extract_layer_sweep_anchor.py
  - python3 build_directions.py --verify-reproducible
  - python3 gate_fit.py
  - python3 pipeline.py --mode smoke --n-rows 8 --dose 200
  decisions:
  - Stop the full held-out run because G0 required zero collapse on dosed smoke
    rows.
  next_steps:
  - Register and run a layer-wise dose calibration on FIT rows only before any
    held-out layer contrast.
  signals:
    hs23_collapse_on_dosed: 1.0
    hs26_collapse_on_dosed: 1.0
    hs29_collapse_on_dosed: 0.0
    hs34_collapse_on_dosed: 0.0
    hs23_readback_mean: 200.01800448639005
    hs26_readback_mean: 199.98736937793728
    hs29_readback_mean: 200.02690423151944
    hs34_readback_mean: 200.11175295058638
- id: 005-decision
  at: '2026-07-07T23:28:42Z'
  kind: decision
  title: Signed FIT-only dose calibration successor
  summary: Created and signed `j-space-midband-dose-calibration-qwen3-4b` to
    find layer-specific non-collapsing setpoints on FIT rows. Held-out rows stay
    untouched until a later calibrated layer contrast.
  evidence:
  - experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md
  - experiments/j-space-midband-dose-calibration-qwen3-4b/experiment.yaml
  run_ids:
  - jspace-midband-dose-calibration-r1
  commands:
  - bin/exp sign j-space-midband-dose-calibration-qwen3-4b
  decisions:
  - Do not reinterpret the dose-200 G0 stop as a behavioral mid-band null.
  - Treat the failed assumption as absolute-dose portability across layer sites.
  next_steps:
  - Run the signed local dose calibration after explicit local launch approval.
  - If all layers receive usable setpoints, register the calibrated held-out
    layer contrast as the next causal test.
  signals:
    dose_ladder: 25,50,75,100,125,150,175,200
    calibration_split: fit
    n_confab_fit_rows: 8
    n_known_fit_rows: 8
- id: 006-infrastructure
  at: '2026-07-08T10:34:16Z'
  kind: infrastructure
  title: Generic tuner dose-calibration verb added
  summary: Added `mechinterp dose-calibrate` to the generic synaptic-tuner
    submodule so future activation-write dose ladders can be config-driven,
    checkpoint each readout/dose/row record to JSONL, resume after crashes, and
    emit aggregate summaries and manifests without bespoke project scripts.
  evidence:
  - synaptic-tuner
  - https://github.com/ProfSynapse/Synaptic-Tuner/pull/140
  - https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/253
  run_ids: []
  commands:
  - pytest tests/mech_interp -q
  - python tuner.py mechinterp list-configs
  decisions:
  - Keep project-specific renderers, graders, row staging, and experiment
    claims outside the generic tuner; the tuner owns only the config schema,
    execution loop, checkpoint/resume semantics, and summaries.
  next_steps:
  - Use `mechinterp dose-calibrate` for the next dose-ladder cell after this
    bespoke local calibration run finishes.
  signals:
    tuner_commit: f09db5f920fc356be710f3f7b9b631eeff9ef9e4
    parent_commit: b9ce0d64
    mechinterp_tests: 157 passed
- id: 007-result
  at: '2026-07-08T10:40:26Z'
  kind: result
  title: FIT dose calibration recovered all layer setpoints
  summary: The local RTX 3090 FIT-only calibration resolved as an exploratory
    pass. All four layers had usable non-collapsing setpoints; hs23 and hs26
    recovered below the collapsed dose-200 rung.
  evidence:
  - experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md
  - experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json
  - experiment/notes/j-space-midband-dose-calibration-qwen3-4b.md
  run_ids:
  - jspace-midband-dose-calibration-r1
  commands:
  - python calibrate_dose.py --n-confab 8 --n-known 8 --doses 25 50 75 100 125 150 175 200
  - bin/exp resolve j-space-midband-dose-calibration-qwen3-4b --status resolved --verdict ...
  decisions:
  - Treat this as FIT-only dose calibration evidence, not held-out layer-site
    superiority.
  - Register the calibrated held-out hs23/hs26/hs29 vs hs34 contrast next.
  next_steps:
  - Draft and sign the calibrated held-out layer contrast using hs23=25,
    hs26=75, hs29=125, and hs34=175.
  signals:
    selected_doses:
      hs23: 25
      hs26: 75
      hs29: 125
      hs34: 175
    all_layers_have_usable_dose: true
    collapsed_at_200_recovered: true
    hs23_selected_confab_clean_tighten: 8/8
    hs26_selected_confab_clean_tighten: 8/8
    hs29_selected_confab_clean_tighten: 8/8
    hs34_selected_confab_clean_tighten: 7/8
- id: 008-decision
  at: '2026-07-08T11:05:00Z'
  kind: decision
  title: Calibrated held-out layer contrast signed
  summary: Signed `j-space-calibrated-layer-contrast-qwen3-4b` as the held-out
    causal contrast using the FIT-selected setpoints hs23=25, hs26=75,
    hs29=125, and hs34=175. The run is not launched; local RTX 3090 launch
    still requires explicit approval for this exact signed cell.
  evidence:
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/experiment.yaml
  run_ids: []
  commands:
  - bin/exp sign j-space-calibrated-layer-contrast-qwen3-4b
  - bin/exp validate
  - bin/exp regen
  decisions:
  - Keep this as exploratory Tier-2 held-out evidence, not a headline claim.
  - Do not start the local GPU run without a fresh exact launch approval.
  next_steps:
  - On approval, run the smoke command first; if G0 passes, run full mode with
    `--i-know-this-is-the-held-out-run`.
  signals:
    expected_selected_doses:
      hs23: 25
      hs26: 75
      hs29: 125
      hs34: 175
- id: 009-result
  at: '2026-07-08T12:05:00Z'
  kind: result
  title: Calibrated held-out layer contrast passed
  summary: The local RTX 3090 smoke and full held-out run resolved as an
    exploratory pass. Best mid-band was hs23, which beat hs34 clean_tighten by
    22.7pp with only +0.78pp known-correct cost; hs34 remained viable.
  evidence:
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/analysis-committed/full_summary.json
  run_ids:
  - jspace-calibrated-layer-contrast-r1
  commands:
  - PYTHONPATH=synaptic-tuner python experiments/j-space-calibrated-layer-contrast-qwen3-4b/run_contrast.py --mode smoke --n-rows 8
  - PYTHONPATH=synaptic-tuner python experiments/j-space-calibrated-layer-contrast-qwen3-4b/run_contrast.py --mode full --i-know-this-is-the-held-out-run
  decisions:
  - Treat this as exploratory surface-local causal support, not a headline
    confirmatory claim.
  - Future contrast cells should prefer the generic tuner checkpoint/resume
    path when feasible; this bespoke runner wrote only an end-of-run aggregate.
  next_steps:
  - "Decide the replication surface for the mid-band advantage: same-model rerun, cross-family, or the two-signal surface."
  signals:
    n_rows: 443
    selected_doses:
      hs23: 25
      hs26: 75
      hs29: 125
      hs34: 175
    best_mid_layer: hs23
    hs23_confab_clean_tighten: 165/185 = 89.2%
    hs34_confab_clean_tighten: 123/185 = 66.5%
    tighten_delta_best_mid_minus_hs34_pp: 22.7
    hs23_known_correct_cost: 9/258 = 3.5%
    hs34_known_correct_cost: 7/258 = 2.7%
    cost_delta_best_mid_minus_hs34_pp: 0.78
    g1_midband_superiority_pass: true
    g2_no_cost_regression_pass: true
    g3_predecessor_reference_viable_pass: true
---
# J-space J-lens r1 findings

## Question

What did the full-corpus Qwen3-4B J-lens characterization say about epistemic directions, the workspace-like band, and the L34 write layer?

## Trajectory Position

This session sits in the mechanistic bridge between the portable readout line
and the fragile activation-write line. The motivating question was whether the
J-space/global-workspace framing could explain why epistemic directions are easy
to read but hard to write into behavior.

## Summary

The full-corpus Qwen3-4B J-lens run resolved the cheap H1 characterization. The
instrument smoke passed: final-layer J-lens readouts matched the direct unembed
baseline with mean cosine 0.9811, mean top-10 overlap 0.82, and 3/5 top-1
matches over 1000 prompts.

The H1 verbalization split is interpretable but not the naive "all uncertainty
tokens" story. `pos_ctrl_L34` and `c_hat_L34` are J-space-verbalizable as
self/absence/error/impossibility directions. `u_d_L34` is answer/reply-like,
especially around `答案` and `回答`, so it looks more like an answer/readout
axis than an explicit abstention phrase. `neg_ctrl_L34` is a noisy local null.

The layer profile is the bigger planning result. The workspace-like
effective-dimensionality bump centers on hs=23-29 and peaks at hs=26. Our
existing L34 direction layer maps to hs=34, just after that bump. This makes the
next causal question sharp: if actuation has been fragile because we wrote too
late, mid-band writes at hs=23/26/29 should beat or at least differ cleanly from
the L34/hs34 write.

The first causal successor exposed a prior assumption rather than resolving the
layer question: dose 200 transferred to hs29/hs34 smoke but collapsed hs23/hs26.
That makes layer-wise dose calibration the immediate next step. Held-out
mid-band superiority remains untested until setpoints are chosen on FIT rows.

While that local calibration was running, the generic tuner gained a
config-driven `mechinterp dose-calibrate` verb. Future dose ladders should use
that path: it writes each readout/dose/row result as an immediate checkpoint,
resumes by completed triples, and summarizes from the durable JSONL rather than
holding all metrics in memory.

The FIT-only dose calibration then passed: hs23 selected 25, hs26 selected 75,
hs29 selected 125, and hs34 selected 175. This narrows the predecessor failure to
dose portability and leaves the layer-site hypothesis alive, but it still does
not test held-out mid-band superiority.

The held-out contrast resolved as an exploratory pass. Smoke G0 passed, then
the full local RTX 3090 run completed over 443 held-out rows. Best mid-band was
hs23: clean_tighten 165/185 = 89.2% vs hs34 123/185 = 66.5%, delta +22.7pp;
known-correct cost 9/258 = 3.5% vs hs34 7/258 = 2.7%, delta +0.78pp. G1/G2/G3
all passed and hs34 remained viable. This is surface-local causal support for
the layer-site account, not a cross-family or headline confirmatory claim.

## Checkpoints

### 001-result - Full-corpus J-lens characterization resolved

- at: `2026-07-07T22:42:40Z`
- kind: `result`
- summary: Modal run `jspace-jlens-r1` completed on 1000 prompts; the final-layer
  smoke matched the direct unembed baseline and the H1/profile artifacts were
  committed with no prompt text.
- evidence:
  - `experiments/j-space-localization-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-localization-qwen3-4b/NOTEBOOK.md`
  - `experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/PROVENANCE.md`
- signals: smoke mean cosine 0.9811106324195862; mean top-10 overlap 0.82;
  top-1 match count 3/5; n_prompts 1000.

### 002-interpretation - L34 is downstream of the workspace-like peak

- at: `2026-07-07T22:42:40Z`
- kind: `interpretation`
- summary: The profile peaked at hs=26 with a broader hs=23-29 band; L34 maps to
  hs=34, so the existing write layer sits after the apparent workspace peak in a
  late/motor-adjacent declining regime.
- evidence:
  - `experiments/j-space-localization-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/profile_full.json`
- decisions:
  - Treat this as a characterization, not a hard confirmatory pass/fail result.
  - Promote the next actuation question to a fresh registered design before GPU
    causal writes.
- next steps:
  - Register a mid-band vs late-layer write sweep on the two-signal both-tail
    surface, prioritizing hs=23/26/29 against hs=34.
  - Compare workspace/J-lens-derived abstention injection against the existing
    residual caution write on identical selectivity gates.

### 003-interpretation - Caution directions verbalize, confab propensity does not

- at: `2026-07-07T22:42:40Z`
- kind: `interpretation`
- summary: `pos_ctrl_L34` and `c_hat_L34` verbalized as self/absence/error/
  impossibility tokens, `u_d_L34` verbalized as answer/reply tokens, and
  `neg_ctrl_L34` was a noisy local null under the J-lens.
- evidence:
  - `experiments/j-space-localization-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/h1_full.json`
- decisions:
  - Do not describe `u_d_L34` as a pure abstention phrase axis.
  - Keep `neg_ctrl_L34` as a local null for clean J-space verbalization.
- next steps:
  - If confab propensity remains central, refit or decompose it before assuming
    it has a single clean verbalizable workspace direction.

### 004-result - Mid-band write sweep stopped at G0

- at: `2026-07-07T23:28:42Z`
- kind: `result`
- summary: The signed hs23/hs26/hs29/hs34 dose-200 layer sweep prepared
  successfully, but smoke collapsed every dosed hs23 and hs26 row. The full
  held-out contrast was interrupted before completion, so this is a pre-outcome
  G0 null-result rather than evidence against the J-space layer-site hypothesis.
- evidence:
  - `experiments/j-space-midband-write-sweep-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-midband-write-sweep-qwen3-4b/NOTEBOOK.md`
  - `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/smoke_summary.json`
- decisions:
  - Stop the full held-out run because G0 required zero collapse on dosed smoke
    rows.
- next steps:
  - Register and run a layer-wise dose calibration on FIT rows only before any
    held-out layer contrast.

### 005-decision - Signed FIT-only dose calibration successor

- at: `2026-07-07T23:28:42Z`
- kind: `decision`
- summary: Created and signed `j-space-midband-dose-calibration-qwen3-4b` to
  find layer-specific non-collapsing setpoints on FIT rows. Held-out rows stay
  untouched until a later calibrated layer contrast.
- evidence:
  - `experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-midband-dose-calibration-qwen3-4b/experiment.yaml`
- decisions:
  - Do not reinterpret the dose-200 G0 stop as a behavioral mid-band null.
  - Treat the failed assumption as absolute-dose portability across layer sites.
- next steps:
  - Run the signed local dose calibration.
  - If all layers receive usable setpoints, register the calibrated held-out
    layer contrast as the next causal test.

### 006-infrastructure - Generic tuner dose-calibration verb added

- at: `2026-07-08T10:34:16Z`
- kind: `infrastructure`
- summary: Added `mechinterp dose-calibrate` to the generic synaptic-tuner
  submodule so future activation-write dose ladders can be config-driven,
  checkpoint each readout/dose/row record to JSONL, resume after crashes, and
  emit aggregate summaries/manifests without bespoke project scripts.
- evidence:
  - `synaptic-tuner`
  - `https://github.com/ProfSynapse/Synaptic-Tuner/pull/140`
  - `https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/253`
- commands:
  - `pytest tests/mech_interp -q`
  - `python tuner.py mechinterp list-configs`
- decisions:
  - Keep project-specific renderers, graders, row staging, and experiment claims
    outside the generic tuner.
- next steps:
  - Use `mechinterp dose-calibrate` for the next dose-ladder cell after this
    bespoke local calibration run finishes.

### 007-result - FIT dose calibration recovered all layer setpoints

- at: `2026-07-08T10:40:26Z`
- kind: `result`
- summary: The local RTX 3090 FIT-only calibration resolved as an exploratory
  pass. All four layers had usable non-collapsing setpoints; hs23 and hs26
  recovered below the collapsed dose-200 rung.
- evidence:
  - `experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json`
  - `experiment/notes/j-space-midband-dose-calibration-qwen3-4b.md`
- signals: selected doses hs23=25, hs26=75, hs29=125, hs34=175; all layers have
  usable doses; dose-200 collapse recovered for hs23/hs26; selected-dose
  clean_tighten was hs23 8/8, hs26 8/8, hs29 8/8, hs34 7/8.
- next steps:
  - Draft and sign the calibrated held-out layer contrast using hs23=25,
    hs26=75, hs29=125, and hs34=175.

### 008-decision - Calibrated held-out layer contrast signed

- at: `2026-07-08T11:05:00Z`
- kind: `decision`
- summary: Signed `j-space-calibrated-layer-contrast-qwen3-4b` as the held-out
  causal contrast using the FIT-selected setpoints hs23=25, hs26=75, hs29=125,
  and hs34=175. The run is not launched; local RTX 3090 launch still requires
  explicit approval for this exact signed cell.
- evidence:
  - `experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-calibrated-layer-contrast-qwen3-4b/experiment.yaml`
- commands:
  - `bin/exp sign j-space-calibrated-layer-contrast-qwen3-4b`
  - `bin/exp validate`
  - `bin/exp regen`
- decisions:
  - Keep this as exploratory Tier-2 held-out evidence, not a headline claim.
  - Do not start the local GPU run without a fresh exact launch approval.
- next steps:
  - On approval, run the smoke command first; if G0 passes, run full mode with
    `--i-know-this-is-the-held-out-run`.

### 009-result - Calibrated held-out layer contrast passed

- at: `2026-07-08T12:05:00Z`
- kind: `result`
- summary: The local RTX 3090 smoke and full held-out run resolved as an
  exploratory pass. Best mid-band was hs23, which beat hs34 clean_tighten by
  22.7pp with only +0.78pp known-correct cost; hs34 remained viable.
- evidence:
  - `experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-calibrated-layer-contrast-qwen3-4b/analysis-committed/full_summary.json`
- commands:
  - `PYTHONPATH=synaptic-tuner python experiments/j-space-calibrated-layer-contrast-qwen3-4b/run_contrast.py --mode smoke --n-rows 8`
  - `PYTHONPATH=synaptic-tuner python experiments/j-space-calibrated-layer-contrast-qwen3-4b/run_contrast.py --mode full --i-know-this-is-the-held-out-run`
- decisions:
  - Treat this as exploratory surface-local causal support, not a headline
    confirmatory claim.
  - Future contrast cells should prefer the generic tuner checkpoint/resume path
    where feasible; this bespoke runner wrote only an end-of-run aggregate.
- signals: n=443; selected doses hs23=25, hs26=75, hs29=125, hs34=175; hs23
  clean_tighten 165/185 = 89.2%; hs34 clean_tighten 123/185 = 66.5%; delta
  +22.7pp; hs23 known-correct cost 9/258 = 3.5%; hs34 cost 7/258 = 2.7%; delta
  +0.78pp; G1/G2/G3 all passed.
- next steps:
  - Decide the replication surface for the mid-band advantage: same-model rerun,
    cross-family, or the two-signal surface.
