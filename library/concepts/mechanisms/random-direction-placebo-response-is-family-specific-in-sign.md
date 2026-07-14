---
aliases:
- matched-magnitude random perturbation shifts abstention with family-specific sign
- placebo recruitment is not directionally consistent across families
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  type: mechanism
  status: canonical
cause: "A magnitude-matched random_direction write (the registered placebo, same anchor and dose family as the real doubt-gated caution write) is applied to the confab pool of two families under the identical wide abstention instrument: Qwen3.5-4B at its promoted heldout operating point (paired baseline vs random_direction, n = 1,286 paired confabs) and Mistral-7B-Instruct-v0.3 at its RR-selected operating point (cited from RR2)."
effect: "The placebo shifts wide-instrument confab abstention in OPPOSITE signs by family: qwen's paired rate drops from 139/1286 = 0.108 to 73/1286 = 0.057, a -5.13 point SUPPRESSION with non-overlapping confidence intervals, while mistral's rate rises from 0.280 to 0.354, a +7.39 point RECRUITMENT (RR2, cited). A magnitude-matched random perturbation is therefore not a directionally consistent no-op across families: the sign of its effect on wide-instrument abstention is itself a family property, so a placebo or no-op tolerance for a direction-specificity gate must be two-sided and sized per family rather than assuming either a near-zero delta or a single-sign recruitment pattern."
polarity: mediates
related:
- '[[abstention-wide-instrument-calibration]]'
- '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
- '[[undosed-wide-instrument-baseline-abstention-is-family-graded]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#outcome (Qwen placebo detail; falsifier adjudication)
- type: related_to
  target: '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
  target_id: mechanism:random-direction-placebo-recruits-additional-wide-instrument-abstention
  confidence: high
- type: related_to
  target: '[[undosed-wide-instrument-baseline-abstention-is-family-graded]]'
  target_id: mechanism:undosed-wide-instrument-baseline-abstention-is-family-graded
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Extends, rather than contradicts, `random-direction-placebo-recruits-additional-wide-instrument-abstention`:
that mechanism establishes mistral's placebo RECRUITS +7.39 points of
additional wide-instrument abstention. Measuring the same placebo on qwen at
its own promoted operating point finds the opposite sign: a -5.13 point
SUPPRESSION, with confidence intervals that do not overlap. The pairing of
these two results is the finding, not either result alone: a
matched-magnitude random direction does not have a universal recruit-only
relationship with wide-instrument abstention, its effect's sign is itself a
family property. `abstention-wide-instrument-calibration`'s falsifier
adjudication turns on this signed reading: under a signed interpretation the
qwen delta does not fire the registered ">= 5 points" trigger, because its
own stated consequent ("perturbation-recruited hedging") is a claim a
suppression directly contradicts.
