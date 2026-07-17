---
schema_version: research-session/v1
session_id: 20260717T013941Z-gate-factorial-resolution-and-margin-theory-framework
title: Gate factorial resolution and margin theory framework
status: active
created_at: '2026-07-17T01:39:41Z'
updated_at: '2026-07-17T13:53:39Z'
question: What did the gate-contribution factorial settle, and what framework drives
  the next experiment series?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-result
  at: '2026-07-17T01:40:00Z'
  kind: result
  title: Result
  summary: 'Gate-contribution factorial RESOLVED (falsified): gate axis falsified
    both families. Gap_Sel(c_hat) 0.148 qwen / 0.129 mistral vs floor 0.20 (CIs exclude
    zero, sub-floor); cost protection 0.008 / 0.034 vs 0.10; P1 passed both; S1 qwen
    pass 7.27 sign-opposed, mistral fail 2.03. CG1 28/28 blinded shards, hash-commit-before-unblind
    enforced, opus red-team CONFIRM-NULL pre-verdict. PR #296 merged with PI approval
    (62ea7ff1). Scoreboard: PI 3/4, orchestrator 2/4; differentiating slot (mistral
    gate axis) to PI.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-interpretation
  at: '2026-07-17T01:40:00Z'
  kind: interpretation
  title: Interpretation
  summary: 'Margin theory framework adopted (docs/research/margin-theory-framework.md):
    epistemic state encoded as commitment margin (distance to abstention boundary);
    dose regime determines who supplies selectivity (mid-band: write self-sorts, factorial+doubt-snap;
    overdrive: gate essential, H4 ungated-vs-gated 60.1% vs 3.1%); two channels (readout
    vs susceptibility) may dissociate; boundary anisotropy is substrate-dependent
    (qwen direction-specific, mistral generic). Reconciles all three anchor experiments;
    H4 Binding scope statement 2 anticipated the operating-point dependence.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-decision
  at: '2026-07-17T01:40:00Z'
  kind: decision
  title: Decision
  summary: 'Vocabulary revision registered in framework note section 3: doubt direction
    -> known-unknown direction; doubt gate -> KU readout gate; caution write -> boundary
    push; confab propensity split into baseline confab rate vs commitment margin;
    new term boundary anisotropy. Governed docs keep historical names; KG ids additive-only
    with aliases. Mentalistic names earnable via 4-part criterion (evidence-responsiveness
    test M4 is the open leg). Experiment cascade M1-M6 defined; M1 margin mapping
    is next amendment; confirmatory gate-floor replication deprioritized. KG updates
    dispatched: commitment-margin + boundary-anisotropy terms, operating-point-dependence
    synthesis mechanism, framework term node term:margin-theory-of-epistemic-state.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-checkpoint
  at: '2026-07-17T02:11:48Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1 draft hardened pre-sign: threshold derivation (results-analyst, CPU-only)
    committed under margin-mapping analysis-committed/threshold_derivation/. Ladder
    cut 64x to 4x (doubt-snap hs20 collapse at dose_abs 25.2 = 2x reference); criterion
    reformulated censoring-aware (fitted known median 229.7 dose_abs exceeds collapse,
    so raw median ratio unobservable; observable-bound floor 2.5 derived); retrodiction
    restricted to permuted+baseline anchors, tolerance 0.10 derived; non-monotone
    ceilings 0.05/0.10 derived; n_confab 400 confirmed. Every Decision-record knob
    labeled DERIVED or JUDGMENT. Commits 8eb24dac + 506050c7 on exp/margin-mapping.
    Awaiting PI: 7 knob decisions + both predictors'' scoreboard calls.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-checkpoint
  at: '2026-07-17T02:24:29Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1 margin-mapping SIGNED (worktree exp/margin-mapping, commit 34a1332f,
    pushed). cell.yaml + gates.yaml pinned via bin/exp sign (476463c6 / 7eb74eed).
    Predictions registered pre-generation: PI calls qwen PASS / mistral FAIL on separation
    and setpoint placement, retrodiction PASS both; orchestrator calls PASS on all
    four with bands (observable bound qwen 3.0-3.7, mistral 2.5-4.5; fitted ratio
    qwen 15-60, mistral 8-80; known censored fraction qwen 0.80-0.95, mistral 0.60-0.90).
    Differentiating slots: mistral separation + placement. Decision record resolved
    at sign; single authorized launch knob = mistral top-rung adjustment if preflight
    shows collapse below 3x, NOTEBOOK-recorded pre-run. PI authorized overnight launch
    on free local 3090 (''get this running'', going to bed). Arc: harness-builder
    agent building staging + smokes + mandatory GPU preflight now (no generation,
    no commits); lead commits SC0 manifests at the boundary, then launches full two-family
    staircase detached with RunLog checkpointing (~4.5h/family).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-checkpoint
  at: '2026-07-17T02:49:49Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1 OVERNIGHT LAUNCH HALTED BY REGISTERED GATE. Build agent delivered:
    SC0 staging sha256-verified byte-identical vs factorial, seed-48260714 subsample
    manifests committed, 29/29 CPU smokes. Mandatory GPU preflight FAILED SC1 readback
    (rel 0.005) in BOTH families: 1 of 4 rows per family at the 0.0625x rung only
    (qwen rel 0.0068, mistral rel 0.0066); all rows at 1x/3x/4x passed at rel 0.0004-0.0019.
    Diagnosis: fixed absolute readback noise floor (0.0004-0.0053 dose_abs) dominating
    the relative bar at tiny setpoints; worst mis-dose 0.04% of reference. Lead adjudication
    (NOTEBOOK, commit b1e1e1fa): gate stands as registered (readback tolerance was
    not a pre-authorized knob; classifier also blocked the gates.yaml edit, honored
    per protocol); no retry-until-pass (SC1 has no registered retry remedy); read-only
    repeatability+noise-floor diagnostic dispatched to analysis/preflight_diag/. Proposal
    for PI morning: amend SC1 to rel 0.005 OR abs 0.005 x reference_dose_abs, repin,
    fresh preflight, launch. Collapse observed at 3x/4x both families (by design,
    boundary bracketed by 1.5x/2x rungs); mistral top-rung authorized knob NOT exercised.
    Preflight caught a real instrument-physics fact pre-run: the GPU-smoke-mandatory
    directive paid for itself on its first outing.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-checkpoint
  at: '2026-07-17T13:53:39Z'
  kind: checkpoint
  title: Checkpoint
  summary: "INCIDENT + FIX: worktree cleanup sweep (33 merged worktrees removed with\
    \ --force --force) destroyed gitignored row-level data living only in those worktrees:\
    \ M1's symlinked staging pools (qwen35-midband-heldout, rr2-mistral-confirm targets),\
    \ the factorial's row-level runlogs/generation text, and other resolved experiments'\
    \ data-exhaust. Committed evidence unaffected. Cleanup verification had checked\
    \ git state only (clean+merged) \u2014 gitignored artifacts were invisible to\
    \ it. M1 impact: qwen family SAFE (completed 10/10 rungs before the sweep, all\
    \ rung readbacks OK, full text in M1's own runlog); mistral launch crashed on\
    \ dangling pool symlink (KeyError kuq_unknowns_all:1000). Recovery: agent rebuilding\
    \ pools from committed builder scripts + datasets, acceptance = exact sha256 match\
    \ vs M1 staging_manifest pins, restage as LOCAL COPIES, then resume mistral. Blast-radius\
    \ inventory agent enumerating per-experiment losses (regenerable-deterministic\
    \ / regenerable-GPU / lost). PI-directed programmatic fix SHIPPED: PR #298 merged\
    \ (aea361d5) \u2014 post-merge git hook auto-harvests all gitignored experiments/\
    \ data from every worktree into main's checkout on every pull/merge (symlinks\
    \ materialized, newer-supersedes with prior preserved, --check mode gates worktree\
    \ removal); first harvest copied 3,279 files including live M1 runlogs. Policy\
    \ change: staged inputs are LOCAL COPIES, never cross-worktree symlinks."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
