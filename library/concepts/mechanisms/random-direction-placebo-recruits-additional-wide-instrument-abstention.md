---
aliases:
- placebo write is not a no-op under a wide abstention instrument
- random direction recruits hedge idioms on a hedge-prone pool
- placebo tolerance must be registered against the wide-instrument baseline
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:random-direction-placebo-recruits-additional-wide-instrument-abstention
  type: mechanism
  status: canonical
cause: "A magnitude-matched random_direction write (the registered G3 placebo, same anchor and dose as the real doubt-gated caution write) is applied to a hedge-prone fired-confab pool (Mistral-7B-Instruct-v0.3, mistral atlas site) already shown to carry substantial undosed baseline abstention under a wide idiom-inclusive instrument, and scored with that same instrument (detector-v2-refused OR blinded-adjudication-credited)."
effect: "Adjudicated abstention rises from the undosed baseline 368/1312 = 0.280 to 465/1312 = 0.354 under the random-direction placebo, a +7.39 point delta (Wilson 95% [0.329, 0.381]) against a registered 2-point no-op tolerance, so the placebo fails as a non-no-op. The excess is carried entirely by adjudicated hedge idioms, not by the narrow screen: detector-v2-only credits DROP under the random direction (208/1312 = 0.159 baseline vs 180/1312 = 0.137 random) while adjudication-only credits rise from 160 to 285. A magnitude-matched, non-semantic write can therefore recruit measurable additional abstention on a hedge-prone pool once measured with a wide instrument, so any placebo or no-op tolerance for such an instrument must be registered against the wide-instrument baseline, not transcribed from a narrow-instrument world where the baseline read near zero."
polarity: increases
related:
- '[[rr2-mistral-adjudicated-refusal-confirm]]'
- '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[rr2-mistral-adjudicated-refusal-confirm]]'
  target_id: experiment:rr2-mistral-adjudicated-refusal-confirm
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md#outcome (RG3 placebo fail, certified by adversarial red-team review)
- type: related_to
  target: '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
  target_id: mechanism:wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Direct consequence of `wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal`:
once the wide instrument shows the baseline itself is non-trivial, a
placebo write that is directionally random but magnitude-matched to a real
intervention is no longer guaranteed to be a no-op against that baseline.
On `rr2-mistral-adjudicated-refusal-confirm`'s certified RG3 fire, the
random_direction placebo lifted adjudicated abstention +7.4 points over
baseline on the confab population (known-correct population unaffected,
delta 0.0), entirely through additional credited hedge idioms rather than
detector-v2 hits, which an independent red-team review confirmed was not an
artifact of grader bias or degenerate output. The gated write's own lift
over baseline (+41.9 points) is still 5.7 times the placebo's, but the
registered RG3 leg is a fixed-tolerance test on the placebo delta, not a
ratio test, and the fixed 2-point tolerance (transcribed from a
zero-baseline world) fails under the wide instrument. Forward implication,
not a gate change: any successor testing direction-specificity under a wide
abstention instrument must register its placebo tolerance, or an explicit
effect-ratio gate, against the wide-instrument baseline measured before new
data.
