---
schema_version: research-session/v1
session_id: '0031'
title: Paper reorg + SR seed-robustness + steering-scaffold merge
status: active
created_at: '2026-07-01T11:59:38Z'
updated_at: '2026-07-01T12:00:08Z'
phase: phase1
question: Are the training-free two-signal readout headline magnitudes (Z cross-family
  dial+veto) seed-robust under sampled decoding, and consolidate the paper numbering
  + merge the Paper-4 steering scaffold?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-infrastructure
  at: '2026-07-01T12:00:08Z'
  kind: infrastructure
  title: "Steering scaffold (Paper 4) reviewed + merged; Paper 5\u21924 relabel"
  summary: "Reviewed the confidence-steering scaffold from the paper5 worktree: purely\
    \ additive (10 files under experiment/phase1/probe/steering/), training-free by\
    \ construction (Arm A forward-hook activation steering h\u2190h+alpha*d; Arm B\
    \ CoT text injection; zero weight updates), 88/88 CPU tests green. Merged via\
    \ PR #137, then relabeled Paper 5\u2192Paper 4 (canonical map) via PR #138. Design\
    \ doc docs/plans/confidence-steering-experiment.md already existed on main and\
    \ was already correctly numbered (the '#137 missing plan doc' flag was a wrong-branch\
    \ false alarm). Worktrees + branches cleaned up."
  evidence:
  - experiment/phase1/probe/steering/README.md
  run_ids: []
  commands: []
  decisions:
  - Merge scaffolding to main now (user asked); training-free constraint baked in
    as a hard design rule for Paper 4; full pre-reg (gates/falsifiers) deferred until
    the steering amendment is minted.
  next_steps: []
  signals: {}
- id: 002-launch
  at: '2026-07-01T12:00:08Z'
  kind: launch
  title: Amendment SR (sampled-decode seed-robustness) pre-registered + launched
  summary: Hardens the Z headline dial+veto magnitudes against the single-greedy-decode
    confound. Identical training-free readout under SAMPLED decoding (temp 0.7/top_p
    0.9) x 3 seeds (20260701/02/03) on the 4 confirmatory families ONLY (Qwen3-4B/W
    excluded so the seed pass stays inside the confirmatory set). Scope dial+veto
    (gate is pre-gen-anchor decode-INVARIANT, emitted as invariance check). Extractor
    gained backward-compatible --do-sample/--temperature/--top-p (default greedy =
    X/Z reproduce). SUCCESS = dial 4/4 seed-stable + veto >=3/4 seed-stable + per-seed
    veto majority >=3/4 every seed. Launched 10:11 UTC local Docker unsloth-z:latest,
    single GPU sequential, 12 cells.
  evidence:
  - experiment/protocol/AMENDMENT-SR-sampled-decode-seed-robustness.md
  run_ids: []
  commands:
  - bash experiment/phase1/probe/amendment_sr_queue.sh
  decisions: []
  next_steps: []
  signals: {}
- id: 003-result
  at: '2026-07-01T12:00:08Z'
  kind: result
  title: "SR 3/12: Llama-3.2-3B veto flips greedy-FAIL \u2192 seed-stable PASS (3/3)"
  summary: "Llama-3.2-3B family complete (3 seeds). veto 0.801/0.684/0.732 = seed-stable\
    \ PASS 3/3 (mean ~0.739); dial 0.827/0.853/0.865 all PASS; gate ~0.997 all (decode-invariance\
    \ confirmed). Llama's veto was the CLEAN GREEDY FAIL (0.633) in Z \u2014 under\
    \ sampled decoding it passes on every seed, so the Z single-decode veto miss looks\
    \ like a greedy-decode artifact. n=1 family so far; not read into the locked verdict.\
    \ Ministral/Qwen3.5/Gemma-4 pending (~30 min/seed, ETA ~16:00-17:00 UTC)."
  evidence:
  - experiment/phase1/probe/sr_logs/PROGRESS.log
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - "Let the queue finish; fill AMENDMENT-SR \xA77 per-seed tables + seed-stability\
    \ roll-up + per-seed veto majority + locked verdict; refresh experiment note;\
    \ open the SR PR."
  signals: {}
---
# Paper reorg + SR seed-robustness + steering-scaffold merge

## Question

Are the training-free two-signal readout headline magnitudes (Z cross-family dial+veto) seed-robust under sampled decoding, and consolidate the paper numbering + merge the Paper-4 steering scaffold?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-infrastructure - Steering scaffold (Paper 4) reviewed + merged; Paper 5→4 relabel

- at: `2026-07-01T12:00:08Z`
- kind: `infrastructure`
- summary: Reviewed the confidence-steering scaffold from the paper5 worktree: purely additive (10 files under experiment/phase1/probe/steering/), training-free by construction (Arm A forward-hook activation steering h←h+alpha*d; Arm B CoT text injection; zero weight updates), 88/88 CPU tests green. Merged via PR #137, then relabeled Paper 5→Paper 4 (canonical map) via PR #138. Design doc docs/plans/confidence-steering-experiment.md already existed on main and was already correctly numbered (the '#137 missing plan doc' flag was a wrong-branch false alarm). Worktrees + branches cleaned up.
- evidence:
  - `experiment/phase1/probe/steering/README.md`
- decisions:
  - Merge scaffolding to main now (user asked); training-free constraint baked in as a hard design rule for Paper 4; full pre-reg (gates/falsifiers) deferred until the steering amendment is minted.
### 002-launch - Amendment SR (sampled-decode seed-robustness) pre-registered + launched

- at: `2026-07-01T12:00:08Z`
- kind: `launch`
- summary: Hardens the Z headline dial+veto magnitudes against the single-greedy-decode confound. Identical training-free readout under SAMPLED decoding (temp 0.7/top_p 0.9) x 3 seeds (20260701/02/03) on the 4 confirmatory families ONLY (Qwen3-4B/W excluded so the seed pass stays inside the confirmatory set). Scope dial+veto (gate is pre-gen-anchor decode-INVARIANT, emitted as invariance check). Extractor gained backward-compatible --do-sample/--temperature/--top-p (default greedy = X/Z reproduce). SUCCESS = dial 4/4 seed-stable + veto >=3/4 seed-stable + per-seed veto majority >=3/4 every seed. Launched 10:11 UTC local Docker unsloth-z:latest, single GPU sequential, 12 cells.
- evidence:
  - `experiment/protocol/AMENDMENT-SR-sampled-decode-seed-robustness.md`
- commands:
  - `bash experiment/phase1/probe/amendment_sr_queue.sh`
### 003-result - SR 3/12: Llama-3.2-3B veto flips greedy-FAIL → seed-stable PASS (3/3)

- at: `2026-07-01T12:00:08Z`
- kind: `result`
- summary: Llama-3.2-3B family complete (3 seeds). veto 0.801/0.684/0.732 = seed-stable PASS 3/3 (mean ~0.739); dial 0.827/0.853/0.865 all PASS; gate ~0.997 all (decode-invariance confirmed). Llama's veto was the CLEAN GREEDY FAIL (0.633) in Z — under sampled decoding it passes on every seed, so the Z single-decode veto miss looks like a greedy-decode artifact. n=1 family so far; not read into the locked verdict. Ministral/Qwen3.5/Gemma-4 pending (~30 min/seed, ETA ~16:00-17:00 UTC).
- evidence:
  - `experiment/phase1/probe/sr_logs/PROGRESS.log`
- next steps:
  - Let the queue finish; fill AMENDMENT-SR §7 per-seed tables + seed-stability roll-up + per-seed veto majority + locked verdict; refresh experiment note; open the SR PR.