---
# Gate factorial resolution and margin theory framework

## Question

What did the gate-contribution factorial settle, and what framework drives the next experiment series?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-result - Result

- at: `2026-07-17T01:40:00Z`
- kind: `result`
- summary: Gate-contribution factorial RESOLVED (falsified): gate axis falsified both families. Gap_Sel(c_hat) 0.148 qwen / 0.129 mistral vs floor 0.20 (CIs exclude zero, sub-floor); cost protection 0.008 / 0.034 vs 0.10; P1 passed both; S1 qwen pass 7.27 sign-opposed, mistral fail 2.03. CG1 28/28 blinded shards, hash-commit-before-unblind enforced, opus red-team CONFIRM-NULL pre-verdict. PR #296 merged with PI approval (62ea7ff1). Scoreboard: PI 3/4, orchestrator 2/4; differentiating slot (mistral gate axis) to PI.
### 002-interpretation - Interpretation

- at: `2026-07-17T01:40:00Z`
- kind: `interpretation`
- summary: Margin theory framework adopted (docs/research/margin-theory-framework.md): epistemic state encoded as commitment margin (distance to abstention boundary); dose regime determines who supplies selectivity (mid-band: write self-sorts, factorial+doubt-snap; overdrive: gate essential, H4 ungated-vs-gated 60.1% vs 3.1%); two channels (readout vs susceptibility) may dissociate; boundary anisotropy is substrate-dependent (qwen direction-specific, mistral generic). Reconciles all three anchor experiments; H4 Binding scope statement 2 anticipated the operating-point dependence.
### 003-decision - Decision

