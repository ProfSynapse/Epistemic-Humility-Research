---
schema_version: research-session/v1
session_id: 20260724T223946Z-a-lin-depth-ladder-finding-6-dissolved-accessibility-and-actuation-windows-do-not-overlap
title: 'A_lin depth ladder: finding (6) dissolved; accessibility and actuation windows
  do not overlap'
status: complete
created_at: '2026-07-24T22:39:46Z'
updated_at: '2026-07-30T14:28:28Z'
question: Does gemma-4-E4B's logit lens fail on CLEAN activations (finding 6 real),
  or only on the use_cache=False corrupt extraction (finding 6 = Defect 3)?
tags:
- gemma4-e4b
- diagnostic
- tier3
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-result
  at: '2026-07-24T22:40:09Z'
  kind: result
  title: 'Finding (6) DISSOLVED: the logit-lens failure reproduces only on use_cache=False
    activations'
  summary: 'A_lin (top-1 of final_norm+unembed at the anchor, target = the model''s
    own recorded greedy next token) recomputed on the CLEAN gemma extraction (forward_use_cache:
    True, all 43 indices, 806 rows) vs the QUARANTINED corrupt one, identical harness.
    CLEAN: hs34 0.967, hs38 0.968, hs40 0.970, hs42 1.000, all median rank 1. CORRUPT,
    same depths: 0.000 across the board, median ranks 110692/204746/85073/3563. Live
    .logits, n=200: use_cache=True -> 1.000 (rank 1); use_cache=False -> 0.000 (median
    rank 2333). The reported finding-(6) signature (top-1 2.9%, true token rank 6227)
    reproduces ONLY on the corrupt path. Gemma''s output path is not broken; it was
    measured through KV-starved blocks, since the corrupt extraction held only hs34/38/40/42,
    all inside the corrupted region (>=hs25). Harness validated by the terminal-layer
    tautology in both families (gemma hs42 1.000, llama hs26 1.000) plus distinct-storage
    and non-zero vacuity guards.'
  evidence:
  - experiments/j-space-cross-family-layer-contrast/analysis/crystallization-ladder/alin_report.json
    (sha256 7f90b3906a786bb2...); NOTEBOOK.md entry 2026-07-24 A_lin depth ladder
  run_ids: []
  commands: []
  decisions:
  - Finding (6) is cleared as a precondition gate. It was Defect 3, not an independent
    defect.
  next_steps:
  - Do NOT re-label the gemma arm from this entry -- a disposition change is Tier
    1.
  signals: {}
