---
title: qwen3-4b-l34-placebo-seed-census
aliases:
- Raw-base Qwen3-4B L34 random-direction seed census
- qwen hs34 late-site direction-specificity distributional census
tags:
- kg/experiment
- experiment
- j-space
- doubt-snap
kg:
  id: experiment:qwen3-4b-l34-placebo-seed-census
  type: experiment
  status: canonical
related:
- '[[wide-instrument-control-rescore]]'
- '[[placebo-seed-distribution-census]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[qwen-l34-random-direction-specificity-survives-seed-census]]'
- '[[qwen-l34-random-direction-sign-is-a-draw-level-accident]]'
relationships:
- type: builds_on
  target: '[[wide-instrument-control-rescore]]'
  target_id: experiment:wide-instrument-control-rescore
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md (Design; reuses
    the frozen gated arm 137/185 and undosed baseline 21/185 byte-identically
    from the wicr committed report, same hs34 site, dose 200.0, 185-row
    confab pool, and wide two-instrument stack; generates only the fifteen
    random arms)
- type: related_to
  target: '[[placebo-seed-distribution-census]]'
  target_id: experiment:placebo-seed-distribution-census
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md (Motivation and
    posture; adopts the program's fifteen-fresh-seed-per-operating-point
    standard this experiment established, applied here to the late-site
    operating point)
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: medium
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md#outcome
    (Outcome, QG-G2; the historical single hs34 draw's suppressive sign had
    been read as corroborating this mechanism's qwen reading; the census
    tests that reading distributionally at this specific operating point)
- type: supports
  target: '[[qwen-l34-random-direction-specificity-survives-seed-census]]'
  target_id: mechanism:qwen-l34-random-direction-specificity-survives-seed-census
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md#outcome (QG-G1)
- type: supports
  target: '[[qwen-l34-random-direction-sign-is-a-draw-level-accident]]'
  target_id: mechanism:qwen-l34-random-direction-sign-is-a-draw-level-accident
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md#outcome (QG-G2)
---

Exploratory cell on raw-base `Qwen3-4B`, closing a gap `wide-instrument-
control-rescore` (WG-G1) flagged in its own report: the late-site (hs34,
layer index 33) direction-specificity result rested on a single historical
random-direction draw (seed 20260707, effect ratio 14.5), not the program's
fifteen-fresh-seed standard. This cell reuses that experiment's frozen gated
arm (137/185) and undosed baseline (21/185) byte-identically and generates
fifteen fresh matched-dose random unit directions (seeds 920001-920015) at
the same site, dose (200.0), 185-row confab population, and wide
two-instrument stack, with no component refit.

Resolved 2026-08-26, MIXED, reported straight. QG-G1 (distributional
specificity): effect ratio = frozen gated lift 0.6270 / max_k abs(random
lift_k) = 0.6270 / 0.1297 (seed 920006) = 4.83 against the 3.0 floor, PASS;
the late-site specificity claim survives a fifteen-draw matched-dose
distribution, not just the single historical draw, upgrading it from a
single-draw form (ratio 14.5) to a distributional form (ratio 4.83). QG-G2
(sign-consistency): only 6/15 seeds land negative (9 positive) against the
12/15 floor, FAIL; per-seed signed lifts over the frozen 0.1135 baseline
range -7.0pp to +13.0pp, median +0.5pp, straddling zero. The historical
draw's -4.3pp suppression is a draw-level accident, not a family-signed
suppressive placebo response at this operating point, and the sign-
opposition phrasing in the manuscript is retired at this site (see
[[qwen-l34-random-direction-sign-is-a-draw-level-accident]]). No cost gate
was registered; the random arms ran on confab rows only. Source of truth:
`experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md`.
