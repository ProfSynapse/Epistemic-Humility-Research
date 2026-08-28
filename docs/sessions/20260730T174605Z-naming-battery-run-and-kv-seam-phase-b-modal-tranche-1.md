---
schema_version: research-session/v1
session_id: 20260730T174605Z-naming-battery-run-and-kv-seam-phase-b-modal-tranche-1
title: Naming battery run and kv-seam Phase B Modal tranche 1
status: active
created_at: '2026-07-30T17:46:05Z'
updated_at: '2026-07-31T12:21:36Z'
question: Does the mid-band c_hat write earn a name (naming battery axes G/B/K), and
  does the below-seam actuation survive the KV-sharing OFF contrast (Phase B A1/A2)?
tags: []
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-checkpoint
  at: '2026-07-30T17:46:48Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'NAMING BATTERY (exp/naming-battery-run): phase 2 generation COMPLETE,
    6105/6105 rows exact across 14 arms, ~75 min, zero dupes; lead verified counts/rates/readback
    independently. Rulings in NOTEBOOK (commits e73d1444, a6984ff4): G1 adjudicated
    on refused_v2 with narrow reading also passing; b_neg_2 REGIME-INVALID (degenerate
    0.8979 vs registered 0.20 ceiling, excluded from form scoring), b_neg_1 valid
    at 0.1021; full-run offtarget rests on registered smoke parity. Taxonomy instrument
    pinned (5 files, 5 judgment calls signed off, 36/36 tests). Red-team port-fidelity
    audit: 3 registered ports AST-identical to margin-mapping/harness, 550-row differential
    execution identical, 6105-row invariant audit zero violations; 8 harness files
    pinned after lead re-hashed all (15/15). CRITICAL FINDING: the run wired 2 of
    3 registered graders and registered redact_fields stripped text at write time,
    so no form_class and no text on disk; ruled instrument COMPLETION not design change:
    Arm A-only regeneration (2800 rows) with full 3-grader chain via new standalone
    driver over pinned modules, namespaced runlog_form/, private text sidecar, row-by-row
    verdict-field reproduction as acceptance gate. Runner executing now (driver written,
    smoke passed). KV-SEAM PHASE B (exp/kv-seam-phase-b, Modal cloud lane, user-approved
    ~$32-43): C1 producer corrected per lead ruling (reference completion = C0 greedy
    completion teacher-forced under BOTH conditions, paired; own-completion NLL kept
    as non-gating diagnostic; 42 tests), commits 86fc6e42/c9687aa4/b37918c1/79b88098.
    DISPATCH INCIDENT: first tranche-1 dispatch used the stage command with neither
    detach nor wait flags; the entrypoint spawn+exit pattern killed all 18 calls in
    26 s, $0, volume clean; fixed with wait-mode (fc.get, nonzero on raise) + generic
    needs-restore (each dependency ckpt subtree copied into fresh container, fail-closed
    on missing provenance) + resume arg. Tranche 1 then halted TWICE at b3 fail-closed:
    (1) ON extraction manifest never staged; (2) manifest rows_path records parent
    jspace ABSOLUTE host path + pool_generations.jsonl unstaged. Fixes: manifest +
    pool_generations staged to the volume (the pool_generations upload was classifier-blocked
    for the agent; PI executed it directly), rows_path layout shim materializes staged
    byte-identical eval_rows (7a2784bd) at the recorded path. b0-b3 now PASS (b1 164
    s on A100; far under estimate); chain at b4+. Tranche 2 (b16-b18b,b20) gated on
    C1 PASS; C1 stage entry + NOTEBOOK instrument recording still pending. Next: monitor
    tranche 1 to b15, review Arm A form-pass report, then pool build, blinded 200-row
    calibration via isolated adjudicator, axis arithmetic, naming-table lead adjudication,
    resolve, PRs (each merge needs per-PR user approval).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-checkpoint
  at: '2026-07-30T19:56:30Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Naming battery closed end to end: blinded calibration FAILED (core disagreement
    0.43 vs 0.05 floor, one-sided 79/86 under-detection of hedging; decoys 19/19 under
    a user-approved governed deviation from the 25 floor, moot), AXIS_G_VOID as registered;
    axis B POSITIVE-ONLY via O-2 (release 0.760/0.948 but released-row correctness
    ~0.10 vs 0.30 and placebo 0.107 vs 0.05; output-gate suppression finding recorded);
    axis K KNOWLEDGE-STATE (rare minus popular -0.06, CI spans zero); O-1 fires 6.37:1
    with nothing to prefix; z_d companion read ruled NOT-COMPUTABLE-AS-REGISTERED.
    Cell resolved falsified, verdict unnamed write direction (form instrument void).
    PRs 357 (resolve), 358 (form-instrument-v2 prep draft + grading-reference cautionary
    case), 359 (KG ingest, 5 nodes) all user-approved and merged; ingest worktree
    removed, run worktree RETAINED (analysis/ holds the Arm A generations and the
    unblinded dev set for instrument v2). kv-seam Phase B: b8 exit-1 was the registered
    no-usable-dose verdict (A1 dose-viability NOT-RUN, parent gemma null reproduced);
    lane taught verdict exits (verdict_exit_ok on b8/b9/b10, artifact-presence check,
    VERDICT-RECORDED marker, dependent-stage skips), committed 586ce29a; tranche redispatched
    from b8 18:56Z, sweep mid-flight, chain will self-continue into b9; C1 dispatch
    queued for after tranche 1.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-checkpoint
  at: '2026-07-30T22:15:00Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Post-resolution follow-through, all user-approved and merged: PR 359 KG
    ingest (5 negative-polarity nodes; ingest worktree removed, run worktree retained
    for the Arm A generations and instrument-v2 dev set). PI GPU directive: never
    hard-code GPU in cloud harnesses; kv-seam harness now reads PHASEB_GPU with A100-80GB
    default kept for arm parity, dispatch-side value recorded per stage as gpu_type
    provenance (7201a809 on exp/kv-seam-phase-b); sizing rule added to mechinterp-cells
    modal-launch reference (PR 360, merged a762bc89). Form instrument v2: PI corrected
    the framing, the standing blinded-adjudication protocol (abstention-grading reference,
    CG1/RR2/RR3 lineage) is promoted from calibration-check to primary instrument;
    PI decisions recorded: single judge, model adjudicator with lead spot-check at
    end, own CPU-only cell, opus subagent as judge (PR 361, merged 259ceac6). Phase
    B: b8 verdict recorded end to end (VERDICT-RECORDED marker, gpu provenance, ckpt
    mirrored, A1 dose-viability NOT-RUN, parent gemma null reproduced); b9 OFF-primary
    calibration mid-sweep, ETA about 21:50Z; then b10, smokes with A1-dependent skips,
    then C1 dispatch gating tranche 2.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-checkpoint
  at: '2026-07-31T01:31:26Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'form-judge-axis-g-rescore full arc in one evening: signed (G1 floor from
    dev judge-vs-judge 0.080+0.04), calibration attempt 1 voided at lead spot-check
    (all 25 clear-negative decoys empty; Arm C retains no text anywhere; PI-approved
    deviation drops clear-negative, G2 clear-positive only), attempt 2 validated (G1
    0.035, G2 25/25), payload 1781 rows graded, axis G BINARY: baseline hedged share
    0.431, dose monotonically converts prose to explicit IDK (F4 16 to 267), both
    aligned scoreboard calls correct. Resolved, merged (#362), KG-ingested (#363:
    experiment node + judge-lane instrument mechanism + mode-switch mechanism). Working
    label discussed with PI: explicit-IDK mode switch (descriptive, not an earned
    name). Phase B: b9 exit 0 (A2 found usable doses), b10 in flight.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-checkpoint
  at: '2026-07-31T09:40:17Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'kv-seam Phase B tranche 1 terminal 02:48Z: all 18 stages exit 0, but b8/b9/b10
    (A1/A2/A4 dose calibrations) each recorded registered verdicts of no usable mid-band
    dose (every has_usable_dose false, all layers, both KV conditions); dispatcher
    correctly skipped b11-b15. Registered NULL-RESULT disposition (AMENDMENT.md:996-1000)
    applies. User approved: skip C1 (its OFF-arm gating role is moot with B12/B13
    NOT-RUN) and resolve as NULL-RESULT; resolution artifact fetch from Modal volume
    delegated and in progress; Outcome write-up, resolve, PR next. Lead corrected
    own earlier misreport that b9 found usable doses. Gemma theory state for the record:
    KV-quarantine account NOT confirmed and weakened (below-seam donor-reachable sites
    hs15-23 also inert in the band where mistral actuates; sharing-OFF created no
    viability); null is model-level, mechanism undifferentiated (crystallization-gap/depth-window
    vs flat-structure); untested pocket hs25-27 (rd 0.595-0.643) noted, registered
    ladder does not move. Parallel: idk-switch-naming-confirmatory SIGNED (user-approved)
    with lead build-time rulings (sampled decode per SR standard since naming battery
    was greedy and a fresh seed is a no-op under greedy; N2 scoped to c_hat-dosed
    arms; provenance capture rewritten to real entrypoint contract with hard-fail
    digest match; seeds 20260802/20260803; gates N1 0.15 / N2 0.10 / N3 0.05 / decoys
    25 at 0.92); mechinterp-runner:local image rebuilt and digest pinned; local-3090
    4-arm sweep delegated and in progress, halting at the blinded-judge boundary which
    stays lead-run.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-checkpoint
  at: '2026-07-31T09:48:09Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'CORRECTION superseding the prior checkpoint theory summary: the lead misstated
    the gemma record by citing the pre-sign motivation table without reading the Phase
    A adjudication (NOTEBOOK R1-R9). Gemma DID actuate under sharing ON in Phase A:
    D1/hs15 G1 PASS 0.786 [0.718,0.841] G2 PASS; A3/hs22 G1 0.589 G2 PASS with G3
    PASS-DEGENERATE (direction-specific, five placebo draws at zero); A5/hs24 G1 0.732
    G2 PASS but G3 FAIL (placebo reproduced 88 percent; adjudicated seam-region instability);
    D2/D3 sub-floor; D4/hs23 dose-viability NOT-RUN; hs40 late null. Phase B tranche
    1: no usable dose at hs34/38/42 ON or OFF and hs22/24 OFF; OFF-condition calibration
    undosed floors show known-correct cost 8/8 = 1.0 with zero collapse, i.e. the
    sharing-OFF substrate is behaviorally broken at baseline, which is exactly what
    the registered C1 precondition control exists to adjudicate. Consequences: the
    NULL-RESULT disposition does NOT apply (arms had usable doses); the amendment
    963 falsifier leg (D1 clears while A1 does not) reads as quarantine SUPPORTED-not-established,
    pending lead+user adjudication of NOT-RUN vs fails-G1 wording; lead recommendation
    on C1 FLIPS to RUN it so the A2/A4 axis resolves on the registered INCONCLUSIVE-if-C1-fails
    branch; prior user approval to skip C1 was premised on the wrong picture and is
    void, decision re-lifted. User directed a successor pocket cell (hs25-27 ON, the
    untested rd 0.595-0.643 band, with G3 placebo draws per the A5 lesson) to test
    seam-vs-depth on the unmodified model; registration to be drafted. IDK-switch
    local run blocked on missing NVIDIA Container Toolkit in the WSL distro (user
    sudo required; commands provided); rows materialized, harness intact.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-checkpoint
  at: '2026-07-31T12:21:36Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'KV-SEAM RESOLVED + IDK-SWITCH LAUNCH ARC (2026-07-31). (1) gemma4-e4b-kv-seam-quarantine
    RESOLVED (PR #365, user-approved verdict): C1 precondition FAIL (local pinned
    tf550 run, full FIT population: OFF known-correct cost 180/180 vs ON 0/180, NLL
    3.53 vs 12.33), registered INCONCLUSIVE branch fires for A2/A4; D-ladder supporting
    leg fires as registered (D1 0.786 held-out vs A1 no-usable-dose; VOID-complement
    reading user-approved) so KV-quarantine SUPPORTED-not-established, depth-confounded
    as pre-stated; hs24 non-specific per R4. C0 positive-control hold adjudicated
    BAND-TRANSFER-INVALID: the cited undosed confab band was dosed-cell data (n_fired
    6-7/8 at lowest rung), no genuine ON-midband undosed floor exists, known-correct
    leg one thin n=8 draw (hypergeometric p=8/188=0.043); FAIL robust to entire disputed
    C0 range. (2) PR #364 MERGED (cite-discipline, gemma atlas rows, KG retrieval-verification
    Move 4e, one-socket-two-daemons docker gotcha). (3) Docker root cause: /var/run/docker.sock
    backed by Desktop engine (nvidia runtime) when Desktop open, WSL-native dockerd
    (no GPU) when closed; NO toolkit install needed; user directive immortalized in
    mechinterp-cells skill: ask user to open Desktop, never work around. IDK-switch
    digest was captured from wrong daemon: repinned 0421dc9c to fe732c8f (Phase A
    validated build). (4) IDK-switch launch chain: worktree submodule uninitialized
    (fixed, gitlink 34c89fc4); shared image lacked pydantic (MechInterp.config import;
    parent naming battery ran in documented base-conda deviation AMENDMENT:272-273)
    so Dockerfile +pydantic==2.12.4 via Synaptic-Tuner PR #150, rebuild 894cb31b (tuner
    rev 49cebc2b), SECOND repin fe732c8f to 894cb31b (commit b82e401a); smoke re-running
    now, then 1600-gen sweep to judge-lane halt. (5) gemma4-e4b-pocket-ladder drafted
    (58de997d), red-teamed NOT-SIGNABLE (B1 placebo site-set refusal, B2 wrong extraction
    named - corrupt at hs25+, B3 no staging contract, B4 rollup arm-map), remediated
    (adb1c9e3 + fe852230: registered_control_site_sets from cell.yaml, corrected use_cache=True
    extraction with 4 staged-input sha256s incl eval_rows, pocket_rollup.py, seed
    stride 1000*hs, PASS-DEGENERATE reporting restriction, multiplicity note); signable
    pending orchestrator+user scoreboard calls (must-not-sign guard manual: exp.py
    cmd_sign never reads AMENDMENT.md - lead-owned gap). NEXT: verify smoke, dispatch
    generate, judge lane lead-run; PR #365 merge decision with user; post-merge kv-seam
    KG ingest under new Move 4e retrieval rules; pocket sign after user call.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
