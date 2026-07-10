---
schema_version: research-session/v1
session_id: 20260704T120000Z-amendment-aj-erasure-category-geometry-fleet
title: Amendment AJ resolved (caution survives certified knowledge erasure) + category-geometry
  MI fleet
status: complete
created_at: '2026-07-04T12:00:00Z'
updated_at: '2026-07-04T15:30:00Z'
track: research
question: Does the caution readout survive certified erasure of the knowledge subspace,
  and does unanswerability FLAVOR (category) have its own linear structure in the
  raw base?
tags:
- paper3
- mech-interp
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: 'AJ RESOLVED: caution is not reducible to the knowledge readout
    (0.858 post-LEACE vs 0.912 baseline; certificate 0.996 -> 0.496); knowledge carries
    a small quantified share (5.4 +/- 0.6 pts) that landed exactly on the pre-stated
    0.05 gate line. Category fleet: flavor is linearly readable from L1 (0.946 macro-AUROC
    at L34), doubt geometry is a shared trunk with per-flavor branches, pliability
    is one curve with category threshold offsets plus a controversial-flavor anomaly.'
  changed_by_session: Paper3 Section 5/9 rank-1 caveat lifted and replaced by a linear-only
    erasure caveat (PR 190); prediction scoreboard gains the aim-small-miss-small
    threshold rule; backlog item 22 executed, item 22a (controversial flip anomaly)
    queued.
checkpoints:
- id: 001-decision
  at: '2026-07-04T12:10:00Z'
  kind: decision
  title: 'AJ signed and launched: dual predictions recorded (both SURVIVES), CPU-only
    run on cached tensors'
  summary: User prediction recorded pre-launch ("AJ survived I agree worth being optimistic
    here"), orchestrator ~85 percent SURVIVES. Loader row-key sanitization bug (double-colon
    vs double-underscore separators) found and fixed pre-launch (PR 187), gates untouched.
    Janitor pass in parallel - results-provenance-inventory retired with pointer to
    the per-paper appendices, paper3 de-narrated (PR 188).
- id: 002-result
  at: '2026-07-04T13:20:00Z'
  kind: result
  title: AJ run landed in the pre-registered ambiguous zone; Addendum A1 showed the
    gap sits ON the threshold; user adjudicated SURVIVES (PRs 189, 190)
  summary: 'Certificate PASS first try (knowledge probe 0.996 -> 0.496 OOF, no fallback
    knobs); caution survives at 0.858 CI [0.823, 0.890] (baseline 0.912), falsifier
    (<0.65) nowhere in sight. But the random-control gap came in 0.053 vs the locked
    <= 0.05, a 0.003 miss. Addendum A1 (gate-free, user requested): gap = 0.0538 +/-
    0.0060 across 24 CV seeds (29 percent of seeds pass), bootstrap P(gap <= 0.05)
    = 0.415 - the statistic is statistically indistinguishable from the threshold.
    User adjudicated SURVIVES with the dependency quantified; scoreboard TIE/TIE (tally
    user 3, orchestrator 2, ties 1). Process lesson recorded: aim small miss small
    - derive gate thresholds from expected effect size and uncertainty, never round
    .0/.5 defaults. Descriptive: INLP never certifies (0.813 at k=40), the knowledge
    concept is hydra-redundant too; the whitened closed-form eraser was necessary.
    Paper3 Section 5/9 caveat lifted (PR 190).'
