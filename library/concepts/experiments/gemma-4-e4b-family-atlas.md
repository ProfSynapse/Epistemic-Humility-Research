---
title: gemma-4-e4b-family-atlas
aliases:
- Gemma-4-E4B-it family atlas
- third family-atlas cell (post-jspace)
tags:
- kg/experiment
- experiment
- j-space
- cross-family
kg:
  id: experiment:gemma-4-e4b-family-atlas
  type: experiment
  status: canonical
related:
- '[[jspace-family-atlas]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[refused-vs-known-contrast-carries-norm-position-confound]]'
relationships:
- type: tests
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: low
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md#prediction
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md#falsifier
- type: builds_on
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: high
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md (Motivation and posture, "identical procedure to jspace-family-atlas")
- type: builds_on
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md (Design, pin provenance and mined pool)
- type: supports
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: low
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md#outcome
- type: supports
  target: '[[refused-vs-known-contrast-carries-norm-position-confound]]'
  target_id: mechanism:refused-vs-known-contrast-carries-norm-position-confound
  confidence: medium
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md#outcome (random-direction control diagnostic)
---

Read-only, capture-only mapping experiment on `google/gemma-4-E4B-it`
(pinned revision `fee6332c1abaafb77f6f9624236c63aa2f1d0187`, 42 decoder
layers), the third registered family-atlas cell after
[[jspace-family-atlas]]'s Llama-3.2-3B-Instruct and Mistral-7B-Instruct-v0.3
cells. Unlike those two, no committed split manifest existed for this
substrate, so the cell first mined a fresh row pool through
`doubt-snap-cross-family-confirmatory`'s own never-launched
`gemma4_e4b_it` cell definition. That mining instrument (AG0a) needed two
signed re-specifications before it passed: revision 1 raised a hardcoded
200-token generation cap to 400 (Gemma is more verbose than the Qwen-family
cells the cap was calibrated on) and replaced a brittle exact-string parity
comparator with a role-relevant-grade comparator; revision 2 redefined the
termination limb from raw EOS-emission to answer-capture (a row counts as
captured if it emits EOS, or if its graded text contains a complete
well-formed first-JSON answer), after an independent red-team review
returned SIGN-WITH-CONSTRAINTS. Both revisions were scoped as
instrument-adequacy fixes, not findings; a signed stopping rule barred a
third re-specification of the same limb.

Once mining passed (AG0a v3, all five limbs), the atlas computed the same
per-layer `eff_dim_frac` (representation-variance participation-ratio) and
per-layer held-out AUROC read panel (doubt, caution, raw refusal) as
`jspace-family-atlas`, at all 43 hidden-state indices (embeddings + 42
decoder layers). The registered falsifier fired on the profile limb: the
single maximum sits at hs_index 4 (eff_dim_frac 0.0189, depth 0.095), inside
the outer-20% early-exterior region the falsifier named, with no interior
peak. The falsifier's second limb did not fire: a contiguous band from
hs_index 13 through 42 clears 0.80 held-out AUROC on all three axes
simultaneously, with hs_index 4-6 also marginally clearing it. Gemma-4-E4B-it
is therefore the third family, after Llama-3.2-3B-Instruct and
Mistral-7B-Instruct-v0.3, to show an early-exterior `eff_dim_frac` peak
decoupled from a healthy mid-band read panel
([[workspace-band-peak-location-is-family-relative]]), strengthening that
mechanism's cross-family generality beyond two data points.

The atlas also re-derived a fixed random-direction control over all 43
layers (the harness report had quoted only two). The control is near chance
at hs_index 0-8, 14-18, and 36-40, but elevated and spiky through much of the
mid-band (max-over-contrasts 0.83-0.97 at hs_index 10-12, 24, and 28-34, and
0.89 at hs_index 42). This is the same norm/position confound family
`jspace-family-atlas` documented on the doubt (refused-vs-known) contrast
specifically, but here it is layer-patchy across all three axes rather than
confined to one contrast, extending
[[refused-vs-known-contrast-carries-norm-position-confound]] beyond its
original axis-specific scope. The practical consequence: the naive
best-per-axis layers (doubt at hs_index 21, caution at hs_index 25, raw
refusal at hs_index 26) all sit where the control itself reads 0.80-0.97 and
are not clean reads; the clean-control layer sets with all three axes still
clearing 0.80 are hs_index 14-18 and hs_index 36-40 (the latter containing
the doubt-snap fleet's ported 0.94-depth write site, hs_index 40, where
doubt is the strongest axis at 0.9949, correcting the orchestrator's
pre-registered call that raw_refusal would read strongest there).

All four gates (AG0a mining integrity, AG0 capture/refit integrity, AG1
profile reproducibility, AG2 read-panel CIs) passed. Source of truth:
`experiments/gemma-4-e4b-family-atlas/AMENDMENT.md` (Outcome section) and
`experiment.yaml`.
