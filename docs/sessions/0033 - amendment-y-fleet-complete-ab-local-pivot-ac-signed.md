---
schema_version: research-session/v1
session_id: '0033'
title: Amendment Y fleet complete (H_B1 4/4) + AB cloud-to-local pivot + Amendment AC signed
status: active
created_at: '2026-07-02T18:00:00Z'
updated_at: '2026-07-02T23:55:00Z'
phase: phase1
question: Does the two-signal readout predate post-training (Y)? Can AB V1 run at all
  on the HF cloud lane, and what is the fallback? Can the doubt readout REGULATE the
  caution write (AC, PHASE3 RQ4 Stage 1)?
tags:
- experiment-runner
- paper4
- paper5
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: 'Y closed (origin claim supported); AB running locally; AC implemented and queued'
  changed_by_session: 'pretraining-origin question answered 4/4; cloud lane abandoned for AB; first RQ4 control-loop cell signed and built'
checkpoints:
- id: 001-launch
  at: '2026-07-02T18:30:00Z'
  kind: launch
  title: AB V1 round 3 launched at d1943674 after committing gitignored direction files
  summary: Round-2 AB cloud failure root-caused to the frozen qwen3.5-4b probe
    direction files being gitignored (present locally, absent in the job checkout).
    Fixed with a scoped gitignore exception, committed the four direction files
    (d1943674), verified all 11 in-job inputs via git ls-tree of the pinned sha,
    and relaunched AB-1/2/3 as round 3 with the exact recovered round-2 commands.
- id: 002-decision
  at: '2026-07-02T22:40:00Z'
  kind: decision
  title: Cloud lane abandoned for AB V1 — all three round-3 cells stalled; moved to local 3090 queue
  summary: All three round-3 cells cleared bootstrap and direction/pool load, then
    froze mid model-weight download for 35+ minutes with byte-identical durable
    logs (same A10G pathology as the benched OLMo Y-cell). User directed
    cancellation; jobs canceled via API, outcome recorded in
    amendment_ab_v1_launch.json (round3_outcome), and a sequential local queue
    armed on the 3090 (OLMo extraction -> OLMo scoring -> AB-1/2/3). Durable-log
    byte-stasis across health checks is the stall oracle.
- id: 003-gate
  at: '2026-07-02T23:00:00Z'
  kind: gate
  title: Amendment AC (doubt-regulated caution) signed, implemented, 30/30 tests green
  summary: First PHASE3 RQ4 Stage-1 cell signed with a conservative posture
    (use-the-signal attempts 0-for-4 prior; 83% doubt-alignment spoiler named;
    null closes RQ4 Stage 1 negatively and is reportable). Implemented on branch
    amendment-ac-doubt-regulated-caution off main f10402cc — couple mode (erase
    caution_perp + write doubt-scaled setpoint; g=0 bit-identical to ablate),
    offline gain-map builder (1217 rows; per-cell mean z kr +0.35 / ka +1.18 /
    ur -0.73, signs as pre-registered), permuted-gains information control
    (seed 20260702), selectivity-gap analysis with paired bootstrap (AC-G1
    >=5pt CI excl 0), configs full+smoke, 17 new tests + 13 B1 regression all
    green. GPU smoke queued behind OLMo + AB local cells.
- id: 004-result
  at: '2026-07-02T23:30:00Z'
  kind: result
  title: OLMo-2-7B local Y cell PASS (gate 0.998 / dial 0.858 / veto 0.775) — fleet 10/10
  summary: The local 3090 replacement for the benched cloud cell completed
    (3000 attempts, 2998 answered, 725 correct / 1128 wrong / 627 hallucination,
    floors cleared by wide margins) and PASSES all three gates at L16. This
    closes the last open Y cell.
- id: 005-result
  at: '2026-07-02T23:55:00Z'
  kind: result
  title: 'Amendment Y roll-up: H_B1 SUPPORTED 4/4, H_B2 4/4, H_B3 not supported; era signal in within-SA control'
  summary: All 10 cells + chatrender control + engine-equivalence cell rolled up
    into AMENDMENT-Y §9 with per-cell artifacts committed under
    experiment/phase1/probe/amendment_y_results/. Headlines — the boundary signal
    predates post-training on all four Arm A families (gate 0.997+ on every base,
    falsifier 0/4); post-training does NOT sharpen the veto (deltas <= 0, clean
    Olmo-3 pair 0.803 -> 0.731); Qwen3.5-Base veto is render-sensitive (0.666
    k-shot vs 0.867 chat) while the gate is render-invariant; the era ladder is
    descriptive-only with the era signal in the within-SA control (~0.59 old era
    -> 0.71-0.82 modern) and all readouts reported next to the 0.964 text
    baseline. Regimen paper's §8 open question is answered in the "already
    present from pretraining" direction; paper text update deliberately deferred
    to the paper line (paper-line-restructure unmerged; avoid cross-branch
    conflicts).
---

# Session 0033 — Amendment Y fleet complete + AB local pivot + Amendment AC signed

See checkpoints. Three threads advanced in one session: (1) Amendment Y closed
with its primary hypothesis supported 4/4 and the roll-up committed on the Y
branch; (2) Amendment AB V1 moved from the HF cloud lane (three stalled fleets,
two failure postmortems, one infrastructure lesson about verifying in-job
inputs against the pinned sha) to a sequential local 3090 queue; (3) Amendment
AC — the first doubt-regulates-caution control-loop cell — was signed under a
deliberately conservative framing, fully implemented, and queued for GPU time
behind the AB cells.
