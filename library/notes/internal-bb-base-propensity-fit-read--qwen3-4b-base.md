---
title: 'Base-Model Confab-Propensity Direction Certified at Held-Out AUROC 0.82 With Zero Training (Amendment BB)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-bb-base-propensity-fit-read
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: lab-notebook
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- qwen3-4b
metrics:
- auroc
fulltext: ../../experiments/bb-base-propensity-fit-read/AMENDMENT.md
provenance: 'Internal amendment (Tier-2 probe-fit, signed 2026-07-11, resolved 2026-07-11). Source of truth: experiments/bb-base-propensity-fit-read/AMENDMENT.md section 12 (outcome). Checkpoint: untrained base Qwen/Qwen3-4B @ 1cfa9a72, 4-bit, no adapter, pulled from the hub. Fit surface: AL''s 1,662-row A0 surface, regenerated on base grades. Read surface: the vendored, byte-identical copy of Amendment H9''s 750-row enlarged held-out draw (experiments/h9-propensity-reading-gate/AMENDMENT.md), so BB and H9 score the same rows on the same staged text, differing only in the model under test.'
related:
- '[[confabulation-propensity-direction]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[base-confab-propensity-direction-reads-held-out-without-training]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[internal-al-injection-null--true-checkpoint]]'
- '[[internal-h9-reading-gate-inconclusive-by-power--true-checkpoint]]'
relationships:
- type: supports
  target: '[[base-confab-propensity-direction-reads-held-out-without-training]]'
  target_id: mechanism:base-confab-propensity-direction-reads-held-out-without-training
  confidence: high
- type: studies
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: medium
- type: related_to
  target: '[[internal-al-injection-null--true-checkpoint]]'
  target_id: paper:internal-al-injection-null
  confidence: high
- type: related_to
  target: '[[internal-h9-reading-gate-inconclusive-by-power--true-checkpoint]]'
  target_id: paper:internal-h9-reading-gate-inconclusive-by-power
  confidence: high
---

## Summary

Amendment BB is phase 1 of the program's base-model loop: epistemic humility
without training, where the trained checkpoints are the contrast condition. It
fits AL's exact confab-propensity recipe fresh on untrained base Qwen/Qwen3-4B
(not the AI-TRUE-fit direction, which AL's own provenance shows transfers across
checkpoints at only cosine 0.17) and asks whether the base model's own direction
reads out on held-out rows. Phase 0 first measured feasibility on the
already-staged 750-row read pool BB shares with
[[internal-h9-reading-gate-inconclusive-by-power--true-checkpoint]]: all three
pre-registered floors passed (schema-follow, positive-cell, negative-cell), with
the base model turning out to be heavily abstention-biased rather than the
refusal-starved risk the design flagged. Phase 1 then fit the base direction on
a base-regenerated 1,662-row surface and read it on the held-out draw: **result
RESOLVED, BB-P1-G1 PASS**, held-out propensity AUROC 0.8179 (95% bootstrap CI
[0.7190, 0.9042], 1,000 resamples, read once), the program's first certified
held-out propensity reading anywhere, achieved with zero training. This is the
before-training bookend to H9, which asked the identical held-out reading
question on the trained AI-TRUE checkpoint and could not adjudicate it because
the positive cell (confabulation) starved there; BB shows the untrained
substrate carries ample mass in both cells and a direction fit on it generalizes
cleanly.

## Claims

- Evidence label: pre-registered phase-0 feasibility floors (BB-P0-A/B/C, all
  PASS, over the 750-row base-generated read pool). Schema-follow 0.976 >= 0.60;
  positive-cell (confabs) 32 >= 20; negative-cell (honest unanswerable refusals)
  558 >= 20. Both registered predictors called all-pass; the orchestrator's
  named most-likely failure (the negative-cell floor) was wrong in direction:
  base is heavily abstention-biased, 92.2% honest refusal on unanswerables and
  64.8% over-refusal on knowns. (`experiments/bb-base-propensity-fit-read/AMENDMENT.md`
  section 12.)
- Evidence label: pre-registered fit-surface evaluability precondition
  (BB-P1-G0). MET: 205 confabulations and 1,020 unanswerable-refused rows on the
  guarded 1,662-row base fit surface (floors 20/20 each), so the power failure
  that made H9 inconclusive on the trained checkpoint does not exist on base.
- Evidence label: pre-registered held-out reading gate (BB-P1-G1, PASS lines
  AUROC >=0.62 and CI lower bound >0.55). PASS, decisively: held-out propensity
  AUROC 0.8179, 95% bootstrap CI [0.7190, 0.9042] (1,000 resamples, read once on
  the vendored 750-row surface).
- Evidence label: pre-registered caution positive control (BB-P1-G2, floor
  >=0.80). PASS: AUROC 0.9820 on the gradeable-only primary population (n=732),
  0.9813 on the all-750 non-gating sensitivity line.
- Evidence label: fidelity gates (pre-registered). BB-FID-1 (determinism) PASS,
  cosine >=1-1e-6. BB-FID-2 (recipe parity under the pre-launch repin: fit-math
  functions verbatim-identical to H9's pinned scorer plus an AL section-3.2 knob
  assertion) PASS.
- Evidence label: registered near-duplicate sensitivity sweep (same KUQ
  populations as H9). 0 rows flagged, max token overlap 0.75 vs the 0.90
  threshold; the AUROC excluding flagged rows equals the headline read.
- Evidence label: honest priors (non-gating, recorded per gates.yaml). Base
  in-cell OOF propensity AUROC 0.7745; base in-cell OOF caution AUROC 0.9738;
  the held-out caution value (0.9820) sits within the pre-registered ~0.10 band
  of that measured prior.
- Evidence label: derived cross-experiment comparison (arithmetic on the two
  governed docs' own counts over the identical 750-row read pool, not a
  registered gate). Base confabulates on 32 of the 605 unanswerable rows
  (5.29%) against AI-TRUE's 4 of the same 605 rows (0.66%)
  (`experiments/bb-base-propensity-fit-read/AMENDMENT.md` section 12;
  `experiments/h9-propensity-reading-gate/AMENDMENT.md` section 10), a ratio of
  about 8x. Reported as a descriptive before/after-training contrast; the
  amendments do not register a causal mechanism connecting training to this
  rate change, so none is claimed here.
- Caveats: single model, single seed. A phase-1 pass certifies a
  within-checkpoint base reading claim, not portability or a multi-seed
  headline (same caveat AL and H9 carry). Exploratory lab-notebook evidence,
  never pooled with the locked headline matrix.
