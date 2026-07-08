---
schema_version: research-session/v1
session_id: 0041-dark-dose-calibration-tuner-probe-worktree-cleanup
title: Dark-screen dose calibration, tuner firing-probe fix, worktree cleanup
status: active
created_at: '2026-07-06T20:41:08Z'
updated_at: '2026-07-06T20:42:18Z'
phase: phase1
question: Can the raw-base dark-actuator-screen run on bnb-4bit, and what dose/instrument
  fixes does it need?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-result
  at: '2026-07-06T20:42:18Z'
  kind: result
  title: AM veto is real but length-confounded; ~0.77-0.85 content signal
  summary: 'Length-controlled re-analysis of the AM post-generation veto (exploratory,
    already-peeked data, single seed): the 0.917 headline is length-inflated, but
    in length-matched bands the veto beats a length-only baseline by +0.17-0.22 AUROC
    (CI excludes 0 in all powered bands), landing ~0.74-0.86; full-population partial-out-length
    margin +0.07 CI[0.037,0.104]. Real content signal, moderate-to-good, NOT a length
    detector. Residual-only set cannot be length-matched (all-long).'
  evidence:
  - scratchpad/am_extract/length_control_result.json; AMENDMENT-AM-residual-catch-veto-coverage.md
    sec9
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Fresh pre-registered confirmatory run to quote the readout dial in a paper (length-balanced,
    position-controlled, length-only null, gates pre-stated).
  signals: {}
- id: 002-interpretation
  at: '2026-07-06T20:42:18Z'
  kind: interpretation
  title: 'Base lever: dose-escalate on pos_ctrl (initial no-window read RETRACTED)'
  summary: 'Free-3090 dose escalation with the REAL erase_write law + real pos_ctrl_L34
    on the raw base. A coarse ladder (100,500) reported ''no clean window -> base
    null''; a finer sweep RETRACTED that as a granularity artifact. True shape: inert
    -> clean coherent refusal-shift -> collapse. bnb-4bit window ~150-300 (setpoint),
    bf16 ~100; ambient ~19-27 both, so window ~7-14x ambient. Instrument valid on
    the base; write is faithful (max_write_err is write-accuracy, not perturbation
    size).'
  evidence:
  - scratchpad/dose_ladder_4bit_v2_results.json, dose_ladder_bf16_results.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-result
  at: '2026-07-06T20:42:18Z'
  kind: result
  title: 'Ambient-relative dose calibration: 12/12 confabs flip at k~7'
  summary: 'Per-prompt k*ambient sweep (24 rows) on pos_ctrl: confab rows (baseline
    answers) flip cleanly to refuse at k=5-9 (median 7), collapse only at k>=13-15;
    already-refusing rows unchanged until k>=9. So k=7 flips confabs without touching
    already-refusing rows (the selectivity G-instrument needs). Recommended screen
    ladder: ambient-relative k in {5,7,9}, strength = k*ambient/sigma per direction.
    The old absolute {1,2,4} ladder was entirely inert and would have voided the screen.'
  evidence:
  - scratchpad/ambient_relative_rows.jsonl; dark-actuator-screen/NOTEBOOK.md 2026-07-06
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-infrastructure
  at: '2026-07-06T20:42:18Z'
  kind: infrastructure
  title: 'Tuner PR #138: configurable gen_stream firing-probe strength'
  summary: The tuner gen_stream firing guard probed at a hardcoded 100.0, inert on
    bnb-4bit (window >=150), so it false-negatived and aborted every direction. Added
    optional SmokeConfig.gen_stream_probe_strength (default None -> unchanged); threaded
    into gen_stream_fires. Generic/backward-compatible. Merged tuner main 56c7c6b;
    dark-screen submodule bumped. The firing probe is a WIRING check (large over-driven
    write), NOT a dose; inert directions must not be aborted by it (they are the expected
    screen null).
  evidence:
  - 'Synaptic-Tuner PR #138 (56c7c6b); EHR PR #233 submodule bump c165db23'
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-infrastructure
  at: '2026-07-06T20:42:18Z'
  kind: infrastructure
  title: Worktree cleanup 25 -> 10; mechinterp-cells dose-calibration reference
  summary: 'Pruned 16 merged+clean worktree branches (25 -> 10 worktrees). Pushed
    dark-screen (#233) and AO (#231). Added a mechinterp-cells skill reference reference/dose-calibration.md
    (SKILL.md kept as a lean router). Remaining worktrees with unmerged work: amendment-am,
    amendment-ak (finished results, need PRs), amendment-ag/par-mining/steering-cell-skill/session-0039
    (stale, PR-or-abandon), lab-diagnostics-bundle (untracked diag data).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-handoff
  at: '2026-07-06T20:42:18Z'
  kind: handoff
  title: dark-run re-smoking with wiring-probe fix; full 34-dir screen pending
  summary: dark-run (harness-builder) is wiring smoke.gen_stream_probe_strength per
    direction as a large over-driven wiring probe (L determined empirically on the
    random control), then re-running the 3-direction G-instrument smoke (pos_ctrl
    must flip, randctrl at floor). On confirmation + lead go, the full 34-direction
    dark-actuator-screen runs on the free 3090. Screen is Tier-2 exploratory; graduates
    earn their own signed amendments.
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Confirm G-instrument on smoke -> run full 34-direction screen -> score graduation
    table.
  signals: {}
---
# Dark-screen dose calibration, tuner firing-probe fix, worktree cleanup

## Question

Can the raw-base dark-actuator-screen run on bnb-4bit, and what dose/instrument fixes does it need?

## Trajectory Position

_Not yet recorded._

## Summary

Two-track session. **Readout track:** the AM post-generation "this is likely a
hallucination" veto is a real content signal (~0.77-0.85 length-controlled, +0.07
CI-significant on the broad population), not just a length detector, but well
below its length-inflated 0.917 headline; product-viable as a soft flag, needs a
fresh pre-registered confirmatory run to claim.

