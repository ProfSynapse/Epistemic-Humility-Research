---
aliases:
- A real evidence-specific projection response that is sub-floor and behaviorally inert
- Evidence registration in the anchor state does not imply evidence-driven behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:evidence-registration-exists-without-driving-behavior-worldknown
  type: mechanism
  status: canonical
cause: "In margin-evidence-responsiveness-worldknown (M4-WK), a world-known c_hat direction refit natively (baseline AUROC 0.8628) is projected at the question's last-token anchor under three arms (no_answer_baseline, true_answer in-context, category-matched false_answer placebo) on 400 confident-wrong-on-answerable rows, testing both a collapse leg (does the true-answer shift meet a pre-registered floor, frozen before the shift was computed) and a specificity leg (is the true-answer shift larger than the false-answer placebo shift, the anti-tautology control against a direction merely detecting that any answer-shaped text is present)."
effect: "The specificity leg passes: the paired true-minus-false projection shift is 0.1022 (bootstrap 95% CI [0.0527, 0.1524], excluding zero, true answer larger), so the anchor state does carry a real, evidence-specific component that is not explained by the mere presence of an answer-shaped string. The collapse leg fails: the median true-answer shift (0.5921, CI [0.5364, 0.6694]) falls short of the pre-registered collapse floor (0.8209, frozen at the moment the fresh baseline gap was measured, before either shift was computed). Because both legs are required for criterion (d) and the paired margin channel is separately voided by a non-reproducing survival gate, the net reading is a projection response that is genuine and evidence-specific but too small to count as 'collapsing' the projection, and with no measurable behavioral counterpart: evidence registration exists in the internal state without driving abstention behavior."
polarity: complicates
related:
- '[[margin-evidence-responsiveness-worldknown]]'
- '[[confident-wrongness-steering-hits-coherence-ceiling-before-refusal]]'
- '[[commitment-margin]]'
- '[[margin-theory-of-epistemic-state]]'
relationships:
- type: supported_by
  target: '[[margin-evidence-responsiveness-worldknown]]'
  target_id: experiment:margin-evidence-responsiveness-worldknown
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Native direction, D1 leg-1/leg-2, Channel 2 void)
- type: related_to
  target: '[[confident-wrongness-steering-hits-coherence-ceiling-before-refusal]]'
  target_id: mechanism:confident-wrongness-steering-hits-coherence-ceiling-before-refusal
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (same native direction, same cell)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: medium
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: medium
---

The anti-tautology design in M4-WK separates two questions that a raw
projection shift alone cannot distinguish: does the direction respond to an
answer being present in context at all (a confound, since injecting the true
answer necessarily changes the prompt), or does it respond to THIS answer
being correct? The false-answer placebo, a category-matched distractor
injected under an identical anchor and template, isolates the second
question: only a shift larger for the true answer than for the placebo is
evidence beyond mere answer-presence.

The native world-known direction clears that specificity bar (leg 2) but
misses the collapse floor (leg 1), a real but sub-floor projection response.
Because the collapse floor was itself frozen by a repin the moment the fresh
baseline gap was measured, and strictly before either shift was computed, the
shortfall is not an artifact of a goalpost moved to make the direction fail;
the direction genuinely does not move far enough. The margin channel that
would have supplied a behavioral read on the same rows is separately void: a
staleness check found the no-answer baseline already produces non-trivial
survival at each row's own tipping dose (0.2549, far above the 0.05 ceiling
the check is supposed to enforce), so the paired margin contrast cannot be
interpreted at all on this direction, cause undiagnosed.

Read together, these two results describe a dissociation rather than a
uniform failure: a real, evidence-specific signal is present in the anchor
state (leg 2), it is too weak to count as collapsing the projection by the
pre-registered standard (leg 1), and no clean behavioral channel exists to
say whether that weak signal has any downstream effect at all. Evidence
registration and evidence-driven behavior are shown here to be separable
questions, not two readings of the same mechanism. Source of truth:
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` (Outcome,
Native direction section).
