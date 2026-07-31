---
aliases:
- gate clearance right at a KV-sharing seam boundary can be a random-direction artifact
- hs24 quarantine-control clearance fails its direction-specificity control
- seam-region instability masquerading as steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:seam-adjacent-gate-clearance-is-non-direction-specific
  type: mechanism
  status: canonical
cause: "At Gemma-4-E4B-it's first fully KV-quarantined site (A5/hs24, immediately downstream of both donor blocks 22 and 23, sharing ON, unmodified model), a fitted known-unknown direction clears both primary held-out gates (confab clean_tighten 0.7321 [0.6605, 0.7934]; known-correct cost 0.0333) and is tested against 5 magnitude-matched random-direction placebo draws at the identical site and dose."
effect: "The apparent actuation is NOT direction-specific: the worst single random draw reproduces 88% of the fitted direction's lift (effect_ratio 1.139, short of the pre-registered 3.0 floor), so the direction-specificity gate FAILS. The site also carries the highest full-mode collapse rate measured anywhere in the cell (0.0341). The gate clearance is adjudicated as seam-region instability that the primary confab/known-correct gates alone cannot distinguish from genuine steering, the opposite pattern from the shallower donor-reachable sites (hs15, hs22), which clear the identical direction-specificity control with zero lift on every one of 5 random draws (PASS-DEGENERATE)."
polarity: mediates
related:
- '[[gemma4-e4b-kv-seam-quarantine]]'
- '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[gemma-4]]'
relationships:
- type: supported_by
  target: '[[gemma4-e4b-kv-seam-quarantine]]'
  target_id: experiment:gemma4-e4b-kv-seam-quarantine
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (Stage 6 ruling R4,
    A5/hs24 G3 arithmetic)
- type: related_to
  target: '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
  target_id: mechanism:gemma-actuation-localizes-shallow-of-kv-seam
  confidence: high
  evidence:
  - 'experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (Stage 6 ruling R5 -- raw gate clearance does not separate hs22 from hs24; the G3 direction-specificity control does, completely)'
- type: related_to
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  confidence: low
  evidence:
  - both findings rest on magnitude-matched random-direction controls
    revealing that raw gate clearance or single-draw placebo readings are
    not automatically informative, though this finding uses a K=5
    single-site direction-specificity gate rather than a K=15 cross-family
    census
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
---

This is the descriptive control result that keeps
[[gemma-actuation-localizes-shallow-of-kv-seam]] from being read as "gemma
actuates everywhere below the seam, including right up to its boundary."
The registered secondary expectation (A3/hs22 clears both gates while
A5/hs24 does not) was not met in its literal form -- both sites clear G1 and
G2 -- so the separation the design was looking for shows up in the
direction-specificity control instead, and it shows up completely: hs22 is
PASS-DEGENERATE (zero lift on every placebo draw) while hs24 FAILS
(effect_ratio 1.139, well under the 3.0 floor). Combined with hs24 also
carrying the cell's highest full-mode collapse rate, the reading is that raw
gate clearance at a site immediately adjacent to a KV-sharing seam is not
trustworthy evidence of actuation on its own -- exactly the failure mode the
quarantine account predicts a KV-shared site should produce, since a
narrowed (not severed) causal channel can move gate metrics without genuine
direction-specific steering. Source: [[gemma4-e4b-kv-seam-quarantine]].
