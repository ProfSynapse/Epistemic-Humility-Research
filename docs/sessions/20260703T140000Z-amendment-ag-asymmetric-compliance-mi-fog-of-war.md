---
schema_version: research-session/v1
session_id: 20260703T140000Z-amendment-ag-asymmetric-compliance-mi-fog-of-war
title: Amendment AG resolved (asymmetric compliance) + mech-interp fog-of-war fleet
status: complete
created_at: '2026-07-03T14:00:00Z'
updated_at: '2026-07-03T18:30:00Z'
phase: phase1
question: "What is the AF prime made of \u2014 compliance with a credible instruction\
  \ or resonance with the model's own read-out \u2014 and what does the caution machinery\
  \ it acts on look like from inside?"
tags:
- paper5
- mech-interp
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: 'AG RESOLVED asymmetric compliance (muzzle obeyed +34pt, release
    resisted +7.9pt); belief-vs-policy dissociation instrumented; MI fleet mapped
    the substrate: off-axis prime write, hydra-redundant caution, boundary-distance
    pliability unifies both compliance directions'
  changed_by_session: AF's effect adjudicated as authority-driven policy compliance,
    not belief revision; capacity confound on release resistance demoted (basin depth
    accounts for it); AA steering flatness gets a mechanistic explanation (single
    direction vs redundant hydra)
checkpoints:
- id: 001-decision
  at: '2026-07-03T15:30:00Z'
  kind: decision
  title: 'AG signed: gates locked (user option "B"), Stage-0 recorded, doubt/caution
    instrumentation added (PR 164)'
  summary: Stage-0 conditional-compliance analysis of AF's permuted arm showed asymmetric
    half-dose compliance (wrong muzzle +36.6pt, wrong pro-answer +7.6pt), so the single-band
    draft gate was replaced pre-signing (inside the declared recalibration window)
    with two directional gates (G1a muzzle >= +20pt, G1b asymmetry >= +15pt). User
    prediction recorded pre-result ("pure behavior not internal alignment"). Section
    8 added at user request - gate-free doubt/caution axis measurement under baseline/HIGH/LOW
    renderings.
- id: 002-launch
  at: '2026-07-03T16:10:00Z'
  kind: launch
  title: AG inverted arm + two primed extraction passes launched on the 3090 (explicit
    user approval)
  summary: Batch-1 byte-identical harness delta on AF (inversion applied to certainty_true;
    audited 0/600 mismatches). 600-row inverted generation ~45 min; two forward-only
    primed extractions ~35 min. Runner, state-analyst, and red-team agents did all
    build/run/audit work under the orchestrator policy; lead only verified and adjudicated.
- id: 003-result
  at: '2026-07-03T17:30:00Z'
  kind: result
  title: 'AG RESOLVED: ASYMMETRIC COMPLIANCE; belief unmoved, compliance travels through
    the caution axis (PR 165)'
  summary: G1a PASS +34.0pt CI [26.5, 41.5]; G1b PASS +26.1pt CI [18.0, 34.6]; release
    only +7.9pt; AG-G2 22/279 induced confabulations; degeneracy 0. Opus red-team
    recomputed everything with zero mismatches. Section 8 instrumentation - the prime
    does NOT rewrite the doubt self-assessment (small anti-semantic shifts; flipped-vs-resisted
    AUROC 0.478) but muzzle compliance is predicted by the caution axis (delta 0.654;
    audit refinement - baseline caution predisposition is stronger at 0.749). Knows-it-knows-obeys-anyway.
- id: 004-result
  at: '2026-07-03T17:45:00Z'
  kind: result
  title: 'Neutral-prepend control: any-prepend component real; prime differential
    semantically coherent on caution (PR 166)'
  summary: A token-matched neutral sentence alone shifts the caution projection -0.34z
    (known) / -0.65z (unknown) - the generic component carries most of the raw shift.
    Re-referenced to neutral, HIGH moves caution down and LOW moves it up (semantically
    correct, matching behavior) while the doubt axis stays anti-semantic. The belief-vs-policy
    dissociation sharpened. Residual - single neutral sentence, not a panel.