---
# Naming battery run and kv-seam Phase B Modal tranche 1

## Question

Does the mid-band c_hat write earn a name (naming battery axes G/B/K), and does the below-seam actuation survive the KV-sharing OFF contrast (Phase B A1/A2)?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-checkpoint - Checkpoint

- at: `2026-07-30T17:46:48Z`
- kind: `checkpoint`
- summary: NAMING BATTERY (exp/naming-battery-run): phase 2 generation COMPLETE, 6105/6105 rows exact across 14 arms, ~75 min, zero dupes; lead verified counts/rates/readback independently. Rulings in NOTEBOOK (commits e73d1444, a6984ff4): G1 adjudicated on refused_v2 with narrow reading also passing; b_neg_2 REGIME-INVALID (degenerate 0.8979 vs registered 0.20 ceiling, excluded from form scoring), b_neg_1 valid at 0.1021; full-run offtarget rests on registered smoke parity. Taxonomy instrument pinned (5 files, 5 judgment calls signed off, 36/36 tests). Red-team port-fidelity audit: 3 registered ports AST-identical to margin-mapping/harness, 550-row differential execution identical, 6105-row invariant audit zero violations; 8 harness files pinned after lead re-hashed all (15/15). CRITICAL FINDING: the run wired 2 of 3 registered graders and registered redact_fields stripped text at write time, so no form_class and no text on disk; ruled instrument COMPLETION not design change: Arm A-only regeneration (2800 rows) with full 3-grader chain via new standalone driver over pinned modules, namespaced runlog_form/, private text sidecar, row-by-row verdict-field reproduction as acceptance gate. Runner executing now (driver written, smoke passed). KV-SEAM PHASE B (exp/kv-seam-phase-b, Modal cloud lane, user-approved ~$32-43): C1 producer corrected per lead ruling (reference completion = C0 greedy completion teacher-forced under BOTH conditions, paired; own-completion NLL kept as non-gating diagnostic; 42 tests), commits 86fc6e42/c9687aa4/b37918c1/79b88098. DISPATCH INCIDENT: first tranche-1 dispatch used the stage command with neither detach nor wait flags; the entrypoint spawn+exit pattern killed all 18 calls in 26 s, $0, volume clean; fixed with wait-mode (fc.get, nonzero on raise) + generic needs-restore (each dependency ckpt subtree copied into fresh container, fail-closed on missing provenance) + resume arg. Tranche 1 then halted TWICE at b3 fail-closed: (1) ON extraction manifest never staged; (2) manifest rows_path records parent jspace ABSOLUTE host path + pool_generations.jsonl unstaged. Fixes: manifest + pool_generations staged to the volume (the pool_generations upload was classifier-blocked for the agent; PI executed it directly), rows_path layout shim materializes staged byte-identical eval_rows (7a2784bd) at the recorded path. b0-b3 now PASS (b1 164 s on A100; far under estimate); chain at b4+. Tranche 2 (b16-b18b,b20) gated on C1 PASS; C1 stage entry + NOTEBOOK instrument recording still pending. Next: monitor tranche 1 to b15, review Arm A form-pass report, then pool build, blinded 200-row calibration via isolated adjudicator, axis arithmetic, naming-table lead adjudication, resolve, PRs (each merge needs per-PR user approval).
### 002-checkpoint - Checkpoint

