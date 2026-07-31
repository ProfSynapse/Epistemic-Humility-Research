---
title: gemma4-e4b-pocket-ladder
aliases:
- 'Gemma-4-E4B pocket ladder: hs25/hs26/hs27, sharing ON'
- gemma quarantined pocket actuation ladder
- E1/E2/E3 hs25-hs27 direction-specificity test
tags:
- kg/experiment
- experiment
- j-space
- cross-family
- gemma
kg:
  id: experiment:gemma4-e4b-pocket-ladder
  type: experiment
  status: canonical
related:
- '[[gemma4-e4b-kv-seam-quarantine]]'
- '[[gemma-4]]'
- '[[activation-steering]]'
- '[[gemma-quarantined-pocket-shows-no-direction-specific-actuation]]'
- '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
- '[[seam-adjacent-gate-clearance-is-non-direction-specific]]'
relationships:
- type: builds_on
  target: '[[gemma4-e4b-kv-seam-quarantine]]'
  target_id: experiment:gemma4-e4b-kv-seam-quarantine
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md (Design, Substrate and
    instrument; same checkpoint revision, same instrument copied file-for-file
    with three drifted modules, same FIT anchor extraction staged from this
    parent cell's committed artifacts)
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
- type: supports
  target: '[[gemma-quarantined-pocket-shows-no-direction-specific-actuation]]'
  target_id: mechanism:gemma-quarantined-pocket-shows-no-direction-specific-actuation
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md#outcome (per-arm record,
    E1/hs25 G3 FAIL and E2/hs26, E3/hs27 dose-viability NOT-RUN)
- type: related_to
  target: '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
  target_id: mechanism:gemma-actuation-localizes-shallow-of-kv-seam
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md (Prediction; the falloff
    D1/hs15 0.7857 -> D2/hs18 0.4464 -> D3/hs20 0.4048 -> D4/hs23 NOT-RUN
    continues at E2/hs26 and E3/hs27 dose-viability NOT-RUN, deeper into the
    same quarantined region)
- type: related_to
  target: '[[seam-adjacent-gate-clearance-is-non-direction-specific]]'
  target_id: mechanism:seam-adjacent-gate-clearance-is-non-direction-specific
  confidence: high
  evidence:
  - experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md#outcome (E1/hs25 G3
    ADJUDICATED FAIL, effect_ratio 1.279, reproducing the A5/hs24 signature
    one site deeper into the quarantined region)
---

Tier-2 exploratory follow-up to `gemma4-e4b-kv-seam-quarantine`, registered by
the PI 2026-07-31 to close the one band of the program's cross-family
operating range (relative depth 0.375-0.639, the union of every site that has
ever actuated on any family) that had never been written to on gemma: hs25
(E1, rd 0.595), hs26 (E2, rd 0.619), and hs27 (E3, rd 0.643), all `N >= 24`
and therefore fully inside Gemma-4-E4B-it's KV-sharing seam (donors at blocks
22/23; the quarantine cell's own ladder stopped at A5/hs24 on the
above-seam side). It is a standalone registration, not a reopening of the
quarantine cell's own signed arm set, and it is explicitly not a test of the
KV-quarantine hypothesis: because relative depth and quarantine status are
perfectly correlated across E1/E2/E3, neither a positive nor a negative
result here can by itself decide whether gemma actuates in this band because
of the depth or despite the quarantine.

Design ran a pure sharing-ON actuation ladder (no OFF arms, no patch-based
contrast) reusing the quarantine cell's checkpoint, extraction, and
instrument (13 of 17 Python modules byte-identical; three drifted:
`run_contrast.py` for provenance metadata and a generalized site-set guard,
`placebo_direction.py` for a widened per-site seed formula fixing a verified
cross-site collision defect, `family_config.py`/`families/gemma4-e4b.yaml`
for an additive `pocket` site set). Because the quarantine cell's own
A5/hs24 result had cleared its primary gates while failing
direction-specificity, G3 was made mandatory here for all three arms rather
than optional: no arm may be reported as actuation on G1/G2 alone.

Resolved 2026-07-31 (lead adjudication, re-derived from the committed
`pocket_rollup.json`). **No direction-specific actuation anywhere in the
pocket.** E1/hs25 found a usable FIT dose and cleared both G1 (held-out
confab clean_tighten 0.7917 [0.7241, 0.8462]) and G2 (known-correct cost
0.0333 [0.0176, 0.0621]) on held-out, but its mandatory G3 ADJUDICATED FAIL
(effect_ratio 0.7917/0.6190 = 1.279 against the 3.0 floor) reproduces the
hs24 signature exactly: the worst of 5 magnitude-matched random-direction
placebo draws reproduced 78% of the fitted direction's effect. E2/hs26 and
E3/hs27 were both dose-viability NOT-RUN (max FIT confab-tighten rates 0.375
and 0.250, below the 0.5 usability floor at every ratio rung), deepening the
D4/hs23 NOT-RUN pattern one and two sites further into the quarantined
region. All three registered predictions (drafter, orchestrator, PI) were
MET: sub-case (b) of the prediction at E1, sub-case (a) at E2/E3.

With this cell resolved, every site of the cross-family operating range on
gemma4-e4b above the seam has now been measured: hs24 (parent, G3 FAIL at
1.139), hs25 (this cell, G3 FAIL at 1.279), hs26/hs27 (this cell, no usable
dose). Interpretation stays inside the registered confound fence: this
result is evidence that the pocket band shows hs24-style instability, not a
resolution of the KV-quarantine hypothesis in either direction. See
[[gemma-quarantined-pocket-shows-no-direction-specific-actuation]] for the
full finding. Source of truth:
`experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md` (Outcome section),
`NOTEBOOK.md` (2026-07-31 adjudication entries), and `experiment.yaml`
(`verdict` field).