- id: 002-interpretation
  at: '2026-07-24T22:40:34Z'
  kind: interpretation
  title: Accessibility and actuation windows do not overlap -- a complete account
    of the gemma null needing neither KV quarantine nor the write-side seam
  summary: 'Median rank of the true next token by relative depth (rd = hs/n_layers),
    both families CLEAN, identical code path. llama-3.2-3b (28L): hs17 rank 9, hs20
    rank 3, hs23 rank 2 (top-1 0.339), hs26 top-1 1.000. gemma-4-E4B (42L): hs22 rank
    86572, hs28 rank 8523, hs34 top-1 0.967, hs42 top-1 1.000. Gemma is not globally
    worse -- at rd ~0.81 it is AHEAD of llama (0.967 vs 0.339). It crystallizes LATE.
    Against the dose record recomputed from the registered dose_calibration_summary.json
    artifacts: the max rd with any usable dose across the program is 0.607 (llama
    hs17); gemma''s selected_doses is {} at every tested site (rd 0.810/0.905/1.000).
    So writes actuate only at rd<=0.607 while gemma is linearly accessible only at
    rd>=~0.81 -- the windows do not intersect. This is the ''linear accessibility
    / crystallization gap'' the quarantine draft already named as the strongest competitor
    to KV sharing, now with cross-family numbers. STANDING: observational depth contrast
    on two families, one anchor, one lens; it does NOT establish that low A_lin CAUSES
    write-inertness, only that gemma has no depth where both conditions hold. Vocab
    sizes differ 2x so absolute ranks are not cross-family comparable, though the
    rank 9 vs 86572 gap survives that by three orders of magnitude.'
  evidence:
  - analysis/crystallization-ladder/alin_report.json; analysis-committed/*/dose_calibration_summary.json
  run_ids: []
  commands: []
  decisions:
  - 'Recorded as a measurement only. Predicts B-prime (shallow ladder at hs15/hs18)
    also fails: those sit at rank 61283/119450, deep in the inaccessible region.'
  next_steps:
  - 'Optional: extend the same ladder to mistral-7b-v03 and qwen3.5-4b from their
    existing clean extractions to test whether ''usable dose requires the true token
    within rank ~10'' holds as a predictive rule across four families.'
  signals: {}
- id: 003-blocker
  at: '2026-07-24T22:40:34Z'
  kind: blocker
  title: G0-ALIN as pre-registered cannot discriminate hs22 from hs23
  summary: 'Gemma''s clean A_lin is at the floor everywhere below hs28: top-1 exactly
    0.000 at hs15/18/20/22/24 with median ranks 61283/119450/88087/86572/144858. The
    gemma4-e4b-kv-seam-quarantine precondition G0-ALIN selects arm A3 as ''whichever
    of hs22/hs23 has the higher A_lin''. Both candidates are at chance, so the rule
    chooses between noise. Separately, DECISION_MEMO.md (14:41) predates the clean
    full-depth extraction (16:13) by 92 minutes and is stale: G0-ALIN Part 1 IS CPU-computable
    (hs22/23/24 are on disk, clean), shallow-site norms are computable, and ''both
    options require a fresh extraction'' is false. Its ''cached activations are faithful
    (cos 0.9998)'' figure appears in neither that experiment''s AMENDMENT.md nor its
    NOTEBOOK.md, and the same number is labelled VACUOUS at this experiment''s extract_anchor.py:158
    (CPU and GPU agreed only because both ran the broken path).'
  evidence:
  - analysis/crystallization-ladder/alin_report.json; experiments/gemma4-e4b-kv-seam-quarantine/DECISION_MEMO.md;
    extract_anchor.py:158
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Adjudicating the G0-ALIN defect belongs to that experiment's own draft, not to
    this notebook entry.
  signals: {}
- id: 004-checkpoint
  at: '2026-07-29T16:13:56Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'kv-seam Phase A launch stalled at runtime-provenance boundary. Signed
    gemma4-e4b-kv-seam-quarantine (22 pins) merged; Phase A approved on local 3090.
    Three launch blockers resolved in sequence: Docker Desktop two-daemon socket switch,
    missing accelerate (tuner PR 148), transformers 5.12.1 dropped Gemma4 kv_shared_layer_index
    which the pinned kv_seam_patch.py reads (user chose align-runtime-to-5.5.0; tuner
    PR 149 added TRANSFORMERS_VERSION build-arg; mechinterp-runner:tf550 built at
    15:13Z, digest 479b7ca7891a). ADJUDICATION: smoke_summary.seam_pair.json and runlog/smoke/*
    written 14:34Z under a pre-tf550 unrecorded runtime are SUPERSEDED validity evidence
    (g0_smoke_pass true but not citable); Stage 1 re-runs in-image under tf550, and
    the 2026-07-25 preflight 6/6 PASS is likewise superseded pending in-image re-run.
    STALL: runner subagent parked at 15:09Z waiting on build-completion/Monitor notifications
    that never delivered; nothing on GPU/CPU since. sendmessage_idle_guard.sh self-deadlock
    bug found: a hook-DENIED SendMessage attempt is still recorded in the sender transcript
    and counted as an outbound, so once one send is blocked no later send can ever
    pass (agent already idle, will never emit a new idle signal). Awaiting user decision:
    patch/suspend hook vs stop runner; do not spawn duplicate runners (user directive).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-checkpoint
  at: '2026-07-30T00:04:24Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'kv-seam Phase A through Stage 4 relaunch. Guard hook patched (denied SendMessage
    no longer counts as outbound; user-approved), runner woken; Stage 1 re-run under
    tf550 PASSED (identical to superseded pre-tf550 numbers, consistent with preflight
    ON-bit-identity), preflight 6/6 in-image recorded superseding the 2026-07-25 PASS.
    Stage 2 full seam_pair ON: A3 hs22 tighten 99/168=0.589 [0.514,0.661] cost 1/270
    collapse 0; A5 hs24 tighten 123/168=0.732 [0.661,0.793] cost 9/270=0.033 collapse
    6/176=0.0341; primary block G1/G2 PASS but top-level primary_pass FALSE via g0_smoke_pass
    zero-collapse conjunct (gates.yaml smoke_no_collapse); fired-only G2 NOT-ADJUDICABLE
    both sites (n=2, n=9 vs floor 35) with over-cap discrepancy flag raised (hs24
    fired-only 9/9); disposition deferred to Stage 6. Stage 3 undosed baselines pristine
    both sites (0/168 tighten, 0/270 cost, 438/438). RunLog complete:false resolved
    as expected steady state (run_contrast never calls finalize). 529 storm cost ~3h
    (runner died twice, zero state loss). Stage 4 v1 crashed 58s in: pinned run_placebo
    omitted hs_index stamp (never-re-gate path skips compute_gate_decisions); zero
    placebo rows executed; lead REPIN via bin/exp repin, run_contrast.py 83a70405->14687efd,
    audited reason, one-line stamp fix; runner independently verified hash+audit+validate;
    convergent independent diagnoses lead/runner. hs22 SC1 ledger snapshot accepted
    lab-notebook tier (5/5 accepted in 20 draws; hs24 5/5 in 17); shared-ledger-filename
    clobber wart DEFERRED (placebos do not recur in Phase B; ledger reconstructible
    from registered seeds). Stage 4 v2 launched 00:02:23Z, first placebo row durably
    written 00:03:46Z (past prior crash point), ~4380 generations ETA several hours.
    Remaining: Stage 5a/5b shallow ladder, Stage 6 rollup, then Phase B.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-checkpoint
  at: '2026-07-30T11:57:10Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Paper-program parallel sprint while kv-seam Stage 5a calibrates: six subagent
    memos delivered and lead-verified (series-plan staleness audit docs/review/series-plan-staleness-audit-2026-07-30.md:
    33 experiments mapped, paper-5 rewrite preconditions met since 07-13, H6 resolved
    as h6-genstream-hook-firing-check with neither gen_stream path certified; p3 census
    integration already merged 07-18, one section-6 ownership edit remains; p1 vocabulary
    clean, citation currency only; p2-p4 zero numeric contradictions, three precision
    fixes; figure inventory: 21 figures, legacy numbering, paper-2 raw inputs never
    committed (containment-correct fix is aggregate snapshots, not raw commits), paper-3
    hand-typed constants, cross-paper embed bug p3->p2; arXiv pipeline pilot WORKS:
    paper 4 builds 28pp PDF + arxiv tarball on branch infra/paper-build-pipeline,
    pandoc 3.10.1 + tectonic 0.17.0 pinned, not pushed). Stage 4 placebo adjudication
    recorded earlier stands: A3 PASS-DEGENERATE candidate, A5 effect_ratio 1.14 vs
    3.0 floor. PI discussion on paper 5: confirmed doubt residue lives only in stale
    plan.md + historical filenames; manuscript already KU-vocabulary with title candidates
    staged. PI questions logged: does mid-band even need the gate (factorial: permuted-GATE
    keeps most benefit; gate = margin-tightener at mid-band, essential at overdrive);
    clarified permuted-gate randomizes ROW SELECTION not direction (random DIRECTIONS
    still fail at healthy sites, direction-specificity intact); PI wants (a) explicit
    boxed mid-band recipe in paper 5, (b) possible constructed-direction optimization
    cell (precedent caution: M4c constructive search lost specificity), (c) small
    pre-registered naming battery to define the abstention direction empirically instead
    of vibing (dose-response, negative dose, hard-known vs easy-known cost, output-form
    at sub-flip doses) rather than keeping the unearned caution label. Stage 5a at
    hs40 block, near completion.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-checkpoint
  at: '2026-07-30T14:28:28Z'
  kind: checkpoint
  title: Pre-restart pause checkpoint
  summary: 'kv-seam 5b full run finishing (hs15/hs18 438/438 done, hs20 in flight);
    D4/A6 hs23 adjudicated dose-viability NOT-RUN (zero usable rungs, collapse 0.125
    on all confab-clearing rungs); hs40 late null expected/skipped. write-direction-naming-battery
    SIGNED (PR #355 open, merge pending PI approval; all predictors row 4 + O-1; GPU
    queued behind Phase A/B). Outreach: contact refresh (204 rows), wave-1 tokens
    (14, verified), LinkedIn 14/14, 5-step HubSpot sequence in docs/preparation/outreach-plan-2026-07-30.md;
    clock held until papers ship. Runner instructed to HOLD after 5b completes (user
    machine restart); Stage 6 lead adjudication post-restart.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
track: j-space read-then-actuate
---
# A_lin depth ladder: finding (6) dissolved; accessibility and actuation windows do not overlap

## Question

Does gemma-4-E4B's logit lens fail on CLEAN activations (finding 6 real), or only on the use_cache=False corrupt extraction (finding 6 = Defect 3)?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-result - Finding (6) DISSOLVED: the logit-lens failure reproduces only on use_cache=False activations

- at: `2026-07-24T22:40:09Z`
- kind: `result`
- summary: A_lin (top-1 of final_norm+unembed at the anchor, target = the model's own recorded greedy next token) recomputed on the CLEAN gemma extraction (forward_use_cache: True, all 43 indices, 806 rows) vs the QUARANTINED corrupt one, identical harness. CLEAN: hs34 0.967, hs38 0.968, hs40 0.970, hs42 1.000, all median rank 1. CORRUPT, same depths: 0.000 across the board, median ranks 110692/204746/85073/3563. Live .logits, n=200: use_cache=True -> 1.000 (rank 1); use_cache=False -> 0.000 (median rank 2333). The reported finding-(6) signature (top-1 2.9%, true token rank 6227) reproduces ONLY on the corrupt path. Gemma's output path is not broken; it was measured through KV-starved blocks, since the corrupt extraction held only hs34/38/40/42, all inside the corrupted region (>=hs25). Harness validated by the terminal-layer tautology in both families (gemma hs42 1.000, llama hs26 1.000) plus distinct-storage and non-zero vacuity guards.
- evidence:
  - `experiments/j-space-cross-family-layer-contrast/analysis/crystallization-ladder/alin_report.json (sha256 7f90b3906a786bb2...); NOTEBOOK.md entry 2026-07-24 A_lin depth ladder`
- decisions:
  - Finding (6) is cleared as a precondition gate. It was Defect 3, not an independent defect.
- next steps:
  - Do NOT re-label the gemma arm from this entry -- a disposition change is Tier 1.
### 002-interpretation - Accessibility and actuation windows do not overlap -- a complete account of the gemma null needing neither KV quarantine nor the write-side seam

- at: `2026-07-24T22:40:34Z`
- kind: `interpretation`
- summary: Median rank of the true next token by relative depth (rd = hs/n_layers), both families CLEAN, identical code path. llama-3.2-3b (28L): hs17 rank 9, hs20 rank 3, hs23 rank 2 (top-1 0.339), hs26 top-1 1.000. gemma-4-E4B (42L): hs22 rank 86572, hs28 rank 8523, hs34 top-1 0.967, hs42 top-1 1.000. Gemma is not globally worse -- at rd ~0.81 it is AHEAD of llama (0.967 vs 0.339). It crystallizes LATE. Against the dose record recomputed from the registered dose_calibration_summary.json artifacts: the max rd with any usable dose across the program is 0.607 (llama hs17); gemma's selected_doses is {} at every tested site (rd 0.810/0.905/1.000). So writes actuate only at rd<=0.607 while gemma is linearly accessible only at rd>=~0.81 -- the windows do not intersect. This is the 'linear accessibility / crystallization gap' the quarantine draft already named as the strongest competitor to KV sharing, now with cross-family numbers. STANDING: observational depth contrast on two families, one anchor, one lens; it does NOT establish that low A_lin CAUSES write-inertness, only that gemma has no depth where both conditions hold. Vocab sizes differ 2x so absolute ranks are not cross-family comparable, though the rank 9 vs 86572 gap survives that by three orders of magnitude.
- evidence:
  - `analysis/crystallization-ladder/alin_report.json; analysis-committed/*/dose_calibration_summary.json`
- decisions:
  - Recorded as a measurement only. Predicts B-prime (shallow ladder at hs15/hs18) also fails: those sit at rank 61283/119450, deep in the inaccessible region.
- next steps:
  - Optional: extend the same ladder to mistral-7b-v03 and qwen3.5-4b from their existing clean extractions to test whether 'usable dose requires the true token within rank ~10' holds as a predictive rule across four families.
### 003-blocker - G0-ALIN as pre-registered cannot discriminate hs22 from hs23

- at: `2026-07-24T22:40:34Z`
- kind: `blocker`
- summary: Gemma's clean A_lin is at the floor everywhere below hs28: top-1 exactly 0.000 at hs15/18/20/22/24 with median ranks 61283/119450/88087/86572/144858. The gemma4-e4b-kv-seam-quarantine precondition G0-ALIN selects arm A3 as 'whichever of hs22/hs23 has the higher A_lin'. Both candidates are at chance, so the rule chooses between noise. Separately, DECISION_MEMO.md (14:41) predates the clean full-depth extraction (16:13) by 92 minutes and is stale: G0-ALIN Part 1 IS CPU-computable (hs22/23/24 are on disk, clean), shallow-site norms are computable, and 'both options require a fresh extraction' is false. Its 'cached activations are faithful (cos 0.9998)' figure appears in neither that experiment's AMENDMENT.md nor its NOTEBOOK.md, and the same number is labelled VACUOUS at this experiment's extract_anchor.py:158 (CPU and GPU agreed only because both ran the broken path).
- evidence:
  - `analysis/crystallization-ladder/alin_report.json; experiments/gemma4-e4b-kv-seam-quarantine/DECISION_MEMO.md; extract_anchor.py:158`
- next steps:
  - Adjudicating the G0-ALIN defect belongs to that experiment's own draft, not to this notebook entry.
### 004-checkpoint - Checkpoint

- at: `2026-07-29T16:13:56Z`
- kind: `checkpoint`
- summary: kv-seam Phase A launch stalled at runtime-provenance boundary. Signed gemma4-e4b-kv-seam-quarantine (22 pins) merged; Phase A approved on local 3090. Three launch blockers resolved in sequence: Docker Desktop two-daemon socket switch, missing accelerate (tuner PR 148), transformers 5.12.1 dropped Gemma4 kv_shared_layer_index which the pinned kv_seam_patch.py reads (user chose align-runtime-to-5.5.0; tuner PR 149 added TRANSFORMERS_VERSION build-arg; mechinterp-runner:tf550 built at 15:13Z, digest 479b7ca7891a). ADJUDICATION: smoke_summary.seam_pair.json and runlog/smoke/* written 14:34Z under a pre-tf550 unrecorded runtime are SUPERSEDED validity evidence (g0_smoke_pass true but not citable); Stage 1 re-runs in-image under tf550, and the 2026-07-25 preflight 6/6 PASS is likewise superseded pending in-image re-run. STALL: runner subagent parked at 15:09Z waiting on build-completion/Monitor notifications that never delivered; nothing on GPU/CPU since. sendmessage_idle_guard.sh self-deadlock bug found: a hook-DENIED SendMessage attempt is still recorded in the sender transcript and counted as an outbound, so once one send is blocked no later send can ever pass (agent already idle, will never emit a new idle signal). Awaiting user decision: patch/suspend hook vs stop runner; do not spawn duplicate runners (user directive).
### 005-checkpoint - Checkpoint

- at: `2026-07-30T00:04:24Z`
- kind: `checkpoint`
- summary: kv-seam Phase A through Stage 4 relaunch. Guard hook patched (denied SendMessage no longer counts as outbound; user-approved), runner woken; Stage 1 re-run under tf550 PASSED (identical to superseded pre-tf550 numbers, consistent with preflight ON-bit-identity), preflight 6/6 in-image recorded superseding the 2026-07-25 PASS. Stage 2 full seam_pair ON: A3 hs22 tighten 99/168=0.589 [0.514,0.661] cost 1/270 collapse 0; A5 hs24 tighten 123/168=0.732 [0.661,0.793] cost 9/270=0.033 collapse 6/176=0.0341; primary block G1/G2 PASS but top-level primary_pass FALSE via g0_smoke_pass zero-collapse conjunct (gates.yaml smoke_no_collapse); fired-only G2 NOT-ADJUDICABLE both sites (n=2, n=9 vs floor 35) with over-cap discrepancy flag raised (hs24 fired-only 9/9); disposition deferred to Stage 6. Stage 3 undosed baselines pristine both sites (0/168 tighten, 0/270 cost, 438/438). RunLog complete:false resolved as expected steady state (run_contrast never calls finalize). 529 storm cost ~3h (runner died twice, zero state loss). Stage 4 v1 crashed 58s in: pinned run_placebo omitted hs_index stamp (never-re-gate path skips compute_gate_decisions); zero placebo rows executed; lead REPIN via bin/exp repin, run_contrast.py 83a70405->14687efd, audited reason, one-line stamp fix; runner independently verified hash+audit+validate; convergent independent diagnoses lead/runner. hs22 SC1 ledger snapshot accepted lab-notebook tier (5/5 accepted in 20 draws; hs24 5/5 in 17); shared-ledger-filename clobber wart DEFERRED (placebos do not recur in Phase B; ledger reconstructible from registered seeds). Stage 4 v2 launched 00:02:23Z, first placebo row durably written 00:03:46Z (past prior crash point), ~4380 generations ETA several hours. Remaining: Stage 5a/5b shallow ladder, Stage 6 rollup, then Phase B.
### 006-checkpoint - Checkpoint

- at: `2026-07-30T11:57:10Z`
- kind: `checkpoint`
- summary: Paper-program parallel sprint while kv-seam Stage 5a calibrates: six subagent memos delivered and lead-verified (series-plan staleness audit docs/review/series-plan-staleness-audit-2026-07-30.md: 33 experiments mapped, paper-5 rewrite preconditions met since 07-13, H6 resolved as h6-genstream-hook-firing-check with neither gen_stream path certified; p3 census integration already merged 07-18, one section-6 ownership edit remains; p1 vocabulary clean, citation currency only; p2-p4 zero numeric contradictions, three precision fixes; figure inventory: 21 figures, legacy numbering, paper-2 raw inputs never committed (containment-correct fix is aggregate snapshots, not raw commits), paper-3 hand-typed constants, cross-paper embed bug p3->p2; arXiv pipeline pilot WORKS: paper 4 builds 28pp PDF + arxiv tarball on branch infra/paper-build-pipeline, pandoc 3.10.1 + tectonic 0.17.0 pinned, not pushed). Stage 4 placebo adjudication recorded earlier stands: A3 PASS-DEGENERATE candidate, A5 effect_ratio 1.14 vs 3.0 floor. PI discussion on paper 5: confirmed doubt residue lives only in stale plan.md + historical filenames; manuscript already KU-vocabulary with title candidates staged. PI questions logged: does mid-band even need the gate (factorial: permuted-GATE keeps most benefit; gate = margin-tightener at mid-band, essential at overdrive); clarified permuted-gate randomizes ROW SELECTION not direction (random DIRECTIONS still fail at healthy sites, direction-specificity intact); PI wants (a) explicit boxed mid-band recipe in paper 5, (b) possible constructed-direction optimization cell (precedent caution: M4c constructive search lost specificity), (c) small pre-registered naming battery to define the abstention direction empirically instead of vibing (dose-response, negative dose, hard-known vs easy-known cost, output-form at sub-flip doses) rather than keeping the unearned caution label. Stage 5a at hs40 block, near completion.
### 007-checkpoint - Pre-restart pause checkpoint

- at: `2026-07-30T14:28:28Z`
- kind: `checkpoint`
- summary: kv-seam 5b full run finishing (hs15/hs18 438/438 done, hs20 in flight); D4/A6 hs23 adjudicated dose-viability NOT-RUN (zero usable rungs, collapse 0.125 on all confab-clearing rungs); hs40 late null expected/skipped. write-direction-naming-battery SIGNED (PR #355 open, merge pending PI approval; all predictors row 4 + O-1; GPU queued behind Phase A/B). Outreach: contact refresh (204 rows), wave-1 tokens (14, verified), LinkedIn 14/14, 5-step HubSpot sequence in docs/preparation/outreach-plan-2026-07-30.md; clock held until papers ship. Runner instructed to HOLD after 5b completes (user machine restart); Stage 6 lead adjudication post-restart.
