---
aliases:
- placebo sign is a distributional property, not a single-seed artifact
- family placebo sign census (qwen survives, mistral survives at boundary, llama newly discovered)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  type: mechanism
  status: canonical
cause: "A matched-magnitude random_direction placebo write, held to each family's certified single-seed erase-write setpoint (qwen dose_abs 12.608 at hs20, mistral dose_abs 3.665 at hs16, llama 12 x sigma_c(hs20) re-derived byte-identical from RR's committed fit manifest), is applied across K=15 fresh, pre-registered seeds per family on a fixed S=300-row paired confab subsample, and scored by the same blinded wide adjudicated-abstention instrument each family's single-seed placebo reading used."
effect: "The family-signed placebo reading is a genuine distributional property in all three families, not seed noise, though at different robustness margins. Qwen's suppression SURVIVES robustly: 14/15 = 0.933 seeds negative (bootstrap 95% CI [0.80, 1.00]), median signed delta -6.00 points, IQR [-6.83, -3.67] not spanning zero. Mistral's recruitment SURVIVES only at the exact pre-registered boundary: 12/15 = 0.800 seeds positive (bootstrap 95% CI [0.60, 1.00]), median +7.00 points, IQR [+1.17, +13.67], which falsifies both predictors' registered call that mistral's single-seed recruitment was seed noise. Llama, which had no committed historical sign (a null +0.1 point single-seed reading), instead shows a newly discovered negative sign: 12/15 = 0.800 seeds negative, median -7.67 points, IQR [-9.33, -2.00]. Matched-magnitude random directions are therefore not behaviorally inert in any of the three families measured; suppression is dominant in qwen and llama, recruitment is dominant in mistral."
polarity: mediates
related:
- '[[placebo-seed-distribution-census]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[placebo-seed-distribution-census]]'
  target_id: experiment:placebo-seed-distribution-census
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md#outcome (Per-family verdicts against the pre-stated criterion)
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
- type: related_to
  target: '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
  target_id: mechanism:random-direction-placebo-recruits-additional-wide-instrument-abstention
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Extends `random-direction-placebo-response-is-family-specific-in-sign`, which
established the family-signed placebo map from single seeds (qwen -5.13
suppression, mistral +7.39 recruitment), by measuring whether each family's
sign holds across a 15-seed census at the same matched magnitude rather than
a single draw. It does, in every family, but the margins differ sharply:
qwen's suppression clears its pre-stated criterion with room to spare, while
mistral's recruitment clears the identical criterion at the exact boundary
(12/15, the smallest fraction the pre-registered criterion accepts), a
result the experiment reports with an explicit robustness caution rather
than as a clean confirmation. Llama, carried into the census as a built-in
null control with no committed sign to defend, instead surfaces a newly
discovered negative sign at the same 12/15 boundary as mistral. The
cross-family reading is that matched-magnitude random-direction writes are
never behaviorally inert; whether a given family's sign is treated as
robust or marginal now has a measured distribution behind it instead of one
historical point.
