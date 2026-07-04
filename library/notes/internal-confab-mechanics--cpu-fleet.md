---
title: 'Confabulation Mechanics: Commitment Signal, Specificity Leak, and a Re-derived Veto (session 0037 CPU fleet)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-confab-mechanics
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
fulltext: ../../docs/sessions/0037 - hallucination-mechanics-confab-fleet.md
provenance: 'Internal exploratory synthesis (Tier-1 lab notebook, not a paper draft). Source of truth: docs/sessions/0037 plus analysis/mi_confab_phenotypes_20260704/ (arm A), analysis/mi_confab_signature_20260704/ (arm B), analysis/mi_veto_transport_20260704/ (item 31). Surfaces: Amendment AH stage-0 pregen extractions (arms A/B, raw Qwen3-4B instruct base) and the cached Amendment S/T/U/W pre/post extraction tensors (item 31, raw base + clean-SFT-to-GRPO-v2). PR #196. Ungated exploratory evidence; feeds TODO item 32 (commitment-point extraction) and the Paper 5 steering line.'
related:
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[internal-doubt-degrades-fabrication-specificity]]'
- '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
- '[[post-generation-veto-is-rederived-not-carried]]'
- '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[known-unknown-direction]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[internal-flavor-geometry--category-fleet]]'
- '[[internal-twosignal-readout--training-free]]'
relationships:
- type: supports
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: supports
  target: '[[internal-doubt-degrades-fabrication-specificity]]'
  target_id: mechanism:internal-doubt-degrades-fabrication-specificity
  confidence: high
- type: supports
  target: '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
  target_id: mechanism:question-familiarity-draws-confabulation-at-matched-doubt
  confidence: high
- type: supports
  target: '[[post-generation-veto-is-rederived-not-carried]]'
  target_id: mechanism:post-generation-veto-is-rederived-not-carried
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
  target_id: mechanism:entity-recognition-direction-gates-refusal-vs-hallucination
  confidence: high
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
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
  target: '[[internal-flavor-geometry--category-fleet]]'
  target_id: paper:internal-flavor-geometry
  confidence: high
- type: related_to
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: medium
---

## Summary

Internal exploratory fleet (session 0037, TODO items 30 and 31) asking what happens
mechanically between the model knowing a question is unanswerable before generating
(gate 0.997) and marking its own confabulation lowest-trust afterward (veto 0.980).
Three CPU arms on cached activation surfaces, no GPU. The composite picture is a
graded three-stage failure: before generation the state already leans
fabricate-vs-refuse beyond its doubt level (commitment signal); the doubt that
failed to trigger refusal still degrades the fabrication it could not prevent
(specificity leak); after emission the veto re-derives trust from the answer itself,
on an axis orthogonal to doubt, rather than carrying the pre-generation reading
through (re-derived veto).

## Claims

- Evidence label: caliper-matched probe with permutation null (n=328 matched, arm B).
  At matched caution distance and matched flavor, pre-generation activations predict
  confab-vs-refuse at AUROC 0.834 plus-minus 0.014 (perm p=0.0099), beating TF-IDF by
  +0.215 and familiarity proxies by +0.152 on 10 of 10 paired folds; the direction is
  0.32 whitened-cosine from the doubt trunk and peaks at L24-28.
- Evidence label: within-flavor rank correlation with permutation null (n=309
  confabs, arm A). Pre-generation doubt-trunk projection negatively predicts
  fabrication specificity (rho -0.21 to -0.24, p=0.001) and length (rho -0.27);
  hedging is question-driven (probe 0.674 fails its TF-IDF guard 0.642).
- Evidence label: behavioral prime contrast (arm A). A doubt prime produced 0
  confabulations in 324 generations; a certainty prime raised the confab count (459
  vs 309) and length but not per-confab texture.
- Evidence label: familiarity proxies on matched pairs (arm B). Joint familiarity
  features predict confab-vs-refuse at 0.682 (p=0.0099) at matched doubt, supporting
  the entity-recognition account; the frozen knowledge probe is largely null.
- Evidence label: cross-position probe transfer on cached S/T/U/W tensors (item 31).
  The correctness/veto axis fails position transfer (0.58-0.64 vs 0.81-0.86
  in-position) while answerability transports at 0.96-0.99; post-read advantage
  (+0.022 raw base, +0.094 GRPO-v2) survives residualizing all carried readouts; the
  veto axis is orthogonal to doubt (whitened cosine -0.02); GRPO-v2 is MORE
  re-derived than the raw base.

## Relevance to experiment

Turns the commitment-point experiment (TODO item 32) from a sketch into a design:
read the veto across answer-token positions to find where it crystallizes, steer the
L24-28 commitment direction (orthogonalized to caution) in the answer-token window,
and expect anchor-only interventions to move only the carried minority. Also links
the program's surfaces to the entity-recognition literature via the familiarity
result. Caveats: single surface per claim, single seed, readout-not-causal
throughout; regex phenotypes in arm A; the W surface's transported 0.905 is an upper
bound because its labels coincide.