- at: `2026-07-17T01:40:00Z`
- kind: `decision`
- summary: Vocabulary revision registered in framework note section 3: doubt direction -> known-unknown direction; doubt gate -> KU readout gate; caution write -> boundary push; confab propensity split into baseline confab rate vs commitment margin; new term boundary anisotropy. Governed docs keep historical names; KG ids additive-only with aliases. Mentalistic names earnable via 4-part criterion (evidence-responsiveness test M4 is the open leg). Experiment cascade M1-M6 defined; M1 margin mapping is next amendment; confirmatory gate-floor replication deprioritized. KG updates dispatched: commitment-margin + boundary-anisotropy terms, operating-point-dependence synthesis mechanism, framework term node term:margin-theory-of-epistemic-state.
### 004-checkpoint - Checkpoint

- at: `2026-07-17T02:11:48Z`
- kind: `checkpoint`
- summary: M1 draft hardened pre-sign: threshold derivation (results-analyst, CPU-only) committed under margin-mapping analysis-committed/threshold_derivation/. Ladder cut 64x to 4x (doubt-snap hs20 collapse at dose_abs 25.2 = 2x reference); criterion reformulated censoring-aware (fitted known median 229.7 dose_abs exceeds collapse, so raw median ratio unobservable; observable-bound floor 2.5 derived); retrodiction restricted to permuted+baseline anchors, tolerance 0.10 derived; non-monotone ceilings 0.05/0.10 derived; n_confab 400 confirmed. Every Decision-record knob labeled DERIVED or JUDGMENT. Commits 8eb24dac + 506050c7 on exp/margin-mapping. Awaiting PI: 7 knob decisions + both predictors' scoreboard calls.
### 005-checkpoint - Checkpoint