**Lever track (dark-actuator-screen):** established that the raw-base bnb-4bit
substrate CAN be steered by a rank-1 erase_write, in a narrow coherent window
(inert -> clean refusal-shift -> collapse) that scales with each direction's own
ambient projection (~7-14x ambient; k in {5,7,9}), not with a fixed absolute
strength. An intermediate "base-lever null" read was a coarse-ladder granularity
artifact and was retracted. The old absolute {1,2,4} dose ladder was entirely
inert and would have voided the screen. Recalibrated the screen to
ambient-relative per-direction dosing. Fixed a genuine tuner bug (gen_stream
firing guard probed at a hardcoded 100.0, inert on bnb-4bit) via tuner PR #138
(configurable gen_stream_probe_strength) and bumped the submodule. Key instrument
point: the firing guard is a WIRING check (must use a large over-driven probe),
NOT a dose, or it would wrongly abort the screen's own inert (null) directions.

The full 34-direction screen has not run yet: it is gated on a 3-direction
G-instrument smoke (positive control must flip, random control at floor) with the
new dosing + wiring probe, in progress. Also did a worktree cleanup (25 -> 10).
The screen itself remains Tier-2 exploratory; any graduating candidate earns its
own signed amendment before any claim.

## Checkpoints
### 001-result - AM veto is real but length-confounded; ~0.77-0.85 content signal

- at: `2026-07-06T20:42:18Z`
- kind: `result`
- summary: Length-controlled re-analysis of the AM post-generation veto (exploratory, already-peeked data, single seed): the 0.917 headline is length-inflated, but in length-matched bands the veto beats a length-only baseline by +0.17-0.22 AUROC (CI excludes 0 in all powered bands), landing ~0.74-0.86; full-population partial-out-length margin +0.07 CI[0.037,0.104]. Real content signal, moderate-to-good, NOT a length detector. Residual-only set cannot be length-matched (all-long).
- evidence:
  - `scratchpad/am_extract/length_control_result.json; AMENDMENT-AM-residual-catch-veto-coverage.md sec9`
