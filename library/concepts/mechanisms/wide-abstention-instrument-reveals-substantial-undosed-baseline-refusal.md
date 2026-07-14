---
aliases:
- narrow canonical detector reads substantial baseline abstention as near-zero
- wide instrument reveals undosed hedge-idiom abstention baseline
- baseline abstention is not zero once idiom-inclusive grading is used
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal
  type: mechanism
  status: canonical
cause: "A wide, idiom-inclusive abstention instrument (a diverse detector-v2 pattern screen plus a blinded, symmetric human-adjudication lane) is applied to the UNDOSED baseline arm of a hedge-prone fired-confab pool (Mistral-7B-Instruct-v0.3, the mistral atlas site, at RR's fixed FIT-selected operating point), in place of the narrow locked 3-phrase canonical detector the pool was originally graded with."
effect: "Baseline (no write) adjudicated abstention reaches 368/1312 = 0.280 (Wilson 95% [0.257, 0.305]), while the same rows read only 208/1312 = 0.159 under detector-v2 alone, and near-zero under the original locked 3-phrase canonical detector. Widening the instrument therefore reveals that this confab pool already abstains at a substantial, non-trivial rate via hedge idioms a narrow canonical detector never counts. Consequence for methodology: a placebo/no-op tolerance calibrated on a near-zero-baseline assumption becomes strict, not generous, once the baseline itself is measured this way."
polarity: increases
related:
- '[[rr2-mistral-adjudicated-refusal-confirm]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[rr2-mistral-adjudicated-refusal-confirm]]'
  target_id: experiment:rr2-mistral-adjudicated-refusal-confirm
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md#outcome (RG3 gate results, baseline confab adjudicated abstention)
- type: related_to
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A confirmatory extension of `canonical-phrase-detector-undercounts-cross-family-abstention-idioms`,
found while registering a placebo for `rr2-mistral-adjudicated-refusal-confirm`:
widening the grading instrument does not just recover missed credit on a
dosed arm, it changes what the UNDOSED baseline reads as. Under the wide
instrument, Mistral's fired-confab pool already abstains at 28.0% with no
write applied at all, almost double the detector-v2-only rate and far above
the near-zero the original locked 3-phrase detector implied. This matters
for any downstream placebo design: a no-op tolerance transcribed from a
zero-baseline world is no longer appropriate once the baseline itself is
non-trivial under the wider instrument that motivated the change.
