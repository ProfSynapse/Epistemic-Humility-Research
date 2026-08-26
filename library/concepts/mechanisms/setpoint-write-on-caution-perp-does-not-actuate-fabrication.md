---
aliases:
- Unvalidated refit caution_perp setpoint write does not actuate fabrication (confounded null)
- propensity-selected caution-actuated regulator was decision-inert with an unvalidated actuator
- AN confounded null: refit caution direction never shown to be a lever
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:setpoint-write-on-caution-perp-does-not-actuate-fabrication
  type: mechanism
  status: canonical
cause: "An erase-and-write setpoint push (h' = h - (h.c_hat)c_hat + g*sigma_c*c_hat, g=+2, clipped) on an UNVALIDATED caution_perp direction REFIT on the AI-TRUE checkpoint (cosine -0.064 with AC's validated GRPO-v2 caution_perp, i.e. essentially orthogonal), applied to rows FLAGGED by the confabulation-propensity sensor (prop_z >= 1.00), verified to land precisely on-axis (readback mean observed setpoint 43.98 vs commanded 44.26, max abs error 0.58 against sigma 22.13). The refit direction was never independently shown to be a behavioral lever on this checkpoint (the positive-control screen was deferred, not run), so this is a CONFOUNDED null."
effect: "Did not change the fabricate-vs-refuse decision in either direction: 0 of 116 baseline confabs killed at any gain (g in {+1,+2,+3}); primary-minus-control specificity diff 0, bootstrap CI [0.0, 0.0]; all 47 flagged confabs land in confab_to_different_confab; the reverse push (g=-2) de-refuses 0 of 114 answerable-refused rows. CAVEAT (why polarity is weak): because the actuator direction was never validated as a lever on this checkpoint, this null cannot distinguish 'the caution axis cannot suppress confabulation' from 'this refit direction is a dead actuator.' It is NOT evidence that write-side edits are inert in general: AC is a write-side erase-write on caution_perp that PASSED (+8.7pt)."
polarity: mediates
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

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

Amendment AN (2026-07-06, AI-TRUE checkpoint, local 3090, single seed) selected
rows with the confabulation-propensity sensor (prop_z >= 1.00,
[[confab-propensity-push-reaches-confab-cloud]]) and applied an erase-and-write
caution setpoint on caution_perp. Both AN-G2 (reach floor >= 5 kills) and AN-G3
(specificity floor, primary-minus-control >= 5 with a CI excluding zero) missed
at zero: 0 of 116 confabs killed, all 47 flagged confabs converted to a
different confab category, never a refusal. AN-G1 (collateral) passed but is
vacuous: zero effect on flagged corrects too, so the pass carries no honesty
guarantee. A precision readback confirmed the write landed on-axis to within
0.58 of a sigma-22.13 scale, ruling out an injection-fidelity failure.

This null is CONFOUNDED and must be read as such. The actuator was NOT AC's
actuator: AC coupled doubt to the GRPO-v2 caution_perp, a direction refined B1
had already validated as a lever (ablation moves known_refused refusal
0.994 -> 0.524 with specificity). AN's actuator is caution_perp REFIT on the
AI-TRUE checkpoint, cosine -0.064 with AC's direction, essentially orthogonal
and never independently validated as a lever here (the positive-control screen
was deferred). So the null cannot separate "the caution axis cannot suppress
confabulation" from "this refit direction is a dead actuator." It is emphatically
NOT support for any "input-side actuates, write-side nulls" rule: AC is itself a
write-side erase-write on caution_perp and it PASSED (+8.7pt, AC-G1). The correct
next step is to validate a caution actuator on this checkpoint (the section 6
screen) and then couple it to the propensity readout the way AC coupled doubt.
