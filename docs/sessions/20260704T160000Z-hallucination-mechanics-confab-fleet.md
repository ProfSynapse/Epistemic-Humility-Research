---
schema_version: research-session/v1
session_id: 20260704T160000Z-hallucination-mechanics-confab-fleet
title: Hallucination-mechanics CPU fleet (confab phenotypes, commitment signal, veto
  transport)
status: complete
created_at: '2026-07-04T16:00:00Z'
updated_at: '2026-07-04T20:00:00Z'
track: research
question: What happens mechanically between the model knowing a question is unanswerable
  (pre-gen gate 0.997) and marking its own confabulation lowest-trust (veto 0.980)
  - the commitment-and-content middle the prior results corner but do not explain?
tags:
- mech-interp
- hallucination
- paper5
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Three CPU arms on cached surfaces converged on a mechanistic picture
    of confabulation. (1) Doubt leaks into hallucination texture through SPECIFICITY,
    not hedging. (2) A pre-generation COMMITMENT SIGNAL exists beyond the caution
    threshold (matched AUROC 0.834). (3) The post-gen veto is predominantly RE-DERIVED
    from the emitted answer, orthogonal to the doubt axis; answerability is the carried
    signal.
  changed_by_session: Hallucination-mechanics line opened (TODO items 30-32); items
    30 and 31 resolved same-day on cached data with zero GPU; item 32 upgraded from
    sketch to a two-stage design (position sweep + answer-window steering) and queued
    for amendment drafting.
checkpoints:
- id: 001-decision
  at: '2026-07-04T16:00:00Z'
  kind: decision
  title: Hallucination-mechanics line opened; A/B CPU fleet launched on cached AH
    gen rows; scout found all S/T/U/W post-gen tensors intact
  summary: User directive to lift fog on hallucination mechanics with CPU work while
    the Amendment AI TRUE arm holds the GPU. Framing from session 0036 established
    that confabulations are not knowledge failures (gate fires, veto fires, decision
    is trunk plus flavor threshold), so the fleet targeted the middle. Arm A = phenotype
    taxonomy plus internal-state coupling; arm B = within-flavor caution-matched confab-vs-refuse
    signature hunt. A read-only scout confirmed the Amendment S/T/U/W extraction caches
    are complete on disk (pre AND post tensors, all 37 layers, labels, fitted probe
    coefficients), making the veto-transport analysis (item 31) CPU-only with no re-extraction.
- id: 002-result
  at: '2026-07-04T16:18:00Z'
  kind: result
  title: 'Arm A: doubt leaks into confab texture via SPECIFICITY, not hedging; doubt
    prime drove confabulation to zero'
  summary: On 309 baseline confabs (100 percent cache join), pre-gen doubt-trunk projection
    negatively predicts fabrication specificity (within-flavor rho -0.21 to -0.24,
    perm p=0.001) and length (rho -0.27) - higher internal doubt yields shorter, more
    generic fabrications. The intuitive hedging prediction failed its guard (activation
    probe 0.674 vs TF-IDF question baseline 0.642) - hedgy confabs are question-driven.
    Confabs are long and generic (50 words, low fact density) vs terse dense correct
    answers (11 words). False-premise confabs correct the premise in only 1 of 16.
    The doubt prime produced 0 confabs in 324 generations; the certainty prime raises
    confab count (459 vs 309) and length, not per-confab texture. Instrument note
    - the raw trunk projection and the frozen probe score disagree on the length coupling
    sign; not interchangeable readouts.
- id: 003-result
  at: '2026-07-04T16:34:00Z'
  kind: result
  title: 'Arm B: COMMITMENT SIGNAL found - at matched caution and flavor, pre-gen
    activations predict confab-vs-refuse at 0.834'
  summary: Null model confirms threshold dominance (caution scalar alone 0.939). But
    after within-flavor 1-to-1 caliper matching on caution distance (328 rows, post-match
    scalar 0.528), a pre-gen activation probe still predicts which row confabulates
    at AUROC 0.834 plus-minus 0.014 (perm p=0.0099), beating TF-IDF by +0.215 and
    familiarity features by +0.152 on paired folds (10 of 10 repeats), replicating
    on the full 1338-row population (0.83). Signal peaks mid-network (L24-28) and
    plateaus - argues against terminal decision leakage. Confab direction cosine to
    doubt trunk 0.32 (related, distinct). Familiarity hypothesis supported - at matched
    doubt, familiar-looking questions draw confabulations (joint proxies 0.682, p=0.0099;
    corpus-internal frequencies). Knowledge probe largely null. Trunk projection still
    reads 0.694 after scalar matching - the 1-D scalar compresses away part of the
    geometry (the 22a lesson in reverse).
