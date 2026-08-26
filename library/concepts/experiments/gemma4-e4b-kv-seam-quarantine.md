---
title: gemma4-e4b-kv-seam-quarantine
aliases:
- 'Gemma-4-E4B KV-sharing seam: is the mid-band null a quarantine artifact?'
- gemma KV seam quarantine test
- gemma4-e4b sharing ON/OFF contrast
tags:
- kg/experiment
- experiment
- j-space
- cross-family
- gemma
kg:
  id: experiment:gemma4-e4b-kv-seam-quarantine
  type: experiment
  status: canonical
related:
- '[[j-space-cross-family-layer-contrast]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[gemma-4]]'
- '[[activation-steering]]'
- '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
- '[[kv-sharing-off-ablation-breaks-baseline-substrate]]'
- '[[seam-adjacent-gate-clearance-is-non-direction-specific]]'
relationships:
- type: builds_on
  target: '[[j-space-cross-family-layer-contrast]]'
  target_id: experiment:j-space-cross-family-layer-contrast
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md (Motivation and
    posture; re-grounds that experiment's gemma4-e4b arm, which stopped at a
    registered G0 dose-viability rule on activations later found corrupted
    by use_cache=False)
- type: builds_on
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md (reuses the family
    atlas's checkpoint, eval-pool provenance, and eff_dim_frac profile; the
    atlas's flat mid-stack profile is the reason site selection here uses
    A_lin instead)
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
- type: supports
  target: '[[gemma-actuation-localizes-shallow-of-kv-seam]]'
  target_id: mechanism:gemma-actuation-localizes-shallow-of-kv-seam
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md#outcome (Phase A,
    D1/hs15 result)
  - experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (Stage 6 rulings
    R3, R4, R6)
- type: supports
  target: '[[kv-sharing-off-ablation-breaks-baseline-substrate]]'
  target_id: mechanism:kv-sharing-off-ablation-breaks-baseline-substrate
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md#outcome (C1 FAIL)
  - experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (2026-07-31 C1
    real-run and adjudication entries)
- type: supports
  target: '[[seam-adjacent-gate-clearance-is-non-direction-specific]]'
  target_id: mechanism:seam-adjacent-gate-clearance-is-non-direction-specific
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (Stage 6 ruling R4,
    A5/hs24)
---

Tier-2 exploratory follow-up to `j-space-cross-family-layer-contrast`, whose
gemma4-e4b arm had stopped at a registered G0 dose-viability rule using only
above-seam sites (hs34/hs38/hs40/hs42, relative depth 0.81-1.00) on
activations later found to be corrupted by `use_cache=False`. This experiment
re-grounds on a clean `use_cache=True` extraction and tests whether that
above-seam null was a quarantine artifact of Gemma-4-E4B's cross-layer
KV-sharing (blocks 24-41 read frozen K/V from donor blocks 22/23, so a write
above the seam cannot change what later layers attend over, though the query
path, FFN, and residual stream remain reachable -- the causal channel is
narrowed, not severed) rather than evidence the model is unsteerable.

Design ran in two phases on `google/gemma-4-E4B-it` (raw-base instruct, bf16,
42 blocks, snapshot `fee6332c1abaafb77f6f9624236c63aa2f1d0187`). Phase A
(sharing ON, unmodified model) swept a below-seam depth ladder (D1-D4:
hs15/hs18/hs20/hs23) plus donor-reachable and quarantined controls (A3/hs22,
A5/hs24). Phase B was the primary, pre-stated contrast: the same site
(hs38) with KV-sharing toggled OFF via a registered cache-patch
(`kv_seam_patch.py`), gated on a precondition control (C1) verifying the
OFF-ablation does not itself break the model.

**Terminal verdict (resolved 2026-07-31):** C1 FAIL -- the sharing-OFF
ablation destroys baseline behavior even without injection (known-correct
cost 180/180 vs the sharing-ON baseline's 0/180, Newcombe 95% CI
[0.9704, 1.0] against the 0.05 cap; mean NLL 3.5342 to 12.3303). The primary
A1-vs-A2 sharing-ON/OFF contrast is therefore NOT-RUN, and A2/A4 resolve
INCONCLUSIVE as pre-registered. The falsifier's D-ladder leg fires on the
Phase A results alone: D1/hs15 clears the confab gate on held-out
(0.7857 [0.7176, 0.8410]) while A1 (hs38, sharing ON) reproduces the
parent's no-usable-dose null, so the above-seam null is not a property of
the model -- the KV-quarantine account is SUPPORTED, explicitly NOT
ESTABLISHED, since promotion required the sharing-toggle contrast this
cell's C1 FAIL forecloses. See
[[gemma-actuation-localizes-shallow-of-kv-seam]],
[[kv-sharing-off-ablation-breaks-baseline-substrate]], and
[[seam-adjacent-gate-clearance-is-non-direction-specific]] for the three
findings this resolution rests on.

The program-level reading of gemma as inert or unsteerable, which every
prior measurement in this line only ever tested at relative depth >= 0.81,
does not survive this resolution: gemma actuates cleanly and
direction-specifically at shallow depth (rd 0.357-0.524), with strength
falling monotonically toward the seam and collapsing into non-specific
instability directly at the first quarantined site (hs24). Source of truth:
`experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` (Outcome section),
`NOTEBOOK.md` (Stage 6 rulings and the 2026-07-31 C1 entries), and
`experiment.yaml` (`verdict` field).
