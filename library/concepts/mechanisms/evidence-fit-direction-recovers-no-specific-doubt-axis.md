---
aliases:
- The evidence-maximizing direction is no better than covariance-shaped chance
- Fitting a direction to the true-vs-false evidence contrast does not recover a doubt axis
- Fragmentation upgraded from small-along-native-axis to no-recoverable-axis
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:evidence-fit-direction-recovers-no-specific-doubt-axis
  type: mechanism
  status: canonical
cause: "In evidence-response-direction-search (M4c), a direction d_ev is fit as the mean paired difference between true_answer and false_answer_placebo hs20 anchor states over 200 fit confab rows, the linear direction that maximizes the in-context true-vs-false evidence contrast, then read at the no_answer_baseline arm on 200 held-out confab rows plus 360 correct-control rows, and compared against three covariance-shaped random-direction null flavors (K=1000 draws each) and the native ignorance-fit c_hat_worldknown direction, both recomputed on the identical held-out rows."
effect: "d_ev fires at baseline (held-out confab-vs-correct AUROC 0.7252, CI [0.6832, 0.7652]), clearing the pre-registered 0.70 firing floor. But it fails specificity against every null flavor tested: the registered covariance-shaped null's 95th percentile is 0.8194 (empirical p = 0.191), an isotropic companion null's is 0.7477 (p = 0.079), and an unregistered within-class-centered null's is 0.780 (p = 0.113); d_ev clears none of the three. It is also decisively weaker than the native ignorance-fit direction on the same held-out rows (0.8633; paired AUROC-difference -0.1381, CI [-0.1895, -0.0872], well below the STRONG-bar lower-CI floor of -0.05). The direction built purely to maximize the in-context evidence contrast separates confab from correct at baseline, but no better than generic covariance-shaped geometry would, and substantially worse than a direction fit directly on ignorance. M4-WK's fragmentation reading (the evidence leg and the ignorance leg do not co-locate on the native axis) is upgraded: no linearly recoverable axis reachable from the evidence contrast carries doubt-specific content beyond baseline geometry."
polarity: complicates
related:
- '[[evidence-response-direction-search]]'
- '[[evidence-registration-exists-without-driving-behavior-worldknown]]'
- '[[evidence-contrast-direction-encodes-answer-availability-not-doubt]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[known-unknown-direction]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[evidence-response-direction-search]]'
  target_id: experiment:evidence-response-direction-search
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md#outcome (Rung (c), D_c FAILS, all flavors)
- type: related_to
  target: '[[evidence-registration-exists-without-driving-behavior-worldknown]]'
  target_id: mechanism:evidence-registration-exists-without-driving-behavior-worldknown
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md (Relation to prior cells; M4-WK leg-2 is the existence proof this cell's fit inverts)
- type: related_to
  target: '[[evidence-contrast-direction-encodes-answer-availability-not-doubt]]'
  target_id: mechanism:evidence-contrast-direction-encodes-answer-availability-not-doubt
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md#outcome (same direction, same cell, diagnostic follow-up on why specificity fails)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: medium
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

M4c inverts M4-WK's audition: rather than testing whether a pre-fit ignorance
direction responds to evidence, it fits a direction directly to the
true-vs-false evidence contrast and asks whether that constructed direction
independently earns the naming criterion's rung (a), tracking prospective
ignorance at baseline where no answer is in context.

The result splits the two halves of that question. `d_ev` does clear the
firing floor: rung (a) passes. But the rung-(c) specificity companion is the
one that decides whether a pass means anything, and it fails across every
null flavor tried, including an unregistered, deliberately less-conservative
one added to rule out the conservative-null objection. A direction fit to
maximize an evidence contrast that separates confab from correct no better
than a random direction drawn from the same activation covariance is not
carrying evidence-specific content; it is riding baseline geometry any
direction in that neighborhood would ride. Read against the native
ignorance-fit direction's much larger and cleanly specific separation on the
identical rows, the gap sharpens the reading further: the axis that
maximizes the evidence contrast is not merely non-specific, it is a
materially worse ignorance detector than the direction fit directly on
ignorance.

M4-WK's leg-2 pass showed a real evidence-specific signal exists somewhere in
the anchor state, just small along the native axis; that left open whether a
different linear direction could recover it more cleanly. M4c closes that
door: constructing the direction most favorable to the evidence contrast does
not find a hidden, more legible doubt axis. Source of truth:
`experiments/evidence-response-direction-search/AMENDMENT.md` (Outcome, Rung
(c) and Interpretation sections).
