---
title: placebo-seed-distribution-census
aliases:
- 'Placebo seed-distribution census: multi-seed random-direction null at matched magnitude'
- census of matched-magnitude random-direction placebo signs across 15 seeds
tags:
- kg/experiment
- experiment
- cross-family
- doubt-snap
kg:
  id: experiment:placebo-seed-distribution-census
  type: experiment
  status: canonical
related:
- '[[abstention-wide-instrument-calibration]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[single-seed-placebo-delta-is-a-noisy-draw-from-a-wide-family-distribution]]'
- '[[dosed-detector-refusal-channel-drives-genuine-placebo-recruitment]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
relationships:
- type: builds_on
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md (Motivation and posture)
- type: supports
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md#outcome (Per-family verdicts against the pre-stated criterion)
- type: supports
  target: '[[single-seed-placebo-delta-is-a-noisy-draw-from-a-wide-family-distribution]]'
  target_id: mechanism:single-seed-placebo-delta-is-a-noisy-draw-from-a-wide-family-distribution
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md#outcome (Historical single-seed percentiles)
- type: supports
  target: '[[dosed-detector-refusal-channel-drives-genuine-placebo-recruitment]]'
  target_id: mechanism:dosed-detector-refusal-channel-drives-genuine-placebo-recruitment
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md#outcome (Cross-family observation)
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
- type: related_to
  target: '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
  target_id: mechanism:random-direction-placebo-recruits-additional-wide-instrument-abstention
  confidence: high
---

Registered successor to `abstention-wide-instrument-calibration` (resolved
2026-07-14) and to two intervening single-seed / three-seed measurements
that are not themselves library nodes: `rr3-corrected-placebo-replication`
(resolved FALSIFIED 2026-07-14), whose three fresh mistral seeds spread
-7.4 to +21.8 points and first raised the seed-noise question the census
answers, and `placebo-signflip-question-type-analysis` (resolved
2026-07-14), which confirmed the qwen suppression's mechanistic anchoring
via a pre-generation doubt-axis projection outlier. Both are cited in the
AMENDMENT's Motivation and posture section. The calibration and RR2
established the family-specific SIGN of a matched-magnitude random-direction
placebo from single seeds (qwen -5.13 suppression, mistral +7.39
recruitment); this experiment builds the object those single points implied
but never measured: the per-family DISTRIBUTION of that placebo response
across K=15 fresh, pre-registered seeds at the identical matched magnitude,
scored under the same wide adjudicated-abstention instrument on a fixed
S=300-row paired subsample per family.

Resolved 2026-07-15. Full run: K=15 accepted seeds per family, S=300 paired
rows per seed, n_missing = 0 for every family and seed, adversarially
red-teamed (full-arc audit including an independent raw-artifact
re-derivation of all 15 mistral deltas) before the Outcome was written. All
three families show sign-consistent placebo structure rather than seed
noise, at different robustness margins
(`matched-magnitude-placebo-sign-survives-as-distributional-property`):
qwen's suppression SURVIVES robustly (14/15 negative, median -6.00, IQR not
spanning zero); mistral's recruitment SURVIVES only at the exact
pre-registered boundary (12/15 positive, median +7.00), which FALSIFIES
both predictors' registered call that mistral's recruitment was seed noise;
llama, carried as a built-in null control with no committed sign, instead
shows a newly discovered negative sign at the identical 12/15 boundary
(median -7.67). Both historical single-seed deltas land at the 53rd
percentile of their family's own census distribution
(`single-seed-placebo-delta-is-a-noisy-draw-from-a-wide-family-distribution`),
confirming they were typical, not lucky, draws even though the census
reveals mistral's true distributional margin to be far thinner than the
single point suggested. Per-seed delta tracks the dosed detector-refusal
count strongly in mistral and llama, and red-team sampling confirms these
dose-induced refusals are genuine, well-formed abstentions rather than a
text-quality or scoring artifact
(`dosed-detector-refusal-channel-drives-genuine-placebo-recruitment`).

All four integrity gates (SC0 provenance/staging, SC1 magnitude-matching,
SC2 grading integrity, SC3 paired population and coverage) passed; SC3
passed only after a post-unblind instrument correction, disclosed in full
in the Outcome, that fixed a report-build bug dropping detector-refused
rows from the paired join (the fix moved two verdicts, both AGAINST the
registered predictions, which the red team adjudicated as the opposite of
motivated-fix contamination). No locked verdict moved: the Phase 1 headline
matrix, the wide-instrument calibration, RR3, and the signflip resolution
are untouched by this census, which adjudicated only its own pre-registered
criterion. Source of truth:
`experiments/placebo-seed-distribution-census/AMENDMENT.md`.