- id: 003-observation
  at: '2026-07-04T15:00:00Z'
  kind: observation
  title: 'Category-geometry MI fleet (backlog item 22, 3 CPU agents on the AH 18.5k
    surface): flavor readable from L1, shared trunk + per-flavor branches, one pliability
    curve with category offsets'
  summary: 'Tier-1 lab-notebook, scripts now in experiments/flavor-geometry-category-fleet/analysis-committed/category-geometry/
    (cache: 11,996 rows x L0-L36; 5,264 categorized unknowns, 6 canonical flavors;
    6,000 known sample). (1) FLAVOR READOUT: flavor is linearly readable, macro-OvR-AUROC
    0.946 at L34 (perm chance 0.495, acc 0.772 vs 0.197 majority); already 0.904 at
    L1, essentially flat after L10 - flavor is an early content encoding, not a late
    computation. Guards: within single-source 0.953 (not a source artifact); TF-IDF
    text baseline reaches 0.921, so activation excess is only +0.025 - flavor is largely
    surface-recoverable question content. Confusions: counterfactual and future_unknown
    crisp (0.97), unsolved_problem smeared into controversial (0.64 diagonal). (2)
    CATEGORY GEOMETRY (L20/24/28): for a linear known/unknown detector there is ONE
    axis - cross-flavor transfer AUROC within ~1pt of diagonal (0.988 vs 0.998). But
    whitened per-flavor doubt directions align at only ~0.71 mean cosine; after projecting
    out the shared trunk every flavor keeps 20-42 percent of direction norm whose
    residual alone still separates its unknowns at 0.69-0.91 AUROC. Counterfactual
    is the geometric outlier (cos down to 0.575, strongest residual 0.91). Frozen
    AH probe reads five flavors at 0.98-0.99 but under-flags ambiguous (0.92; median
    ambiguous unknown scores 0.19 = looks answerable). Known/unknown split is also
    a dataset split (uniform across flavors - affects trunk magnitude, not between-flavor
    structure). (3) PLIABILITY (AH gen arms): baseline refusal is one curve in caution
    boundary distance (AUROC 0.956; per-flavor 0.90-0.97) with significant category
    THRESHOLD offsets (LR p=0.004, no slope interaction p=0.35): future_unknown refused
    93 percent vs controversial/unsolved ~68 percent; confab rates mirror it (31-33
    percent vs 7 percent). Certainty-prime release uptake follows boundary distance
    (AUROC 0.146, inverted as expected) except CONTROVERSIAL: within-flavor z-AUROC
    0.34 vs 0.08-0.17 elsewhere, highest flip rate 25 percent, interaction p=0.026
    - controversial flips for reasons the caution axis does not capture. Instrument
    note: AH prime arm is collinear with contrast and gold class, so within-arm analyses
    are the clean ones. Agent-ops note: the flavor agent duplicated its own run 5x
    without killing priors (fixed by hand); full-dim 2560 lbfgs probes are unusable
    on this box - PCA-128 + saga is the pattern (memory saved).'
- id: 004-decision
  at: '2026-07-04T14:06:00Z'
  kind: decision
  title: 'Backlog item 22a queued (user directive): controversial-flavor flip anomaly,
    CPU-first predictor hunt (PR 191)'
  summary: What predicts controversial flips if not boundary distance - knowledge-probe
    score, surface features, or the per-flavor residual direction from the geometry
    arm? Then a targeted steering/patching cell if a direction emerges (gates with
    item-22 Tier-3 follow-ups).
artifacts:
- experiments/knowledge-subspace-erasure/AMENDMENT.md
- archive/experiment/phase1/probe/amendments/amendment_aj_subspace_erasure.py
- archive/experiment/phase1/probe/amendments/amendment_aj_addendum_gap_distribution.py
- archive/experiment/phase1/probe/mi_category_geometry_prep.py
- experiments/flavor-geometry-category-fleet/analysis-committed/category-geometry/ (committed scripts;
  scripts committed)
- docs/prediction-scoreboard.md
legacy_session:
  id: '0036'
  path: docs/sessions/0036 - amendment-aj-erasure-category-geometry-fleet.md
---
# Session 0036: Amendment AJ resolution + category-geometry fleet

Two arcs, both CPU-only while the Amendment AI TRUE arm held the GPU.

**Amendment AJ.** The paper3 Section 9 rank-1 reducibility caveat is answered:
certified LEACE erasure of everything a linear probe can read about gold
answerability (0.996 -> 0.496) leaves the caution readout at 0.858 held-out.
The pre-stated gap condition (<= 0.05 vs equal-rank random erasure) missed by
0.003, and the gate-free Addendum A1 showed the true gap sits statistically on
the line (0.0538 +/- 0.0060 across seeds, bootstrap pass probability 0.415).
User adjudicated SURVIVES with the dependency quantified. Both predictions
called strict G2 PASS: scored TIE/TIE. The durable process lesson - aim small
miss small: never lock a gate on a round-number threshold the expected effect
can sit on - is recorded in the scoreboard.

**Category-geometry fleet (item 22).** Three parallel analysts on a shared
11,996-row x 37-layer cache of the AH surface. Unanswerability flavor is
linearly readable near-ceiling from very early depth, but a text baseline gets
most of it: it is an encoding of question content, not a late-computed state.
The doubt axis is one trunk for detection with real per-flavor branches
(counterfactual most distinct); the frozen knowledge probe systematically
under-flags ambiguous questions. Behavior consults the trunk plus per-flavor
thresholds; the certainty prime's release action on controversial questions
rides something the caution axis misses (item 22a). Tier-3 follow-ups
(category steering/patching, SAE basis) now have three concrete targets:
the counterfactual residual direction, the ambiguous under-flag, and the
controversial flip anomaly.
