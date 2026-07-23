---
aliases:
- dose-induced detector refusals under placebo writes are genuine abstentions
- detector-refusal count tracks per-seed placebo recruitment
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dosed-detector-refusal-channel-drives-genuine-placebo-recruitment
  type: mechanism
  status: canonical
cause: "Within the 15-seed matched-magnitude random-direction census, each accepted seed's automatic detector-v2 refusal screen fires on a variable count of the fixed S=300 confab rows; that per-seed dosed detector-refusal count is compared against the seed's paired wide-instrument abstention delta, and outlier-positive seeds in mistral and llama are red-team sampled and read in full against each flagged row's baseline committed-answer status."
effect: "The dosed detector-refusal count is the dominant per-seed driver of the placebo delta in mistral and llama: llama's two most positive outlier seeds (+19.33 and +6.33 points) are exactly its two seeds with the highest dosed detector-refusal counts (97/300 and 50/300), and the same tracking holds in mistral. Red-team sampling of the flagged rows confirms these dose-induced detector-refusals are coherent, well-formed abstentions on rows that carried a committed answer at baseline, not dose-degraded or garbled text, with zero degenerate-and-refused overlap across all 51 census runlogs. The detector-refusal channel behind mistral and llama's positive-sign seeds is therefore a genuine behavioral recruitment effect, not a scoring artifact or a text-quality confound."
polarity: increases
related:
- '[[placebo-seed-distribution-census]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[placebo-seed-distribution-census]]'
  target_id: experiment:placebo-seed-distribution-census
  confidence: high
  evidence:
  - experiments/placebo-seed-distribution-census/AMENDMENT.md#outcome (Cross-family observation)
- type: related_to
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
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

Direct mechanistic correlate of `matched-magnitude-placebo-sign-survives-as-
distributional-property`: it identifies WHICH scored channel carries the
per-seed variance the census distribution measures. The finding rules out
the most obvious threat to trusting a wide, idiom-inclusive instrument
across 45 dosed generations per family: that a matched-magnitude random
write might occasionally degrade generation quality badly enough that the
detector or the blinded adjudicator credits garbled text as abstention. The
red team's row-level check instead finds the opposite, that the outlier
seeds carry the cleanest, most legible refusals in the family's runlog set,
supporting the reading that a random write can genuinely, mechanistically
recruit refusal behavior at some seeds and not others, consistent with this
being a real dose-response-adjacent phenomenon rather than a measurement
artifact.
