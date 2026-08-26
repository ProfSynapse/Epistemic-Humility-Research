---
aliases:
- qwen hs34 sign-opposition claim retired as a draw accident
- the historical hs34 suppressive draw is not a family-signed response
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-l34-random-direction-sign-is-a-draw-level-accident
  type: mechanism
  status: canonical
cause: "Fifteen fresh matched-dose random unit directions (seeds 920001-920015) are applied at the same site (hs34), dose (200.0), rows, and instrument as the historical single random-direction draw (seed 20260707) that had shifted raw-base Qwen3-4B's wide-instrument confab rate by -4.3pp (a suppressive sign) in `wide-instrument-control-rescore`."
effect: "Only 6 of the 15 fresh seeds land negative (9 positive); the per-seed signed lifts over the frozen 0.1135 baseline range from -7.0pp (seed 920011) to +13.0pp (seed 920006), median +0.5pp, straddling zero with a slight positive lean. The registered sign-consistency gate (>= 12/15 negative) FAILS. The historical draw's -4.3pp suppression at this site is therefore a draw-level accident, not evidence of a family-signed suppressive placebo response at the hs34 late-site operating point, and the sign-opposition phrasing tying it to qwen's family identity is retired from the manuscript claims at this operating point specifically."
polarity: complicates
related:
- '[[qwen3-4b-l34-placebo-seed-census]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[wide-instrument-control-rescore]]'
relationships:
- type: supported_by
  target: '[[qwen3-4b-l34-placebo-seed-census]]'
  target_id: experiment:qwen3-4b-l34-placebo-seed-census
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md#outcome (QG-G2)
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md#outcome
    (Outcome, QG-G2; weakens only the hs34-specific corroboration of that
    mechanism's qwen reading, not its separate abstention-wide-instrument-
    calibration evidence at a different operating point)
- type: related_to
  target: '[[wide-instrument-control-rescore]]'
  target_id: experiment:wide-instrument-control-rescore
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md (Motivation and
    posture; the historical draw this mechanism reassesses is WG-G1's own
    random-direction arm)
---

`wide-instrument-control-rescore` had read its single hs34 random-direction
draw's -4.3pp suppression as consistent with
`random-direction-placebo-response-is-family-specific-in-sign`'s qwen
reading. A fifteen-seed distribution at the identical operating point shows
that single draw was not representative: the fresh distribution splits 6
negative / 9 positive and straddles zero. This does not overturn the broader
family-specific-sign mechanism, whose qwen evidence comes from a different,
pooled operating point in `abstention-wide-instrument-calibration` (-5.13pp,
14/15 seeds negative under its own census); it narrows that mechanism's
claim by removing the hs34 late-site single draw as corroborating evidence
and retires the sign-opposition phrasing specifically at that site.
