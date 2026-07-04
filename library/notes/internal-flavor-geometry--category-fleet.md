---
title: 'Category Geometry of Unanswerability: Flavor Encoding, Shared Doubt Trunk, and Per-Flavor Refusal Thresholds (session 0036 fleet + item 22a)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-flavor-geometry
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
fulltext: ../../docs/sessions/0036 - amendment-aj-erasure-category-geometry-fleet.md
provenance: 'Internal exploratory synthesis (Tier-1 lab notebook, not a paper draft). Source of truth: docs/sessions/0036 checkpoint 003 plus analysis/mi_category_geometry_20260704/ (flavor_readout, category_geometry, pliability arms) and analysis/mi_controversial_flips_20260704/ (item 22a resolution). Surface: Amendment AH stage-0 + expansion pregen extractions, raw Qwen3-4B instruct base, 11,996 rows x L0-L36. PRs #192, #193. Ungated exploratory evidence; feeds the Paper 5 steering line.'
related:
- '[[unanswerability-flavor-is-early-content-encoding]]'
- '[[unanswerability-detection-shares-one-axis-across-flavors]]'
- '[[flavor-specific-doubt-residuals-persist]]'
- '[[refusal-threshold-varies-by-unanswerability-flavor]]'
- '[[scalar-readout-compression-mimics-second-mechanism]]'
- '[[answerability-probe-under-flags-ambiguous-questions]]'
- '[[known-unknowns-taxonomy]]'
- '[[known-unknown-questions]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[internal-twosignal-readout--training-free]]'
relationships:
- type: supports
  target: '[[unanswerability-flavor-is-early-content-encoding]]'
  target_id: mechanism:unanswerability-flavor-is-early-content-encoding
  confidence: high
- type: supports
  target: '[[unanswerability-detection-shares-one-axis-across-flavors]]'
  target_id: mechanism:unanswerability-detection-shares-one-axis-across-flavors
  confidence: high
- type: supports
  target: '[[flavor-specific-doubt-residuals-persist]]'
  target_id: mechanism:flavor-specific-doubt-residuals-persist
  confidence: high
- type: supports
  target: '[[refusal-threshold-varies-by-unanswerability-flavor]]'
  target_id: mechanism:refusal-threshold-varies-by-unanswerability-flavor
  confidence: high
- type: supports
  target: '[[scalar-readout-compression-mimics-second-mechanism]]'
  target_id: mechanism:scalar-readout-compression-mimics-second-mechanism
  confidence: medium
- type: supports
  target: '[[answerability-probe-under-flags-ambiguous-questions]]'
  target_id: mechanism:answerability-probe-under-flags-ambiguous-questions
  confidence: high
- type: studies
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: uses
  target: '[[known-unknown-questions]]'
  target_id: dataset:known-unknown-questions
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
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
- type: related_to
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: medium
---

## Summary

Internal exploratory fleet (session 0036, backlog items 22 and 22a) asking whether
the FLAVOR of an unanswerable question, using the six canonical KUQ-derived
categories (ambiguous, controversial, unsolved problem, false assumption, future
unknown, counterfactual), has its own linear structure in the raw Qwen3-4B instruct
base, and whether refusal behavior consults it. Three parallel analyses on a shared
11,996-row x 37-layer activation cache (flavor readout, category geometry,
pliability), plus a follow-up predictor hunt that resolved the one apparent anomaly.
The composite picture: flavor is stamped on the question at entry as content
encoding; unanswerability is judged on one shared axis with per-flavor accents; and
behavior applies per-flavor trigger thresholds to that single judgment.

## Claims

- Evidence label: layer-sweep probe with text baseline (n=5,264 categorized unknowns).
  Flavor is linearly readable at 0.946 macro-OvR-AUROC (L34), already 0.904 at L1 and
  flat after L10; a TF-IDF text baseline reaches 0.921, so flavor is an early encoding
  of question content, not a late-computed judgment (flavor_readout arm).
- Evidence label: cross-flavor transfer matrix (L20/24/28). A known/unknown detector
  trained on one flavor transfers to every other within about one point of its home
  performance (off-diagonal 0.988 vs diagonal 0.998): one shared detection axis
  (category_geometry arm).
- Evidence label: whitened direction geometry. Per-flavor doubt directions align at
  only ~0.71 mean whitened cosine; after projecting out the shared trunk each flavor
  retains 20-42 percent of direction norm whose residual alone separates its unknowns
  at 0.69-0.91 AUROC; counterfactual is the outlier both ways (cos 0.575, residual
  0.91) (category_geometry arm).
- Evidence label: within-arm behavioral regression (n=942 eligible). Baseline refusal
  is one curve in caution boundary distance (AUROC 0.956) with significant per-flavor
  threshold offsets (p=0.004, no slope interaction p=0.35): future unknown refused 93
  percent vs controversial/unsolved ~68 percent, and confabulation rates mirror the
  offsets (31-33 percent vs 7 percent) (pliability arm).
- Evidence label: frozen-probe per-flavor audit. The frozen answerability probe reads
  five flavors at 0.98-0.99 but under-flags ambiguous questions (0.92, median unknown
  score 0.19, i.e. they read as answerable) (category_geometry arm).
- Evidence label: predictor hunt with permutation nulls (n=168, 42 flips). The
  controversial-flavor flip anomaly (caution scalar predicts prime uptake at 0.34
  signed vs 0.08-0.17 elsewhere) is a compression artifact of the 1-D caution scalar,
  not a second mechanism: a direct L20 activation probe predicts the flips at 0.753
  (perm p=0.024) but re-reads the same shared doubt geometry (it also predicts
  baseline refusal at 0.711, and cross-flavor residual projections do as well); the
  frozen knowledge probe is a null (p>=0.17) and flips are partly text-predictable
  (TF-IDF 0.70) (item 22a).

## Relevance to experiment

Gives the Paper 5 steering line differentiated targets (counterfactual residual
direction, ambiguous under-flag) instead of one monolithic axis, and strengthens the
two-signal readout story: the validated gate is genuinely one gate across flavors.
Also a methods lesson: where a 1-D scalar readout disagrees with behavior, check
whether the full geometry closes the gap before positing a new mechanism.
