---
aliases:
- Setpoint write on caution_perp does not actuate fabrication
- propensity-selected caution-actuated regulator is decision-inert
- sensor-actuator composition does not reach the confab cloud
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:setpoint-write-on-caution-perp-does-not-actuate-fabrication
  type: mechanism
  status: canonical
cause: "An erase-and-write setpoint push (h' = h - (h.c_hat)c_hat + g*sigma_c*c_hat, g=+2, clipped) on the doubt-orthogonalized caution_perp coordinate at L35, applied to rows FLAGGED by the confabulation-propensity sensor (prop_z >= 1.00), verified to land precisely on-axis (readback mean observed setpoint 43.98 vs commanded 44.26, max abs error 0.58 against sigma 22.13)."
effect: "Does not change the fabricate-vs-refuse decision in either direction. 0 of 116 baseline confabs killed at any gain on the dose ladder (g in {+1,+2,+3}); primary-minus-control specificity diff 0 with bootstrap CI [0.0, 0.0]; all 47 flagged confabs land in confab_to_different_confab (the write changes the generated text but never flips fabricate to refuse). The same actuator pushed the opposite direction (g=-2) also de-refuses 0 of 114 baseline answerable-refused rows. The write is precise and output-changing but decision-inert."
polarity: prevents
related:
- '[[internal-an-setpoint-regulator-null--true-checkpoint]]'
- '[[confabulation-propensity-direction]]'
- '[[confab-cloud]]'
- '[[confab-propensity-push-reaches-confab-cloud]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
relationships:
- type: supported_by
  target: '[[internal-an-setpoint-regulator-null--true-checkpoint]]'
  target_id: paper:internal-an-setpoint-regulator-null
  confidence: high
- type: related_to
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: related_to
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
- type: related_to
  target: '[[confab-propensity-push-reaches-confab-cloud]]'
  target_id: mechanism:confab-propensity-push-reaches-confab-cloud
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: related_to
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
contradicted-by: []
---

Amendment AN (2026-07-06, AI-TRUE checkpoint, local 3090, single seed) tested
the one combination the program's earlier write-side nulls had not closed:
select rows with the sensor that has proven reach into the confab cloud (the
confabulation-propensity direction, [[confab-propensity-push-reaches-confab-cloud]]),
then actuate them with the knob proven to move behavior elsewhere (Amendment
AC's erase-and-write caution setpoint). Both AN-G2 (reach floor >= 5 kills) and
AN-G3 (specificity floor, primary-minus-control >= 5 with a CI excluding zero)
missed at zero: 0 of 116 confabs killed, 0 of 47 flagged confabs converted to a
different confab category never a refusal. AN-G1 (collateral) passed but is
vacuous: zero effect on flagged corrects too, so the "pass" carries no honesty
guarantee, only the absence of the risk the effect never posed. A precision
readback confirmed the write landed on-axis to within 0.58 of a sigma-22.13
scale, ruling out an injection-fidelity failure. This closes the pairing AL's
same-direction push and AI's reward-channel test each left open: neither an
imprecise write (ruled out here and in AL) nor the wrong actuator (AC's
actuator demonstrably moves behavior on its own population) explains the
null; the caution_perp coordinate, reached this precisely on propensity-
flagged rows, simply does not carry the fabricate-vs-refuse decision for this
population. caution_perp is a correlate of the caution behavior it was fit on,
not a general-purpose lever the confab cloud will answer to when addressed
through a different sensor.
