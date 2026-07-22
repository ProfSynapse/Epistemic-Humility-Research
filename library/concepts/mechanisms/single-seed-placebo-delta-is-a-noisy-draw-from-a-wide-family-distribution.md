---
aliases:
- single-seed placebo deltas sit mid-distribution, not at an extreme
- historical placebo points are noisy draws from a wide census spread
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:single-seed-placebo-delta-is-a-noisy-draw-from-a-wide-family-distribution
  type: mechanism
  status: canonical
cause: "Each family's historical single-seed matched-magnitude placebo delta (qwen -5.13, mistral +7.39, both measured before the census on different single seeds) is located by percentile rank within that family's own 15-seed census distribution of signed matched-magnitude deltas, measured independently on the fixed S=300-row census subsample."
effect: "Both historical single-seed deltas land squarely inside the middle of their family's census spread rather than at an extreme: qwen's -5.13 point suppression is at the 53rd percentile of its census distribution (median -6.00), and mistral's +7.39 point recruitment is at the 53rd percentile of its census distribution (median +7.00, IQR [+1.17, +13.67], full span [-8.00, +20.33]). RR3's three earlier fresh mistral seeds, measured on a different full-pool denominator and grading lane and not counted toward the census K, sit far more widely across the census distribution (roughly the 3rd, 67th-100th, and 100th percentiles), consistent with a wide recruitment-dominant spread rather than a tight point estimate. A single-seed placebo reading is a legitimate but individually noisy draw that can land anywhere across a span of 15-30+ points even when its sign matches the family's dominant distributional sign, so a successor citing a single-seed placebo delta should report it against the measured family census distribution rather than transcribe it as a point constant."
polarity: mediates
related:
- '[[placebo-seed-distribution-census]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[placebo-seed-distribution-census]]'
  target_id: experiment:placebo-seed-distribution-census
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md#outcome (Historical single-seed percentiles)
- type: related_to
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  confidence: high
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Both predictors registered ranges for where each historical single-seed
delta would fall within the eventual census distribution (qwen 40th-60th
percentile, mistral 50th-70th percentile) and both calls landed correct: the
53rd percentile for both families. That accuracy is itself informative, not
just a scoreboard footnote: it shows the historical single-seed points were
not lucky or unlucky outliers relative to their family's true distribution,
even though the census as a whole (`matched-magnitude-placebo-sign-survives-
as-distributional-property`) revealed mistral's sign to be far more marginal
than the single point suggested. The two findings are compatible because a
draw can sit near the median of a wide, boundary-crossing distribution: the
53rd-percentile reading says the historical seed was typical, while the
12/15 boundary result says "typical" for mistral is still barely inside the
survive criterion. RR3's three additional mistral seeds, plotted against
this same distribution on a different denominator, span nearly its full
range (3rd to 100th percentile), underscoring how wide a draw from this
family's true distribution can be.