- next steps:
  - Fresh pre-registered confirmatory run to quote the readout dial in a paper (length-balanced, position-controlled, length-only null, gates pre-stated).
### 002-interpretation - Base lever: dose-escalate on pos_ctrl (initial no-window read RETRACTED)

- at: `2026-07-06T20:42:18Z`
- kind: `interpretation`
- summary: Free-3090 dose escalation with the REAL erase_write law + real pos_ctrl_L34 on the raw base. A coarse ladder (100,500) reported 'no clean window -> base null'; a finer sweep RETRACTED that as a granularity artifact. True shape: inert -> clean coherent refusal-shift -> collapse. bnb-4bit window ~150-300 (setpoint), bf16 ~100; ambient ~19-27 both, so window ~7-14x ambient. Instrument valid on the base; write is faithful (max_write_err is write-accuracy, not perturbation size).
- evidence:
  - `scratchpad/dose_ladder_4bit_v2_results.json, dose_ladder_bf16_results.json`
### 003-result - Ambient-relative dose calibration: 12/12 confabs flip at k~7

- at: `2026-07-06T20:42:18Z`
- kind: `result`
- summary: Per-prompt k*ambient sweep (24 rows) on pos_ctrl: confab rows (baseline answers) flip cleanly to refuse at k=5-9 (median 7), collapse only at k>=13-15; already-refusing rows unchanged until k>=9. So k=7 flips confabs without touching already-refusing rows (the selectivity G-instrument needs). Recommended screen ladder: ambient-relative k in {5,7,9}, strength = k*ambient/sigma per direction. The old absolute {1,2,4} ladder was entirely inert and would have voided the screen.
- evidence:
  - `scratchpad/ambient_relative_rows.jsonl; dark-actuator-screen/NOTEBOOK.md 2026-07-06`
### 004-infrastructure - Tuner PR #138: configurable gen_stream firing-probe strength

- at: `2026-07-06T20:42:18Z`
- kind: `infrastructure`
- summary: The tuner gen_stream firing guard probed at a hardcoded 100.0, inert on bnb-4bit (window >=150), so it false-negatived and aborted every direction. Added optional SmokeConfig.gen_stream_probe_strength (default None -> unchanged); threaded into gen_stream_fires. Generic/backward-compatible. Merged tuner main 56c7c6b; dark-screen submodule bumped. The firing probe is a WIRING check (large over-driven write), NOT a dose; inert directions must not be aborted by it (they are the expected screen null).
- evidence:
  - `Synaptic-Tuner PR #138 (56c7c6b); EHR PR #233 submodule bump c165db23`
### 005-infrastructure - Worktree cleanup 25 -> 10; mechinterp-cells dose-calibration reference

- at: `2026-07-06T20:42:18Z`
- kind: `infrastructure`
- summary: Pruned 16 merged+clean worktree branches (25 -> 10 worktrees). Pushed dark-screen (#233) and AO (#231). Added a mechinterp-cells skill reference reference/dose-calibration.md (SKILL.md kept as a lean router). Remaining worktrees with unmerged work: amendment-am, amendment-ak (finished results, need PRs), amendment-ag/par-mining/steering-cell-skill/session-0039 (stale, PR-or-abandon), lab-diagnostics-bundle (untracked diag data).
### 006-handoff - dark-run re-smoking with wiring-probe fix; full 34-dir screen pending

- at: `2026-07-06T20:42:18Z`
- kind: `handoff`
- summary: dark-run (harness-builder) is wiring smoke.gen_stream_probe_strength per direction as a large over-driven wiring probe (L determined empirically on the random control), then re-running the 3-direction G-instrument smoke (pos_ctrl must flip, randctrl at floor). On confirmation + lead go, the full 34-direction dark-actuator-screen runs on the free 3090. Screen is Tier-2 exploratory; graduates earn their own signed amendments.
- next steps:
  - Confirm G-instrument on smoke -> run full 34-direction screen -> score graduation table.
