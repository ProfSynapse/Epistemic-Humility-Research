---
title: gemma-quarantined-pocket-shows-no-direction-specific-actuation
aliases:
- gemma's quarantined pocket (hs25-hs27) shows no direction-specific actuation
- hs25 reproduces the hs24 non-specificity signature at a deeper quarantined site
- hs26/hs27 deepen the D4/hs23 dose-viability NOT-RUN pattern
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gemma-quarantined-pocket-shows-no-direction-specific-actuation
  type: mechanism
  status: canonical
cause: "A fitted known-unknown direction is dosed into Gemma-4-E4B-it at each of three sites one to three blocks deeper into the KV-sharing seam's quarantined region than A5/hs24 (hs25/E1 relative depth 0.595, hs26/E2 0.619, hs27/E3 0.643, all N >= 24 and therefore donor-unreachable by both KV-sharing donor blocks), sharing ON, unmodified model, with a mandatory direction-specificity control (G3, 5 magnitude-matched random-direction placebo draws) required at every arm regardless of whether the primary gates clear."
effect: "No arm produces a direction-specific actuation result. E1/hs25 finds a usable FIT dose and clears both primary held-out gates (G1 confab clean_tighten 0.7917 [0.7241, 0.8462]; G2 known-correct cost 0.0333 [0.0176, 0.0621]), but its mandatory G3 is ADJUDICATED FAIL: effect_ratio = 0.7917 / 0.6190 = 1.279, short of the 3.0 floor, because the worst of 5 placebo draws reproduced 78% of the fitted direction's lift -- the same disposition (actuates, not direction-specific) as A5/hs24 (effect_ratio 1.139), one site deeper into the quarantined region, with the same heavy-tailed placebo draw shape (one near-effect draw, four small). E2/hs26 and E3/hs27 are both dose-viability NOT-RUN: their FIT-split confab-tighten rates (0.375 and 0.250) never clear the 0.5 usability floor at any ratio rung, deepening the D4/hs23 NOT-RUN pattern one and two sites further past the seam. All three registered predictions (drafter, orchestrator, PI) were MET. Per the registered confound fence, rd and KV-quarantine status are perfectly correlated across this pocket, so this result is evidence that the band is unstable/non-actuable by this instrument; it does not by itself resolve the KV-quarantine hypothesis in either direction. With this result, every site of the cross-family operating range on gemma4-e4b above the seam has been measured, and none has produced an adjudicated direction-specific actuation."
polarity: mediates
related:
- '[[gemma4-e4b-pocket-ladder]]'
- '[[gemma4-e4b-kv-seam-quarantine]]'
- '[[seam-adjacent-gate-clearance-is-non-direction-specific]]'
- '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
- '[[gemma-4]]'
relationships:
- type: supported_by
  target: '[[gemma4-e4b-pocket-ladder]]'
  target_id: experiment:gemma4-e4b-pocket-ladder
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md#outcome (per-arm record)
  - experiments/gemma4-e4b-pocket-ladder/NOTEBOOK.md (2026-07-31 Stage 1 and
    Stage 2 adjudication entries)
- type: related_to
  target: '[[gemma4-e4b-kv-seam-quarantine]]'
  target_id: experiment:gemma4-e4b-kv-seam-quarantine
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md (Motivation and posture;
    the checkpoint, extraction, and instrument are reused from this parent
    cell, and the registered rule this experiment applies -- G3 mandatory
    where the parent left it optional -- is a direct response to the parent's
    own A5/hs24 result)
- type: related_to
  target: '[[seam-adjacent-gate-clearance-is-non-direction-specific]]'
  target_id: mechanism:seam-adjacent-gate-clearance-is-non-direction-specific
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md (Design, "G3
    direction-specificity is MANDATORY here"; E1/hs25's effect_ratio 1.279
    reproduces this mechanism's hs24 signature, effect_ratio 1.139, one site
    deeper into the quarantined region)
- type: related_to
  target: '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
  target_id: mechanism:gemma-actuation-localizes-shallow-of-kv-seam
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md (Prediction; cites the
    parent cell's monotonic below-seam falloff, D1/hs15 0.7857 down to
    D4/hs23 NOT-RUN, as the basis for the prior that this pocket sits below
    the gate that discriminates a specific effect)
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
---

This finding closes the last unmeasured band of the program's cross-family
operating range on gemma4-e4b and extends
[[seam-adjacent-gate-clearance-is-non-direction-specific]] from a single
site (A5/hs24) to a three-site pocket one to three blocks deeper into the
same KV-quarantined region. The extension is not uniform: E1/hs25 repeats
the hs24 pattern exactly (raw gate clearance without direction specificity,
same heavy-tailed placebo shape), while E2/hs26 and E3/hs27 do not even
reach the point of a direction-specificity test -- their FIT-split dose
calibration never finds a rung that clears the primary confab floor without
collapse, the same NOT-RUN disposition [[gemma-actuation-localizes-shallow-of-kv-seam]]
already recorded one site upstream at D4/hs23. Read together, the two
mechanisms describe a single monotonic pattern: actuation strength and
direction-specificity both fall off approaching and crossing the KV-sharing
seam, with the region beyond hs24 producing either non-specific gate
clearance or no usable dose at all, and never a direction-specific result.

This is deliberately narrower than a resolution of the KV-quarantine
hypothesis. Because relative depth and quarantine status are perfectly
correlated across E1/E2/E3 (registered as the "confound cuts both ways"
clause in `gemma4-e4b-pocket-ladder/AMENDMENT.md`), this result cannot
separate "gemma fails to actuate specifically in this band because it is
quarantined" from "gemma fails to actuate specifically in this band for an
unrelated depth-dependent reason that happens to coincide with the
quarantined region here." It is evidence that the band is inert to this
instrument's direction-specificity control, not evidence about why. See
[[gemma4-e4b-pocket-ladder]] for the full resolution.
