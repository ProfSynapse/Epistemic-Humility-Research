---
title: wide-instrument-control-rescore
aliases:
- Wide-instrument re-score of the gated-controller and layer-contrast controls (Qwen3-4B)
- WG-G1/WG-G2/WG-G3 instrument-gap closure
tags:
- kg/experiment
- experiment
- doubt-snap
- j-space
kg:
  id: experiment:wide-instrument-control-rescore
  type: experiment
  status: canonical
related:
- '[[doubt-gated-caution-tighten]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[gated-controller-and-layer-site-controls-survive-wide-instrument]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
relationships:
- type: builds_on
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md (Motivation and posture;
    Design Stage 0 regenerates the 4.5 cell's gated/random_direction/permuted_gate
    arms from its committed pipeline and direction artifacts)
- type: builds_on
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: high
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md (Design Stage 0
    regenerates the 4.6 cell's hs23/hs34 gated arms and controls from its
    committed pipeline)
- type: builds_on
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md (Design Stage 1;
    the wide two-instrument stack, detector_v2 plus blinded context-free
    grading, is pinned byte-identical from this cell, no component refit or
    retuned)
- type: supports
  target: '[[gated-controller-and-layer-site-controls-survive-wide-instrument]]'
  target_id: mechanism:gated-controller-and-layer-site-controls-survive-wide-instrument
  confidence: high
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md#outcome
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: medium
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md#outcome (WG-G1
    random-direction lift -4.3pp, suppressive, matching the census
    expectation this mechanism already establishes for qwen)
---

Exploratory control-validation cell on raw-base Qwen3-4B, registered against a
gap paper 5 Appendix D states explicitly: the random-direction and
permuted-gate controls behind the Section 4.5 gated-controller headline
(`doubt-gated-caution-tighten`) and the Section 4.6 layer-site contrast
(`j-space-calibrated-layer-contrast-qwen3-4b`) had only ever been scored under
the narrow canonical phrase detector, never under the wide two-instrument
stack (frozen widened pattern detector plus blinded context-free LLM grading)
that every Section 4.8 number rests on. The cell regenerates both source
cells' arms byte-for-byte from their committed pipelines and pinned direction
artifacts (a parity precondition, WG-G0, since the original row-level
generations were not retained on disk), then re-scores the regenerated rows
under the wide instrument with no component refit.

Resolved 2026-08-20. Verdict: prediction CONFIRMED, all gates pass, and both
narrow-detector control conclusions survive at both operating points. WG-G0
(parity): every regenerated arm matched its committed narrow-detector rate to
0.0pp (13/13 rate pairs byte-exact). CG1 (grading-lane calibration): PASS on
all four shards, clear-positive and clear-negative decoy agreement 1.0/1.0.
WG-G1 (random-direction specificity, Section 4.5): wide gated confab
tightening 74.05% (137/185) vs undosed baseline 11.35% (lift +62.7pp) against
the random-direction lift of -4.3pp (suppressive), effect ratio 14.5 against
the >=3.0 threshold. WG-G2 (permuted-gate contribution, Section 4.5): paired
known-correct cost excess (permuted minus gated) +20.6pp, bootstrap 95% CI
[+14.8, +26.3], n=209. WG-G3 (layer-site conclusion, Section 4.6): paired
hs23-vs-hs34 clean-tightening advantage +22.70pp, equal to the narrow-detector
anchor, bootstrap 95% CI [+16.2, +29.7], n=185.

Instrument-change magnitude: across all 2,677 core rows scored, exactly 5
gained adjudicated abstention beyond detector_v2. At these operating points
the wide instrument barely moves qwen raw-base rates, consistent with
`abstention-wide-instrument-calibration`'s family-specificity reading. The
result closes the paper 5 Section 6.4 instrument-validity gap for both
controls: neither the Section 4.5 nor the Section 4.6 control conclusion is a
narrow-detector artifact. Source of truth:
`experiments/wide-instrument-control-rescore/AMENDMENT.md`.