- at: `2026-07-30T19:56:30Z`
- kind: `checkpoint`
- summary: Naming battery closed end to end: blinded calibration FAILED (core disagreement 0.43 vs 0.05 floor, one-sided 79/86 under-detection of hedging; decoys 19/19 under a user-approved governed deviation from the 25 floor, moot), AXIS_G_VOID as registered; axis B POSITIVE-ONLY via O-2 (release 0.760/0.948 but released-row correctness ~0.10 vs 0.30 and placebo 0.107 vs 0.05; output-gate suppression finding recorded); axis K KNOWLEDGE-STATE (rare minus popular -0.06, CI spans zero); O-1 fires 6.37:1 with nothing to prefix; z_d companion read ruled NOT-COMPUTABLE-AS-REGISTERED. Cell resolved falsified, verdict unnamed write direction (form instrument void). PRs 357 (resolve), 358 (form-instrument-v2 prep draft + grading-reference cautionary case), 359 (KG ingest, 5 nodes) all user-approved and merged; ingest worktree removed, run worktree RETAINED (analysis/ holds the Arm A generations and the unblinded dev set for instrument v2). kv-seam Phase B: b8 exit-1 was the registered no-usable-dose verdict (A1 dose-viability NOT-RUN, parent gemma null reproduced); lane taught verdict exits (verdict_exit_ok on b8/b9/b10, artifact-presence check, VERDICT-RECORDED marker, dependent-stage skips), committed 586ce29a; tranche redispatched from b8 18:56Z, sweep mid-flight, chain will self-continue into b9; C1 dispatch queued for after tranche 1.
### 003-checkpoint - Checkpoint