- at: `2026-07-17T02:24:29Z`
- kind: `checkpoint`
- summary: M1 margin-mapping SIGNED (worktree exp/margin-mapping, commit 34a1332f, pushed). cell.yaml + gates.yaml pinned via bin/exp sign (476463c6 / 7eb74eed). Predictions registered pre-generation: PI calls qwen PASS / mistral FAIL on separation and setpoint placement, retrodiction PASS both; orchestrator calls PASS on all four with bands (observable bound qwen 3.0-3.7, mistral 2.5-4.5; fitted ratio qwen 15-60, mistral 8-80; known censored fraction qwen 0.80-0.95, mistral 0.60-0.90). Differentiating slots: mistral separation + placement. Decision record resolved at sign; single authorized launch knob = mistral top-rung adjustment if preflight shows collapse below 3x, NOTEBOOK-recorded pre-run. PI authorized overnight launch on free local 3090 ('get this running', going to bed). Arc: harness-builder agent building staging + smokes + mandatory GPU preflight now (no generation, no commits); lead commits SC0 manifests at the boundary, then launches full two-family staircase detached with RunLog checkpointing (~4.5h/family).
### 006-checkpoint - Checkpoint

- at: `2026-07-17T02:49:49Z`
- kind: `checkpoint`
- summary: M1 OVERNIGHT LAUNCH HALTED BY REGISTERED GATE. Build agent delivered: SC0 staging sha256-verified byte-identical vs factorial, seed-48260714 subsample manifests committed, 29/29 CPU smokes. Mandatory GPU preflight FAILED SC1 readback (rel 0.005) in BOTH families: 1 of 4 rows per family at the 0.0625x rung only (qwen rel 0.0068, mistral rel 0.0066); all rows at 1x/3x/4x passed at rel 0.0004-0.0019. Diagnosis: fixed absolute readback noise floor (0.0004-0.0053 dose_abs) dominating the relative bar at tiny setpoints; worst mis-dose 0.04% of reference. Lead adjudication (NOTEBOOK, commit b1e1e1fa): gate stands as registered (readback tolerance was not a pre-authorized knob; classifier also blocked the gates.yaml edit, honored per protocol); no retry-until-pass (SC1 has no registered retry remedy); read-only repeatability+noise-floor diagnostic dispatched to analysis/preflight_diag/. Proposal for PI morning: amend SC1 to rel 0.005 OR abs 0.005 x reference_dose_abs, repin, fresh preflight, launch. Collapse observed at 3x/4x both families (by design, boundary bracketed by 1.5x/2x rungs); mistral top-rung authorized knob NOT exercised. Preflight caught a real instrument-physics fact pre-run: the GPU-smoke-mandatory directive paid for itself on its first outing.
### 007-checkpoint - Checkpoint

- at: `2026-07-17T13:53:39Z`
- kind: `checkpoint`
- summary: INCIDENT + FIX: worktree cleanup sweep (33 merged worktrees removed with --force --force) destroyed gitignored row-level data living only in those worktrees: M1's symlinked staging pools (qwen35-midband-heldout, rr2-mistral-confirm targets), the factorial's row-level runlogs/generation text, and other resolved experiments' data-exhaust. Committed evidence unaffected. Cleanup verification had checked git state only (clean+merged) — gitignored artifacts were invisible to it. M1 impact: qwen family SAFE (completed 10/10 rungs before the sweep, all rung readbacks OK, full text in M1's own runlog); mistral launch crashed on dangling pool symlink (KeyError kuq_unknowns_all:1000). Recovery: agent rebuilding pools from committed builder scripts + datasets, acceptance = exact sha256 match vs M1 staging_manifest pins, restage as LOCAL COPIES, then resume mistral. Blast-radius inventory agent enumerating per-experiment losses (regenerable-deterministic / regenerable-GPU / lost). PI-directed programmatic fix SHIPPED: PR #298 merged (aea361d5) — post-merge git hook auto-harvests all gitignored experiments/ data from every worktree into main's checkout on every pull/merge (symlinks materialized, newer-supersedes with prior preserved, --check mode gates worktree removal); first harvest copied 3,279 files including live M1 runlogs. Policy change: staged inputs are LOCAL COPIES, never cross-worktree symlinks.
