---
schema_version: research-session/v1
session_id: 20260809T094942Z-paper-3-burn-downs-item-25-falsified-item-26-harness-item-27-signed
title: 'Paper-3 burn-downs: item-25 falsified, item-26 harness, item-27 signed'
status: active
created_at: '2026-08-09T09:49:42Z'
updated_at: '2026-08-10T09:43:13Z'
question: Do the three registered paper-3 limitation burn-downs (wrong-answer power
  fix, OOD breadth, caution-install transfer) survive their gates, and what do their
  resolutions change in paper 3?
tags: []
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-checkpoint
  at: '2026-08-09T09:49:58Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Arc through 2026-08-09 ~09:50Z, all merged to main (PRs 406-413). (1)
    Paper-4 review fix pass merged (PR 406). (2) Item 25 wrong-answer-cell-power-fix
    ran end to end and RESOLVED FALSIFIED (PRs 407 registration, 409 resolution):
    axis-level A1 refit AUROC 0.5597 (CI 0.5185-0.5993) vs emitted 0.5207, gap CI
    includes zero, on 360 wrong / 420 correct deployment-rendered rows; scope ruling
    is axis-level only (unregistered context probe 0.6769 shows correctness linearly
    present elsewhere); calibration contrast A7 +0.2373 survives; headline 0.997 known/unknown
    readout untouched. KG ingest merged (PR 410); paper-3 draft-v2 axis-level revision
    merged (PR 412), scoped exactly to AMENDMENT section 7 authorized sites; fig-p2-01
    PNG regeneration and four out-of-scope ECE-0.004 restatements (abstract, intro,
    two discussion sites) left as flagged residuals. (3) Item 26 ood-breadth-beyond-selfaware
    harness built and merged (PR 411): G0 screen reproduced every registered count,
    8 arm configs, additive ood.py loaders, gate scorers, RUNBOOK; lead hand-pinned
    all 16 new modules (sign/repin tooling gap, third occurrence) and re-ran the screen
    post-pin byte-identical. (4) Item 27 caution-install-bounded-site-sweep SIGNED
    (PR 413): feasibility probe P1 failed on Wilson extrapolation (207.47 < 250),
    PI-approved full-corpus census measured 33+227=260 actual confabs over M_u 3496
    >= 250 floor under a criterion fixed pre-run; realized rate 7.44 pct inside the
    prior bracket (probe 8.25, SelfAware census 5.75-6.6); lead recounted both private
    row files independently and verified disjointness/union. NEXT: item-26 stage-4
    smoke then 8-12 GPU-h panel (launch approved, GPU free); item-27 sweep harness
    build then separate PI launch approval for 16-26 GPU-h; fig-p2-01 regeneration;
    caution-install-sweep worktree retained because its gitignored analysis/ holds
    the probe/census row data the sweep pool draws from.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-checkpoint
  at: '2026-08-09T16:29:23Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Item-26 full run complete through stage 8 and lead-adjudicated. Stages
    2-4: re-merge exit 0; G1 re-merge parity FAIL (5/9 metrics 0.27-0.39pp over the
    0.10pp bar, counts exact) -> registered consequence applied, arms A2/A6/A7 VOID,
    cell reports on five arms. Stage 5: five-arm panel 4h37m, all exit 0, G2 exact
    counts 15/15 cells coverage 100, G3 zero think contamination. Stage 6 blocked
    twice by runtime gaps: mechinterp-runner image did not exist (built + pinned per
    2026-07-10 directive; instrument.runtime_image_digest added), then missing requests/peft
    and pandas (Dockerfile pins added in submodule commits 69c65b3 + 552775a, rebuilt,
    repinned twice, nothing evidential ran under superseded pins). Extraction exact
    2748/2748 rows both arms. Stage 7+8: G7 FAIL both arms (held-out 0.6279/0.6349
    vs 0.90 floor; margin 0.1326/0.1379 vs 0.15), G5 FAIL as registered (A3 std 0.1687,
    A8 std 0.4238 over 0.10 ceiling; all arms AUROC <= 0.65), G4 NOT_RUN as registered
    (n_arms 8 instrument unsatisfiable after G1 void; descriptive unregistered 5-arm
    rho ~0.1-0.2 with tie/compression caveat), G6 read, falsifier DOES NOT FIRE (no
    arm emitted-AUROC >= 0.70). Prediction: component 4 supported (over-refusal moves
    >10pp), components 2-3 failed, 1 unadjudicable. Headline: behavior transfers in
    level; the 0.997 internal readout does NOT transfer to AmbigQA (0.63); stated
    collapse not universal. gate_score.py flat integrity short-circuit adjudicated
    a pinned-script defect; remedied by hand-pinned wrapper score_evidential_fivearm.py
    calling pinned functions unchanged (verified line by line). Skill note added:
    mechinterp-runner root-write gotcha + router eager-import package gaps. PENDING:
    PI approval of PR #414 (item-27 missing probe scripts), the item-26 results PR
    + resolve wording, item-27 sweep harness + launch approval.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-checkpoint
  at: '2026-08-10T09:43:13Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Burn-down day tail plus two mini-cells: PR 416 (rawbase-ambigqa-boundary-readout,
    M1 0.6338, flavor-specific band, prediction supported) merged; PI approved resolves
    for item 26 and the rawbase cell (PR 417, with KG ingest of both, five typed nodes);
    PI then directed the flavor side quest. flavor-atlas-rawbase registered/signed/run
    same night (PR 418 merged): three all-layer raw-base extractions (AmbigQA 2748,
    KUQ screened 5540, SelfAware 3369, 37 states, 17.5 GPU-min), pinned OOF protocol
    sweep plus 8x8 transfer matrix. Result: mixed atlas as registered. All six KUQ
    flavors separate 0.98-0.999 with free cross-transfer incl SelfAware (0.83-0.9996);
    AmbigQA max 0.6590 over all 37 layers, near-chance transfer both directions. Reading:
    overt vs covert unanswerability, not flavor vs flavor. P1 supported, P2 failed
    (KUQ-ambiguous half), no falsifier fired. Style confound registered; style-controlled
    confirmatory cell is next. Repin audit: discover_layers ''all'' string crash fixed
    pre-reading. Process: shared-checkout branch collision (lead checkout under librarian)
    untangled via worktree; rule added to pr-workflow skill. Atlas resolve stamp still
    awaits PI approval; paper-3 scoping revision queued; item-27 sweep harness queued;
    submodule PR queued.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