- id: 004-result
  at: '2026-07-04T16:45:00Z'
  kind: result
  title: 'Veto transport (item 31): the post-gen veto is predominantly RE-DERIVED
    from the emitted answer; answerability is the carried signal'
  summary: On same-row pre/post pairs, the whole state is largely rewritten by generation
    (cosine ~0.58) and the correctness projection survives weakly (r about 0.34-0.37);
    the correctness axis fails cross-position transfer (0.58-0.64 vs 0.81-0.86 in-position)
    while the answerability axis transports near-perfectly (0.96-0.99) - answerability
    is a carried question property, correctness is not. Post beats pre (+0.022 raw
    base, +0.094 grpo-v2) and the surplus survives residualizing out every carried
    readout - a large chunk of veto signal is NEW post-generation information. The
    veto axis is orthogonal to the doubt axis (whitened cosine -0.02). Out-of-sample
    veto reproduction - dial to hallucination detection 0.784 raw base, 0.969 grpo-v2
    (matches published 0.980). The deployed GRPO-v2 checkpoint is MORE re-derived
    than the raw base (0.719 to 0.812 post-beats-pre, 0.773 after removing the carried
    part). All effect sizes held-out or cross-dataset; in-sample reapplication of
    cached probes discarded as circular.
- id: 005-decision
  at: '2026-07-04T17:00:00Z'
  kind: decision
  title: 'Synthesis: graded-failure picture of confabulation; item 32 upgraded to
    two-stage design (position sweep + answer-window steering)'
  summary: Composite picture - before generation the state already leans fabricate-vs-refuse
    beyond its doubt level (arm B); the doubt that failed to trigger refusal still
    degrades the fabrication (arm A); after emission the veto re-derives trust from
    the answer itself, on an axis orthogonal to doubt (item 31). Confabulation is
    a graded failure, not a binary one. Item 32 design implications - read the veto
    across answer-token positions to find where it crystallizes; steer the L24-28
    confab direction (orthogonalized to caution) in the answer-token window; anchor-only
    intervention moves only the carried minority; doubt and veto want different commitment
    points. Ops lesson saved to memory - harness blocks subagent Write for report
    files (heredoc workaround) and background agents must end with an explicit send
    to main.
- id: 006-result
  at: '2026-07-04T20:00:00Z'
  kind: result
  title: 'Follow-on: the commitment direction is NOT internal familiarity - familiarity
    axis whitened-orthogonal to the whole decision geometry'
  summary: Post-signing de-risk for AK Stage 2 (user-approved CPU follow-on, experiments/confab-mechanics-cpu-fleet/analysis-committed/familiarity-geometry/).
    An internal familiarity direction (Ridge of corpus-internal mean log frequency
    onto PCA-128 activations, matched set reproduced exactly at 328 rows) is whitened-orthogonal
    to EVERYTHING - cosines to the doubt trunk 0.005 to 0.031, caution axis -0.045
    to 0.010, commitment direction -0.035 to -0.020 across L20/24/28. Projecting it
    out leaves the commitment probe untouched (0.834 to 0.834, survival 1.00); its
    own projection reads confab-vs-refuse at only 0.571 (perm p=0.0099), weaker than
    the 0.682 text proxies it was fit from. The commitment direction's only geometric
    relative is the doubt trunk (whitened cos 0.64 at L20 decaying to 0.30 at L28).
    AK implication - steer the commitment direction, not a familiarity vector; a familiarity
    vector is near-orthogonal and moves a weak sub-0.6 signal. Caveats - frequency-proxy
    familiarity (rank-1, not a subspace erasure), diagonal whitening at n=328.
artifacts:
- experiments/confab-mechanics-cpu-fleet/analysis-committed/familiarity-geometry/ (committed scripts;
  script committed)
- experiments/confab-mechanics-cpu-fleet/analysis-committed/confab-phenotypes/ (committed scripts;
  script committed)
- experiments/confab-mechanics-cpu-fleet/analysis-committed/confab-signature/ (committed scripts;
  script committed)
- experiments/commitment-point/analysis-committed/veto-transport/ (committed analysis;
  scripts committed)
- TODO.md (items 30-32)
legacy_session:
  id: '0037'
  path: docs/sessions/0037 - hallucination-mechanics-confab-fleet.md
---
# Session 0037: hallucination-mechanics CPU fleet

One directive ("lift some of the fog from how hallucinations work
mechanically"), three CPU arms on cached surfaces, zero GPU used, all three
resolved same-day.

**The picture.** Our confabulations were already cornered: the model knows the
question is unanswerable before generating and distrusts its own answer
afterward. The fleet filled in the middle. Arm B found a pre-generation
commitment signal - at matched caution distance and matched flavor, the
activations still predict fabricate-vs-refuse at 0.834, on a direction only
0.32-aligned with the doubt trunk, peaking mid-network. Arm A found that the
doubt which failed to stop the fabrication still shapes it - higher doubt
yields shorter, more generic confabs (specificity leak), while hedging turned
out to be question-driven. The veto-transport analysis found the post-gen veto
is mostly re-derived from the emitted answer on an axis orthogonal to doubt,
and that post-training shifts the balance further toward re-derivation;
answerability, by contrast, is genuinely carried through generation.

**Why it matters.** Confabulation is a graded failure with three separable
mechanical stages (lean, degrade, re-derive), each now instrumented. The
familiarity result connects our surface to the entity-recognition literature.
And the design for the commitment-point experiment (item 32) is no longer a
sketch: read across answer tokens for veto crystallization, steer the confab
direction in the answer window, expect anchor-only interventions to
underperform.

**Caveats.** Single surface per claim, single seed, all readout-not-causal;
matched n=328 in arm B; regex phenotypes in arm A; W's answerability and veto
labels coincide (transported 0.905 is an upper bound); cross-family
comparisons descriptive.
