---
schema_version: research-session/v1
session_id: 20260806T115256Z-grpo-three-seed-confirmatory-seed-3-chain-and-g1-adjudication
title: 'GRPO three-seed confirmatory: seed-3 chain and G1 adjudication'
status: active
created_at: '2026-08-06T11:52:56Z'
updated_at: '2026-08-07T09:34:16Z'
question: Does the seed-1 GRPO abstention shift replicate across seeds 2 and 3 (G1,
  primary falsifier), and does post-GRPO preference recovery replicate (G2)?
tags:
- grpo
- replication
- seed3
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-result
  at: '2026-08-06T11:53:05Z'
  kind: result
  title: Result
  summary: 'G1 ADJUDICATED PASS on both seeds; primary falsifier survived. Seed-3
    grpo_v2 vs same-seed base: answer_on_unknown 11.72->4.94 (-6.78pp), refusal_recall
    88.28->95.06 (+6.78pp), against a band pre-stated at 8.72/91.28 hours before the
    run existed. Seed 2: -4.36/+4.36. Both clear the 3.0pp floor. G0 PASS on seed-3
    clean_sft, dpo, kto, grpo_v2. NOTE the two G1 metrics are exact complements (sum
    to 100.00 in all 21 runs of this block), so G1 is ONE direction-plus-floor test
    passed in two seeds, not two corroborating findings; must not be written up as
    two. Cost recorded alongside the pass: over_refusal rose +8.51pp (seed 2) and
    +9.67pp (seed 3), MORE than the abstention gain, and truthful_pct is nearly flat
    (+0.18, +0.53).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-validation
  at: '2026-08-06T11:53:36Z'
  kind: validation
  title: Validation
  summary: 'INSTRUMENT ARTIFACT, confirmed from source and lead-re-derived: correct_on_known_pct
    is correct_known/answered_known (scorers.py:287), a FILTERED denominator excluding
    refused known rows (answered_known incremented at :268). Seed-3 base->grpo_v2:
    answered_known 958->732 (-23.6%), correct_known 455->403 (-11.4%), so the rate
    ROSE 47.49->55.05 (+7.56pp) while the same numerator over ALL known rows FELL
    19.47->17.24 (-2.23pp). The metric reports improvement for a model that got 52
    fewer questions right. BLOCKED from any write-up unless quoted with its denominator
    and raw count. G1 unaffected: refusal_recall_pct (:281), answer_on_unknown_pct
    (:282-284), over_refusal_pct (:285) all use unconditional full-class denominators,
    so the +9.67pp over-refusal cost is real and comparable. truthful_pct (:289) sums
    raw counts over fixed n; its flatness is forced cancellation (+70/-52 rows seed
    3, +45/-39 seed 2), NOT absence of effect. Labels are SelfAware ground-truth answerability
    (ood.py:131), label_from_target False, no oracle leak.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-recovery
  at: '2026-08-06T11:53:36Z'
  kind: recovery
  title: Recovery
  summary: 'clean_sft_dpo_grpo seed 3 crashed exit 139 (SIGSEGV) at step 150/1861,
    torch.AcceleratorError cudaErrorUnknown, OOMKilled=false. Second CUDA fault on
    this WSL2 host in two days (same signature as seed-3 stage-1). Capacity ruled
    out BY COMPARISON: crashed at 49.06% VRAM peak while seed 2 ran the same arm to
    1861/1861 at 82.60%. G0 training_completed_clean FAILS, instrument stop, no outcome
    read. Relaunching from scratch, deliberately NOT --resume-from-checkpoint, because
    a resumed optimizer trajectory is not how seeds 1-2 were produced and this arm
    feeds the cross-seed G3 matrix. Watch-trap note: the background wait task summary
    again reported ''exit code 0'' while the container exited 139; the real code came
    from the watch output file and docker inspect.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Relaunch dpo_grpo, then kto_grpo, then grpo_dpo (closes G2), then grpo_kto, in
    registered launch_order. PR 394 open.
  signals: {}
- id: 004-checkpoint
  at: '2026-08-07T09:34:16Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Block RESOLVED and merged (PR #397): G2 adjudicated PASS both seeds against
    pre-stated band; grpo_kto final arm closed G0 PASS (chain 8/8); G3 intervals delivered
    (seed-level bootstrap, script pinned); red-team pass SAFE TO RESOLVE with two
    MAJOR accepted findings: (1) 117 SelfAware known questions verbatim in training
    prompts (G1 structurally immune, G2 stratum-robust, absolute known-row levels
    caveated, guard-extension follow-up), (2) G5 delivered with DPO-pair sign reversal
    (KTO pair holds). G4 not triggered (max 85 distinct). bin/exp repin correctly
    refused post-resolution gates.yaml header fix; defect ruled cosmetic, machine
    state authoritative. KG ingest in flight on branch kg/grpo-three-seed-ingest.
    Clean-subset sensitivity re-aggregation dispatched (PI-approved): decontaminated
    metrics for all 16 runs as paper-2 sensitivity table, gates unchanged. Next GPU
    run launched with PI approval: headline-seed1-postfix-rerun DPO cell dispatched
    (cold-start seed 1, post-fix build sha 39e2ba8c, trainer pinned 089fa9b7, worktree
    postfix-rerun).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
