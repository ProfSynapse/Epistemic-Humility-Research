---
aliases:
- gemma is actuable at shallow relative depth, contra its prior inert reputation
- depth-coverage artifact resolves the gemma cross-family null
- gemma actuates below the KV-sharing seam, strength falling toward it
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gemma-actuation-localizes-shallow-of-kv-seam
  type: mechanism
  status: canonical
cause: "A dosed known-unknown direction is written into Gemma-4-E4B-it at shallow relative depth below its KV-sharing seam (D1/hs15, relative depth 0.357, both donor blocks 22 and 23 still reachable), the first time any site below relative depth 0.81 was tested on this substrate in this program."
effect: "The write clears both primary held-out gates (confab clean_tighten 0.7857 [0.7176, 0.8410] against the 0.50 floor; known-correct cost 0.0111 against the 0.05 cap) with perfect direction-specificity against 5 magnitude-matched random-direction placebo draws, all of which produced zero lift. Actuation strength then falls off monotonically at greater relative depth approaching the seam (hs18 0.4464 FAIL, hs20 0.4048 FAIL, hs23 finds no usable dose on any ratio rung). Every prior gemma measurement in this program's cross-family line sat at relative depth >= 0.81, so gemma's standing reputation as inert or unsteerable was a depth-coverage artifact of where it had been dosed, not a property of the model."
polarity: enables
related:
- '[[gemma4-e4b-kv-seam-quarantine]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[gemma-4]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[gemma4-e4b-kv-seam-quarantine]]'
  target_id: experiment:gemma4-e4b-kv-seam-quarantine
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md#outcome (Phase A
    results table)
  - experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (Stage 6 rulings
    R3 per-arm G1/G2 table, R4 G3 direction-specificity, R6 ladder profile)
- type: related_to
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: medium
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md (the atlas's
    eff_dim_frac profile is flat mid-stack on gemma and supplied no
    site-selection signal, which is why this experiment used a linear-
    accessibility sweep and a fixed cross-family depth band instead)
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

Established on `google/gemma-4-E4B-it`'s below-seam depth ladder (D1-D4,
A3/hs22) under sharing-ON, unmodified-model conditions. The shallowest site
tested, D1/hs15, is also the strongest: G1 and G2 both PASS with the widest
margin of any arm, and G3's direction-specificity check is
PASS-DEGENERATE (five accepted magnitude-matched random-direction draws all
produced exactly zero lift, so the fitted direction's effect has no
comparator to be measured against, and the result is never citable as a
large effect ratio). A3/hs22 (relative depth 0.524) shows the same
PASS-DEGENERATE pattern. Effect strength then degrades in order at greater
depth: D2/hs18 and D3/hs20 fail the confab floor outright, and D4/hs23
(donor-reachable but adjacent to the seam) finds no ratio rung that clears
the floor without collapse.

This finding is deliberately narrower than a resolution of the KV-quarantine
hypothesis itself. It establishes that gemma is actuable at all -- reversing
a program-wide reading built entirely on above-seam sites (relative depth
0.81-1.00) -- and it arms the pre-registered falsifier's D-ladder leg
(D1 clears G1 while the above-seam replication arm does not), which the
falsifier reads as SUPPORTING the quarantine account without establishing
it: the depth ladder cannot on its own separate "actuation fails above the
seam because KV-sharing blocks the write" from a generic
shallow-band-only actuation profile, since every family in this program
shows *some* depth-dependent falloff. Promotion beyond "supported" required
the sharing ON/OFF contrast at a fixed site, which
[[kv-sharing-off-ablation-breaks-baseline-substrate]] forecloses in this
cell. See [[gemma4-e4b-kv-seam-quarantine]] for the full resolution and
[[seam-adjacent-gate-clearance-is-non-direction-specific]] for why the
seam-adjacent site's apparent clearance does not extend this pattern all
the way to the seam.