track: paper-3-burn-downs
---
# Paper-3 burn-downs: item-25 falsified, item-26 harness, item-27 signed

## Question

Do the three registered paper-3 limitation burn-downs (wrong-answer power fix, OOD breadth, caution-install transfer) survive their gates, and what do their resolutions change in paper 3?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-checkpoint - Checkpoint

- at: `2026-08-09T09:49:58Z`
- kind: `checkpoint`
- summary: Arc through 2026-08-09 ~09:50Z, all merged to main (PRs 406-413). (1) Paper-4 review fix pass merged (PR 406). (2) Item 25 wrong-answer-cell-power-fix ran end to end and RESOLVED FALSIFIED (PRs 407 registration, 409 resolution): axis-level A1 refit AUROC 0.5597 (CI 0.5185-0.5993) vs emitted 0.5207, gap CI includes zero, on 360 wrong / 420 correct deployment-rendered rows; scope ruling is axis-level only (unregistered context probe 0.6769 shows correctness linearly present elsewhere); calibration contrast A7 +0.2373 survives; headline 0.997 known/unknown readout untouched. KG ingest merged (PR 410); paper-3 draft-v2 axis-level revision merged (PR 412), scoped exactly to AMENDMENT section 7 authorized sites; fig-p2-01 PNG regeneration and four out-of-scope ECE-0.004 restatements (abstract, intro, two discussion sites) left as flagged residuals. (3) Item 26 ood-breadth-beyond-selfaware harness built and merged (PR 411): G0 screen reproduced every registered count, 8 arm configs, additive ood.py loaders, gate scorers, RUNBOOK; lead hand-pinned all 16 new modules (sign/repin tooling gap, third occurrence) and re-ran the screen post-pin byte-identical. (4) Item 27 caution-install-bounded-site-sweep SIGNED (PR 413): feasibility probe P1 failed on Wilson extrapolation (207.47 < 250), PI-approved full-corpus census measured 33+227=260 actual confabs over M_u 3496 >= 250 floor under a criterion fixed pre-run; realized rate 7.44 pct inside the prior bracket (probe 8.25, SelfAware census 5.75-6.6); lead recounted both private row files independently and verified disjointness/union. NEXT: item-26 stage-4 smoke then 8-12 GPU-h panel (launch approved, GPU free); item-27 sweep harness build then separate PI launch approval for 16-26 GPU-h; fig-p2-01 regeneration; caution-install-sweep worktree retained because its gitignored analysis/ holds the probe/census row data the sweep pool draws from.
### 002-checkpoint - Checkpoint