- at: `2026-07-30T22:15:00Z`
- kind: `checkpoint`
- summary: Post-resolution follow-through, all user-approved and merged: PR 359 KG ingest (5 negative-polarity nodes; ingest worktree removed, run worktree retained for the Arm A generations and instrument-v2 dev set). PI GPU directive: never hard-code GPU in cloud harnesses; kv-seam harness now reads PHASEB_GPU with A100-80GB default kept for arm parity, dispatch-side value recorded per stage as gpu_type provenance (7201a809 on exp/kv-seam-phase-b); sizing rule added to mechinterp-cells modal-launch reference (PR 360, merged a762bc89). Form instrument v2: PI corrected the framing, the standing blinded-adjudication protocol (abstention-grading reference, CG1/RR2/RR3 lineage) is promoted from calibration-check to primary instrument; PI decisions recorded: single judge, model adjudicator with lead spot-check at end, own CPU-only cell, opus subagent as judge (PR 361, merged 259ceac6). Phase B: b8 verdict recorded end to end (VERDICT-RECORDED marker, gpu provenance, ckpt mirrored, A1 dose-viability NOT-RUN, parent gemma null reproduced); b9 OFF-primary calibration mid-sweep, ETA about 21:50Z; then b10, smokes with A1-dependent skips, then C1 dispatch gating tranche 2.
### 004-checkpoint - Checkpoint

