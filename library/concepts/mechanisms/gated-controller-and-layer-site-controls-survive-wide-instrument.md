---
aliases:
- narrow-detector control conclusions are not instrument artifacts (Qwen3-4B, Sections 4.5-4.6)
- wide-instrument re-score confirms the gated-controller and layer-contrast controls
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gated-controller-and-layer-site-controls-survive-wide-instrument
  type: mechanism
  status: canonical
cause: "`wide-instrument-control-rescore` regenerates the doubt-gated-caution-tighten (Section 4.5, gated / random_direction / permuted_gate arms on the 185 confabulation-prone / 258 known-correct held-out pool) and j-space-calibrated-layer-contrast-qwen3-4b (Section 4.6, hs23 and hs34 gated arms plus controls on the 443-row held-out pool) arms byte-for-byte from their committed pipelines and pinned direction artifacts (WG-G0 parity: every regenerated arm matches its committed narrow-detector rate to 0.0pp, 13/13 rate pairs byte-exact), then re-scores the regenerated rows under the certified wide two-instrument stack (detector_v2 plus blinded context-free LLM grading, pinned byte-identical from abstention-wide-instrument-calibration) instead of the narrow canonical phrase detector, with no instrument component refit or retuned."
effect: "Both narrow-detector control conclusions survive at both operating points. Section 4.5 random-direction specificity (WG-G1): the wide-instrument gated confab-tightening lift (+62.7pp, 74.05% vs 11.35% undosed) is 14.5x the random-direction lift (-4.3pp, suppressive, matching the qwen census expectation), against a >=3.0 pass threshold. Section 4.5 permuted-gate contribution (WG-G2): the paired known-correct cost excess (permuted gate minus true gate) is +20.6pp, bootstrap 95% CI [+14.8, +26.3], n=209, CI excluding zero. Section 4.6 layer-site conclusion (WG-G3): the paired hs23-vs-hs34 clean-tightening advantage is +22.70pp, equal to the narrow-detector anchor, bootstrap 95% CI [+16.2, +29.7], n=185, CI excluding zero. Across all 2,677 core rows scored, only 5 gained adjudicated abstention beyond detector_v2, so at these operating points the choice of scoring instrument is decoupled from the control conclusions: neither the Section 4.5 nor the Section 4.6 result is a narrow-detector artifact, closing the paper 5 Section 6.4 instrument-validity gap."
polarity: decouples
related:
- '[[wide-instrument-control-rescore]]'
- '[[doubt-gated-caution-tighten]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[detector-v2-undercounts-baseline-abstention-by-family-varying-margins]]'
relationships:
- type: supported_by
  target: '[[wide-instrument-control-rescore]]'
  target_id: experiment:wide-instrument-control-rescore
  confidence: high
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md#outcome
- type: related_to
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
- type: related_to
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: high
- type: related_to
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md#outcome (WG-G1
    random-direction lift -4.3pp, suppressive, reproducing this mechanism's
    qwen finding at a different operating point)
- type: related_to
  target: '[[detector-v2-undercounts-baseline-abstention-by-family-varying-margins]]'
  target_id: mechanism:detector-v2-undercounts-baseline-abstention-by-family-varying-margins
  confidence: medium
  evidence:
  - experiments/wide-instrument-control-rescore/AMENDMENT.md#outcome (only 5
    of 2,677 core rows gained abstention beyond detector_v2, a small margin
    consistent with qwen's family-specific undercount reading)
---

The paper 5 Appendix D limitation this mechanism resolves: two narrow-detector
control results (the Section 4.5 gated-controller specificity and cost
selectivity, and the Section 4.6 layer-site contrast) had only ever been
measured under the narrow canonical phrase detector, never under the wide
two-instrument stack that every Section 4.8 headline number rests on. A
detector change could, in principle, have reversed either conclusion.

`wide-instrument-control-rescore` closes the gap by regeneration-plus-rescore
rather than assumption: it reproduces the source cells' arms exactly (parity
gate byte-exact) before re-scoring them under the wide instrument, so any
divergence would be attributable to the instrument change alone. All three
gates pass with wide margins (effect ratio 14.5 against a 3.0 floor; both
paired-bootstrap CIs well clear of zero), and the instrument-change magnitude
finding (5/2,677 core rows) shows the wide instrument moves qwen raw-base
rates only marginally at these operating points. The random-direction
suppression finding (WG-G1) also reproduces
`random-direction-placebo-response-is-family-specific-in-sign`'s qwen
suppression at a different operating point, strengthening that mechanism's
generality. Source of truth:
`experiments/wide-instrument-control-rescore/AMENDMENT.md#outcome`.
