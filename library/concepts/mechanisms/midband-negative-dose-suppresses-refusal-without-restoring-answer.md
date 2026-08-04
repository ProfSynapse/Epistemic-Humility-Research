---
aliases:
- output-gate suppression, not abstention control
- negative c_hat dose fails Arm B's specificity leg (override O-2)
- axis B resolves POSITIVE-ONLY
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:midband-negative-dose-suppresses-refusal-without-restoring-answer
  type: mechanism
  status: canonical
cause: "Negative dosing along the frozen hs20 c_hat direction under erase_write (setpoint -12.608 at -1.0x the reference dose, and -6.304 at -0.5x) is applied ungated to P-REFUSE, 421 rows where Qwen/Qwen3.5-4B naturally produced refused_on_answerable under this exact render on an answerable PopQA question, with no prior dosing."
effect: "Refusal drops decisively and with CIs excluding zero, from 0.969 at baseline by 0.760 absolute at -0.5x (to about 0.209) and by 0.948 absolute at -1.0x (to about 0.021), clearing the registered 0.20 release-magnitude floor at both valid rungs (the -2.0x rung is regime-invalid, degenerate rate 0.898 against the 0.20 C1 ceiling, and excluded from the axis-B read). But release is not specific: among released rows, correctness is only 0.094 at -0.5x and 0.105 at -1.0x against a registered 0.30 specificity floor, and the magnitude-matched random_direction placebo at -1.0x also moves refusal by 0.107, above the registered 0.05 ceiling meant to isolate the true direction's contribution. Both specificity legs fail, so the cell's registered override O-2 fires: the naming table's BIDIRECTIONAL leg is not earned even though the raw reduction leg clears, and the registered separate finding is recorded instead, negative dosing suppresses the refusal output surface without restoring the correct answer, an output-gate suppression rather than a reversible abstention-disposition control."
polarity: prevents
related:
- '[[write-direction-naming-battery]]'
- '[[margin-evidence-responsiveness-worldknown]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (Axis B, POSITIVE-ONLY via O-2)
- type: related_to
  target: '[[margin-evidence-responsiveness-worldknown]]'
  target_id: experiment:margin-evidence-responsiveness-worldknown
  confidence: medium
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Populations; P-REFUSE is drawn from this experiment's committed refused_on_answerable rows)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
---

This is the single most consequential axis in the write-direction naming
battery: BIDIRECTIONAL resolution here (a specific, reversible release of
natural over-refusal) would have earned the PI's candidate name, an
abstention/I-don't-know actuator. It does not resolve that way. The raw
reduction leg is unambiguous, negative dosing on natural refusals collapses
refusal from near-ceiling to near-floor at both valid negative rungs. What
fails is specificity on both registered checks at once: the released rows are
overwhelmingly still wrong rather than correct, and a magnitude-matched random
direction produces a comparable refusal drop, so the effect cannot be
attributed to the c_hat direction's content rather than to a generic
perturbation of the output-formation surface near this operating point.

The registered override O-2 exists precisely to prevent a raw
reduction-magnitude number from being read as directional, reversible
abstention control when specificity has not been separately demonstrated. The
resulting reading, output-gate suppression rather than abstention control, is
a negative constraint on how the mid-band write's negative-dose behavior may
be described going forward; it does not license "abstention actuator," "IDK
control," or any name implying restored correct answering.
