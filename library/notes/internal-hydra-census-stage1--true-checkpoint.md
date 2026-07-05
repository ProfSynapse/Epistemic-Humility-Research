---
title: 'Hydra Stage 1 Census: The Caution Readout Is Low-Rank on Collinear Carriers (session 0038, AI-TRUE A0 pre-generation)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-hydra-census-stage1
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
provenance: 'Internal exploratory census (Tier-1 lab notebook, not a paper draft). Source of truth: experiment/phase1/probe/analysis/hydra_census_stage1/{hydra_census_report.json,NOTES.md} in the canonical checkout, plus the census script docstring committed as db8a2b04 (script experiment/phase1/probe/hydra_census_stage1.py). Surface: AI-TRUE A0 pre-generation states (1,662 rows; 90 correct / 120 wrong / 114 answerable-refused / 1,222 unanswerable-refused / 116 confab), seed 20260705, label-agnostic randomized PCA-128 then LogisticRegression saga. CPU only, single seed. Ungated exploratory evidence.'
related:
- '[[caution-readout-is-low-rank-on-collinear-carriers]]'
- '[[refusal-hydra-effect]]'
- '[[representational-independence]]'
- '[[flavor-specific-doubt-residuals-persist]]'
- '[[safety-finetuning-low-rank-activation-changes]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[internal-doubt-degrades-fabrication-specificity]]'
- '[[known-unknown-direction]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[confabulation-propensity-direction]]'
- '[[compound-caution-theory]]'
relationships:
- type: proposes
  target: '[[caution-readout-is-low-rank-on-collinear-carriers]]'
  target_id: mechanism:caution-readout-is-low-rank-on-collinear-carriers
  confidence: high
- type: supports
  target: '[[caution-readout-is-low-rank-on-collinear-carriers]]'
  target_id: mechanism:caution-readout-is-low-rank-on-collinear-carriers
  confidence: high
- type: studies
  target: '[[refusal-hydra-effect]]'
  target_id: term:refusal-hydra-effect
  confidence: high
- type: related_to
  target: '[[representational-independence]]'
  target_id: term:representational-independence
  confidence: high
- type: related_to
  target: '[[flavor-specific-doubt-residuals-persist]]'
  target_id: mechanism:flavor-specific-doubt-residuals-persist
  confidence: high
- type: related_to
  target: '[[safety-finetuning-low-rank-activation-changes]]'
  target_id: mechanism:safety-finetuning-low-rank-activation-changes
  confidence: medium
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[internal-doubt-degrades-fabrication-specificity]]'
  target_id: mechanism:internal-doubt-degrades-fabrication-specificity
  confidence: medium
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
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
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: related_to
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: related_to
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: related_to
  target: '[[compound-caution-theory]]'
  target_id: term:compound-caution-theory
  confidence: medium
---

## Summary

Session-0038 Stage 1 census on the Amendment AI TRUE checkpoint's A0 surface
(1,662 pre-generation states, full-stack extracts) asked whether the caution
signal is a many-headed compound of independent discriminative axes or a single
low-rank readout. Recomputing direction-removal robustness in a label-agnostic
randomized PCA-128 basis, rather than in the raw 2,560-dimensional activation
space, resolves the question. Both signals are cliffs, not plateaus:
permutation-controlled deflation curves at every layer L8 to L36 show caution
(refused versus answered) collapses from AUROC about 0.92 to 0.96 down to the
permuted floor after removing one to two directions, and propensity (confab
versus unref) floors at two to three. An ICA head hunt on the
caution-residualised space yields zero reproducing candidate heads. The
reconciliation with the session-0035 MI result (caution survives about 40 raw
direction removals) is that the two are the same signal in two bases: the raw
removals peeled about 40 nearly collinear carriers, each holding a sliver of one
low-rank readout. The apparent hydra was collinearity, not many independent
heads. Doubt remains a correlate, not a separable removable element.

## Claims

- Evidence label: permutation-controlled deflation, caution (refused versus
  answered). Full AUROC ranges about 0.92 to 0.96 across L8 to L36; a single
  discriminative direction removal drops it to about 0.57 to 0.61, and it hits
  the permuted floor after two removals (occasionally three at early layers).
  Caution is a rank-one-to-two discriminative readout in PCA-128 space
  (hydra_census_report.json, deflation block).
- Evidence label: permutation-controlled deflation, propensity (confab versus
  unref). Full AUROC about 0.81 to 0.95; floors at one to five removals, mostly
  two to three. Slightly deeper than caution but still low-rank
  (hydra_census_report.json, deflation block).
- Evidence label: ICA candidate-head panel (n=16 and n=32) on the
  caution-residualised PCA-128 space at L24. Zero candidate heads: no component
  discriminates any split above about 0.11 distance from chance (the bar was
  0.15, that is AUROC 0.65), and zero of 48 components reproduce across random
  halves at cosine above 0.6. Methodological caveat: ICA maximises independence,
  not discrimination, so class signal spreads across components and this panel
  structurally under-detects; the deflation curves are the primary instrument and
  ICA is corroborating only (hydra_census_report.json, ica_panel and
  ica_stability blocks).
- Evidence label: reconciliation with session-0035 MI. The prior finding that
  caution survives about 40 raw-space direction removals and this census's rank
  one-to-two collapse are two views of one fact. The raw 2,560-dimensional
  removals peeled about 40 near-degenerate, highly collinear carrier directions,
  each carrying a thin sliver of the readout, so the signal appeared to survive
  many removals. The label-agnostic PCA-128 concentrates those carriers into a
  handful of components, where the signal is a sharp permutation-controlled cliff
  (NOTES.md reconciliation section).

## Relevance to experiment

Settles the many-heads question for the Amendment AL surface: caution and
propensity are each carried by one to three discriminative directions, not by a
population of independent heads, so a steering or ablation control law does not
need to enumerate many separate axes to reach the signal. It also reframes the
session-0035 hydra reading as a collinearity artifact of the raw basis rather
than evidence for genuine redundancy, and it confirms that doubt reads as a
correlate of the low-rank caution readout, not as a separable element that can be
removed on its own. Verdict is NULL: no new hydra head, nothing
caution-orthogonal, stable, and population-predictive was found, so this does not
warrant a signed follow-up on current evidence. Caveats: one checkpoint, one
seed, CPU only, readout not causal, and the ICA panel under-detects by
construction.
