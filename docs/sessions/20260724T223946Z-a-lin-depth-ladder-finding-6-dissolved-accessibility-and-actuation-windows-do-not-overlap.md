---
schema_version: research-session/v1
session_id: 20260724T223946Z-a-lin-depth-ladder-finding-6-dissolved-accessibility-and-actuation-windows-do-not-overlap
title: 'A_lin depth ladder: finding (6) dissolved; accessibility and actuation windows
  do not overlap'
status: complete
created_at: '2026-07-24T22:39:46Z'
updated_at: '2026-07-24T22:40:34Z'
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