- id: 005-observation
  at: '2026-07-03T18:10:00Z'
  kind: observation
  title: 'MI fog-of-war fleet (4 CPU agents on existing tensors): off-axis write,
    hydra caution, boundary-distance pliability'
  summary: 'Exploratory, lab-notebook tier, scratch preserved in analysis/mi_exploration_20260703/.
    (1) GEOMETRY: 92-99 percent of the prime''s mean-squared displacement at the pre-gen
    anchor lies OFF the doubt/caution_perp plane (mean-cosine ~0 at L24, dimension-free);
    the readable dial motion is a thin shadow. (2) DISPLACEMENT STRUCTURE: HIGH/LOW
    write near-identical shifts L1-L9 (the generic prepend), split semantically at
    L10 (cos drops 0.92->0.73), share cos ~0.67 after; unexpected late reversal -
    LOW writes larger late-layer displacement than HIGH from L25 on; LOW is mildly
    content-targeted, HIGH is label-blind. (3) HYDRA RANK: 40 iterative within-fold
    direction removals never push held-out refusal AUROC below ~0.90 (permuted control
    flat 0.50); caution is redundantly re-encoded across dozens of directions, first
    component fold-stable 0.68-0.72, structured tail. Doubt is a strong correlate
    (AUROC 0.88, R^2 ~0.5, every component loads ~-0.7 on doubt) but NOT a removable
    element (projecting it out costs exactly a random direction''s worth: ~0.000).
    (4) PLIABILITY UNIFICATION: baseline caution distance-from-boundary predicts compliance
    in BOTH directions and BOTH cells (muzzle kca 0.749; release on unknowns 0.843
    - the strongest cell); cell geography is an orderly gradient (kca -0.69z, kr +0.73z,
    ur +1.22z); one pooled distance curve fits both cells (AUROC 0.823, cell indicator
    adds +0.016 CI [-0.010, +0.043] n.s.). AG''s release resistance is basin depth,
    not (primarily) capacity - the capacity confound is demoted, not excluded (22/279
    released unknowns confabulated).'
- id: 006-infrastructure
  at: '2026-07-03T18:00:00Z'
  kind: infrastructure
  title: 'Housekeeping cleared (PR 167): backlog filter, research-trajectory rewrite,
    item 10 found already fixed'
  summary: build_backlog_index.py filters main/master from the other-worktrees line;
    living docs/research-trajectory.md rewritten from amendment Status/RESULT lines
    (old protocol-dir file kept as historical with pointer); compute_revised saturation
    fix discovered already landed in steering_common.py with a green regression test
    - backlog row predated it. Session ran fully delegated - 7 subagents (runner,
    state-analyst, red-team, neutral-control, 4 MI analysts, housekeeper); lead adjudicated,
    committed, merged PRs 164-167.
next_actions:
- 'Draft Amendment AH (divergent-pool, probe != gold): the only clean own-readout
  vs gold-instruction separator; pliability result adds a per-row prediction (flip
  probability ~ boundary distance) the design can exploit.'
- 'Generation-time geometry follow-up (lab): the off-axis claim holds at the pre-gen
  anchor only; check whether the prime''s write becomes readable at generation-time
  positions (tensors would need one extraction pass).'
- 'Sentence-panel neutral control (lab, cheap): bound sentence-choice variance on
  the single-sentence neutral result.'
- 'SAE decomposition of caution (backlog item 8, cloud): the hydra result says linear
  rank is high; SAE features are the natural next basis and directly test compound-caution''s
  decomposability prediction.'
- 'Paper 5 framing note (CORRECTED): redundancy explains why reading is robust (S-Z
  arc). Do NOT generalize to "single-direction writes fail": AA''s ADDITIVE activation
  write was flat, but AC is a single-direction activation erase-write on caution_perp
  that SUCCEEDED (+8.7pt). AF/AG are prompt/text-channel primes, a separate channel,
  not activation writes. The honest split is by axis and write-form and outcome, not
  a clean input-vs-write binary.'
- 'AD stays signed-on-shelf (user: not interesting under the training-free focus).'
legacy_session:
  id: '0035'
  path: docs/sessions/0035 - amendment-ag-asymmetric-compliance-mi-fog-of-war.md
---
# Session 0035 — Amendment AG + the mech-interp fog-of-war fleet

Arc: AG went signing → launch → resolution → audit → merge in one afternoon
(PRs 164–166), landing ASYMMETRIC COMPLIANCE with both gates passed and the
user's pre-registered prediction ("pure behavior not internal alignment")
confirmed one level deeper: the prime never moves the belief (doubt axis
anti-semantic, compliance-discrimination at chance), while the caution/policy
axis carries the behavioral flip. The neutral-prepend control closed the
any-prepend confound the same day: the generic component is real, but the
prime differential relative to neutral is semantically coherent on caution
only.

The second half of the session pointed four CPU agents at the tensors already
on disk. Three structural results: the prime's write at the pre-gen anchor is
almost entirely off the readable axes (the dials see a shadow); caution is a
redundant many-headed hydra that survives 40 orthogonal direction removals
(doubt is woven through every strand as a correlate but is not a removable
ingredient); and compliance in both directions collapses onto one scalar —
baseline distance from the refused/answered decision boundary — with the cell
indicator adding nothing significant. That last result demotes AG's capacity
confound: unknowns resist release mostly because they start ~0.5z deeper in
the refusal basin, and the 23 that did release were exactly the shallow ones
(AUROC 0.843).

Strategic reading for Paper 5 (CORRECTED): redundancy is why reading is robust.
AA's ADDITIVE single-direction write was flat, and the prompt (a distributed,
high-rank text-channel prime) moves behavior. But do not read this as "activation
writes fail": AC is a single-direction activation erase-write on caution_perp
that succeeded (+8.7pt), so the activation channel does actuate when it erases
and writes a validated direction. Frame by axis x write-form x outcome, not a
clean input-vs-write binary.