- at: `2026-08-09T16:29:23Z`
- kind: `checkpoint`
- summary: Item-26 full run complete through stage 8 and lead-adjudicated. Stages 2-4: re-merge exit 0; G1 re-merge parity FAIL (5/9 metrics 0.27-0.39pp over the 0.10pp bar, counts exact) -> registered consequence applied, arms A2/A6/A7 VOID, cell reports on five arms. Stage 5: five-arm panel 4h37m, all exit 0, G2 exact counts 15/15 cells coverage 100, G3 zero think contamination. Stage 6 blocked twice by runtime gaps: mechinterp-runner image did not exist (built + pinned per 2026-07-10 directive; instrument.runtime_image_digest added), then missing requests/peft and pandas (Dockerfile pins added in submodule commits 69c65b3 + 552775a, rebuilt, repinned twice, nothing evidential ran under superseded pins). Extraction exact 2748/2748 rows both arms. Stage 7+8: G7 FAIL both arms (held-out 0.6279/0.6349 vs 0.90 floor; margin 0.1326/0.1379 vs 0.15), G5 FAIL as registered (A3 std 0.1687, A8 std 0.4238 over 0.10 ceiling; all arms AUROC <= 0.65), G4 NOT_RUN as registered (n_arms 8 instrument unsatisfiable after G1 void; descriptive unregistered 5-arm rho ~0.1-0.2 with tie/compression caveat), G6 read, falsifier DOES NOT FIRE (no arm emitted-AUROC >= 0.70). Prediction: component 4 supported (over-refusal moves >10pp), components 2-3 failed, 1 unadjudicable. Headline: behavior transfers in level; the 0.997 internal readout does NOT transfer to AmbigQA (0.63); stated collapse not universal. gate_score.py flat integrity short-circuit adjudicated a pinned-script defect; remedied by hand-pinned wrapper score_evidential_fivearm.py calling pinned functions unchanged (verified line by line). Skill note added: mechinterp-runner root-write gotcha + router eager-import package gaps. PENDING: PI approval of PR #414 (item-27 missing probe scripts), the item-26 results PR + resolve wording, item-27 sweep harness + launch approval.
### 003-checkpoint - Checkpoint

- at: `2026-08-10T09:43:13Z`
- kind: `checkpoint`
- summary: Burn-down day tail plus two mini-cells: PR 416 (rawbase-ambigqa-boundary-readout, M1 0.6338, flavor-specific band, prediction supported) merged; PI approved resolves for item 26 and the rawbase cell (PR 417, with KG ingest of both, five typed nodes); PI then directed the flavor side quest. flavor-atlas-rawbase registered/signed/run same night (PR 418 merged): three all-layer raw-base extractions (AmbigQA 2748, KUQ screened 5540, SelfAware 3369, 37 states, 17.5 GPU-min), pinned OOF protocol sweep plus 8x8 transfer matrix. Result: mixed atlas as registered. All six KUQ flavors separate 0.98-0.999 with free cross-transfer incl SelfAware (0.83-0.9996); AmbigQA max 0.6590 over all 37 layers, near-chance transfer both directions. Reading: overt vs covert unanswerability, not flavor vs flavor. P1 supported, P2 failed (KUQ-ambiguous half), no falsifier fired. Style confound registered; style-controlled confirmatory cell is next. Repin audit: discover_layers 'all' string crash fixed pre-reading. Process: shared-checkout branch collision (lead checkout under librarian) untangled via worktree; rule added to pr-workflow skill. Atlas resolve stamp still awaits PI approval; paper-3 scoping revision queued; item-27 sweep harness queued; submodule PR queued.
