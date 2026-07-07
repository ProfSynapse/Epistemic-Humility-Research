---
schema_version: research-session/v1
session_id: jspace-jlens-r1-findings
title: J-space J-lens r1 findings
status: complete
created_at: '2026-07-07T22:42:40Z'
updated_at: '2026-07-07T22:42:40Z'
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
  changed_by_session: Localized the Qwen3-4B workspace-like band to hs=23-29
    and placed the existing L34/hs34 write layer just after the peak, making
    a mid-band write-layer sweep the immediate next actuator test.
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