track: grpo-three-seed-confirmatory
---
# GRPO three-seed confirmatory: seed-3 chain and G1 adjudication

## Question

Does the seed-1 GRPO abstention shift replicate across seeds 2 and 3 (G1, primary falsifier), and does post-GRPO preference recovery replicate (G2)?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-result - Result

- at: `2026-08-06T11:53:05Z`
- kind: `result`
- summary: G1 ADJUDICATED PASS on both seeds; primary falsifier survived. Seed-3 grpo_v2 vs same-seed base: answer_on_unknown 11.72->4.94 (-6.78pp), refusal_recall 88.28->95.06 (+6.78pp), against a band pre-stated at 8.72/91.28 hours before the run existed. Seed 2: -4.36/+4.36. Both clear the 3.0pp floor. G0 PASS on seed-3 clean_sft, dpo, kto, grpo_v2. NOTE the two G1 metrics are exact complements (sum to 100.00 in all 21 runs of this block), so G1 is ONE direction-plus-floor test passed in two seeds, not two corroborating findings; must not be written up as two. Cost recorded alongside the pass: over_refusal rose +8.51pp (seed 2) and +9.67pp (seed 3), MORE than the abstention gain, and truthful_pct is nearly flat (+0.18, +0.53).
### 002-validation - Validation

- at: `2026-08-06T11:53:36Z`
- kind: `validation`
- summary: INSTRUMENT ARTIFACT, confirmed from source and lead-re-derived: correct_on_known_pct is correct_known/answered_known (scorers.py:287), a FILTERED denominator excluding refused known rows (answered_known incremented at :268). Seed-3 base->grpo_v2: answered_known 958->732 (-23.6%), correct_known 455->403 (-11.4%), so the rate ROSE 47.49->55.05 (+7.56pp) while the same numerator over ALL known rows FELL 19.47->17.24 (-2.23pp). The metric reports improvement for a model that got 52 fewer questions right. BLOCKED from any write-up unless quoted with its denominator and raw count. G1 unaffected: refusal_recall_pct (:281), answer_on_unknown_pct (:282-284), over_refusal_pct (:285) all use unconditional full-class denominators, so the +9.67pp over-refusal cost is real and comparable. truthful_pct (:289) sums raw counts over fixed n; its flatness is forced cancellation (+70/-52 rows seed 3, +45/-39 seed 2), NOT absence of effect. Labels are SelfAware ground-truth answerability (ood.py:131), label_from_target False, no oracle leak.
### 003-recovery - Recovery

- at: `2026-08-06T11:53:36Z`
- kind: `recovery`
- summary: clean_sft_dpo_grpo seed 3 crashed exit 139 (SIGSEGV) at step 150/1861, torch.AcceleratorError cudaErrorUnknown, OOMKilled=false. Second CUDA fault on this WSL2 host in two days (same signature as seed-3 stage-1). Capacity ruled out BY COMPARISON: crashed at 49.06% VRAM peak while seed 2 ran the same arm to 1861/1861 at 82.60%. G0 training_completed_clean FAILS, instrument stop, no outcome read. Relaunching from scratch, deliberately NOT --resume-from-checkpoint, because a resumed optimizer trajectory is not how seeds 1-2 were produced and this arm feeds the cross-seed G3 matrix. Watch-trap note: the background wait task summary again reported 'exit code 0' while the container exited 139; the real code came from the watch output file and docker inspect.
- next steps:
  - Relaunch dpo_grpo, then kto_grpo, then grpo_dpo (closes G2), then grpo_kto, in registered launch_order. PR 394 open.
### 004-checkpoint - Checkpoint

- at: `2026-08-07T09:34:16Z`
- kind: `checkpoint`
- summary: Block RESOLVED and merged (PR #397): G2 adjudicated PASS both seeds against pre-stated band; grpo_kto final arm closed G0 PASS (chain 8/8); G3 intervals delivered (seed-level bootstrap, script pinned); red-team pass SAFE TO RESOLVE with two MAJOR accepted findings: (1) 117 SelfAware known questions verbatim in training prompts (G1 structurally immune, G2 stratum-robust, absolute known-row levels caveated, guard-extension follow-up), (2) G5 delivered with DPO-pair sign reversal (KTO pair holds). G4 not triggered (max 85 distinct). bin/exp repin correctly refused post-resolution gates.yaml header fix; defect ruled cosmetic, machine state authoritative. KG ingest in flight on branch kg/grpo-three-seed-ingest. Clean-subset sensitivity re-aggregation dispatched (PI-approved): decontaminated metrics for all 16 runs as paper-2 sensitivity table, gates unchanged. Next GPU run launched with PI approval: headline-seed1-postfix-rerun DPO cell dispatched (cold-start seed 1, post-fix build sha 39e2ba8c, trainer pinned 089fa9b7, worktree postfix-rerun).