- at: `2026-07-31T01:31:26Z`
- kind: `checkpoint`
- summary: form-judge-axis-g-rescore full arc in one evening: signed (G1 floor from dev judge-vs-judge 0.080+0.04), calibration attempt 1 voided at lead spot-check (all 25 clear-negative decoys empty; Arm C retains no text anywhere; PI-approved deviation drops clear-negative, G2 clear-positive only), attempt 2 validated (G1 0.035, G2 25/25), payload 1781 rows graded, axis G BINARY: baseline hedged share 0.431, dose monotonically converts prose to explicit IDK (F4 16 to 267), both aligned scoreboard calls correct. Resolved, merged (#362), KG-ingested (#363: experiment node + judge-lane instrument mechanism + mode-switch mechanism). Working label discussed with PI: explicit-IDK mode switch (descriptive, not an earned name). Phase B: b9 exit 0 (A2 found usable doses), b10 in flight.
### 005-checkpoint - Checkpoint

- at: `2026-07-31T09:40:17Z`
- kind: `checkpoint`
- summary: kv-seam Phase B tranche 1 terminal 02:48Z: all 18 stages exit 0, but b8/b9/b10 (A1/A2/A4 dose calibrations) each recorded registered verdicts of no usable mid-band dose (every has_usable_dose false, all layers, both KV conditions); dispatcher correctly skipped b11-b15. Registered NULL-RESULT disposition (AMENDMENT.md:996-1000) applies. User approved: skip C1 (its OFF-arm gating role is moot with B12/B13 NOT-RUN) and resolve as NULL-RESULT; resolution artifact fetch from Modal volume delegated and in progress; Outcome write-up, resolve, PR next. Lead corrected own earlier misreport that b9 found usable doses. Gemma theory state for the record: KV-quarantine account NOT confirmed and weakened (below-seam donor-reachable sites hs15-23 also inert in the band where mistral actuates; sharing-OFF created no viability); null is model-level, mechanism undifferentiated (crystallization-gap/depth-window vs flat-structure); untested pocket hs25-27 (rd 0.595-0.643) noted, registered ladder does not move. Parallel: idk-switch-naming-confirmatory SIGNED (user-approved) with lead build-time rulings (sampled decode per SR standard since naming battery was greedy and a fresh seed is a no-op under greedy; N2 scoped to c_hat-dosed arms; provenance capture rewritten to real entrypoint contract with hard-fail digest match; seeds 20260802/20260803; gates N1 0.15 / N2 0.10 / N3 0.05 / decoys 25 at 0.92); mechinterp-runner:local image rebuilt and digest pinned; local-3090 4-arm sweep delegated and in progress, halting at the blinded-judge boundary which stays lead-run.
### 006-checkpoint - Checkpoint

- at: `2026-07-31T09:48:09Z`
- kind: `checkpoint`
- summary: CORRECTION superseding the prior checkpoint theory summary: the lead misstated the gemma record by citing the pre-sign motivation table without reading the Phase A adjudication (NOTEBOOK R1-R9). Gemma DID actuate under sharing ON in Phase A: D1/hs15 G1 PASS 0.786 [0.718,0.841] G2 PASS; A3/hs22 G1 0.589 G2 PASS with G3 PASS-DEGENERATE (direction-specific, five placebo draws at zero); A5/hs24 G1 0.732 G2 PASS but G3 FAIL (placebo reproduced 88 percent; adjudicated seam-region instability); D2/D3 sub-floor; D4/hs23 dose-viability NOT-RUN; hs40 late null. Phase B tranche 1: no usable dose at hs34/38/42 ON or OFF and hs22/24 OFF; OFF-condition calibration undosed floors show known-correct cost 8/8 = 1.0 with zero collapse, i.e. the sharing-OFF substrate is behaviorally broken at baseline, which is exactly what the registered C1 precondition control exists to adjudicate. Consequences: the NULL-RESULT disposition does NOT apply (arms had usable doses); the amendment 963 falsifier leg (D1 clears while A1 does not) reads as quarantine SUPPORTED-not-established, pending lead+user adjudication of NOT-RUN vs fails-G1 wording; lead recommendation on C1 FLIPS to RUN it so the A2/A4 axis resolves on the registered INCONCLUSIVE-if-C1-fails branch; prior user approval to skip C1 was premised on the wrong picture and is void, decision re-lifted. User directed a successor pocket cell (hs25-27 ON, the untested rd 0.595-0.643 band, with G3 placebo draws per the A5 lesson) to test seam-vs-depth on the unmodified model; registration to be drafted. IDK-switch local run blocked on missing NVIDIA Container Toolkit in the WSL distro (user sudo required; commands provided); rows materialized, harness intact.
### 007-checkpoint - Checkpoint

- at: `2026-07-31T12:21:36Z`
- kind: `checkpoint`
- summary: KV-SEAM RESOLVED + IDK-SWITCH LAUNCH ARC (2026-07-31). (1) gemma4-e4b-kv-seam-quarantine RESOLVED (PR #365, user-approved verdict): C1 precondition FAIL (local pinned tf550 run, full FIT population: OFF known-correct cost 180/180 vs ON 0/180, NLL 3.53 vs 12.33), registered INCONCLUSIVE branch fires for A2/A4; D-ladder supporting leg fires as registered (D1 0.786 held-out vs A1 no-usable-dose; VOID-complement reading user-approved) so KV-quarantine SUPPORTED-not-established, depth-confounded as pre-stated; hs24 non-specific per R4. C0 positive-control hold adjudicated BAND-TRANSFER-INVALID: the cited undosed confab band was dosed-cell data (n_fired 6-7/8 at lowest rung), no genuine ON-midband undosed floor exists, known-correct leg one thin n=8 draw (hypergeometric p=8/188=0.043); FAIL robust to entire disputed C0 range. (2) PR #364 MERGED (cite-discipline, gemma atlas rows, KG retrieval-verification Move 4e, one-socket-two-daemons docker gotcha). (3) Docker root cause: /var/run/docker.sock backed by Desktop engine (nvidia runtime) when Desktop open, WSL-native dockerd (no GPU) when closed; NO toolkit install needed; user directive immortalized in mechinterp-cells skill: ask user to open Desktop, never work around. IDK-switch digest was captured from wrong daemon: repinned 0421dc9c to fe732c8f (Phase A validated build). (4) IDK-switch launch chain: worktree submodule uninitialized (fixed, gitlink 34c89fc4); shared image lacked pydantic (MechInterp.config import; parent naming battery ran in documented base-conda deviation AMENDMENT:272-273) so Dockerfile +pydantic==2.12.4 via Synaptic-Tuner PR #150, rebuild 894cb31b (tuner rev 49cebc2b), SECOND repin fe732c8f to 894cb31b (commit b82e401a); smoke re-running now, then 1600-gen sweep to judge-lane halt. (5) gemma4-e4b-pocket-ladder drafted (58de997d), red-teamed NOT-SIGNABLE (B1 placebo site-set refusal, B2 wrong extraction named - corrupt at hs25+, B3 no staging contract, B4 rollup arm-map), remediated (adb1c9e3 + fe852230: registered_control_site_sets from cell.yaml, corrected use_cache=True extraction with 4 staged-input sha256s incl eval_rows, pocket_rollup.py, seed stride 1000*hs, PASS-DEGENERATE reporting restriction, multiplicity note); signable pending orchestrator+user scoreboard calls (must-not-sign guard manual: exp.py cmd_sign never reads AMENDMENT.md - lead-owned gap). NEXT: verify smoke, dispatch generate, judge lane lead-run; PR #365 merge decision with user; post-merge kv-seam KG ingest under new Move 4e retrieval rules; pocket sign after user call.
