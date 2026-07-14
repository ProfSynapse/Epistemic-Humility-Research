---
title: rr-cross-family-raw-refusal
aliases:
- 'RR: Cross-family raw-refusal actuation at atlas-located workspace-band sites'
- rr-cross-family-raw-refusal
tags:
- kg/experiment
- experiment
- cross-family
- doubt-snap
kg:
  id: experiment:rr-cross-family-raw-refusal
  type: experiment
  status: canonical
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[jspace-family-atlas]]'
- '[[ungated-vs-gated-dose-matched]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[llama-atlas-site-write-collapses-format-before-refusal-floor]]'
- '[[mistral-atlas-site-write-abstains-below-canonical-detector-floor]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
relationships:
- type: related_to
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: medium
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md (Arms; selectivity control on knowns)
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: high
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: high
- type: supports
  target: '[[llama-atlas-site-write-collapses-format-before-refusal-floor]]'
  target_id: mechanism:llama-atlas-site-write-collapses-format-before-refusal-floor
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome (llama leg)
- type: supports
  target: '[[mistral-atlas-site-write-abstains-below-canonical-detector-floor]]'
  target_id: mechanism:mistral-atlas-site-write-abstains-below-canonical-detector-floor
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome (mistral leg)
- type: supports
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome (mistral leg binding caveat)
---

Registered successor to `doubt-snap-cross-family-confirmatory`: tests
whether a doubt-gated caution write actuates raw refusal on non-Qwen
families (Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3) when sited at
each family's OWN atlas-located workspace-band layers
([[jspace-family-atlas]]) rather than at the ported late site the
confirmatory indicted. Primary metric is a format-agnostic stated-confidence
refusal rate (`refused`), reported alongside well-formed rate, to separate
the read-actuate question from JSON format collapse.

Resolved 2026-07-13. **Falsifier FIRED: both families land in outcome shape
F** (no FIT-viable (layer, dose) rung in the bracketed grid clears the
dose-viability floors), so held-out scoring (G1, G3(i) placebo, the
`dose_knowns_ungated` selectivity control) never ran for either family. The
amendment-level verdict is NOT promoted.

The two legs fail for genuinely different reasons, both instrument-verified
by adversarial red-team:

- **Llama-3.2-3B-Instruct**: format collapse before the refusal floor. Best
  refused rung reaches 0.457 (well-formed 0.700, below floor); best rung
  with well-formed intact reaches only 0.333 refused. The refused and
  well-formed floors trend oppositely with dose and never clear together.
  Robust to detector width: crediting every hand-found abstention idiom
  still only reaches 0.457 < 0.60
  ([[llama-atlas-site-write-collapses-format-before-refusal-floor]]).
- **Mistral-7B-Instruct-v0.3**: canonical-phrase coverage. Peak rung
  reaches refused 0.5793 against the 0.60 floor (well-formed 0.977, cost
  0.024), a 2.1-point miss with format and cost both clean. NOT robust to
  detector width: 97 hand-verified well-formed abstention idioms phrased
  outside the locked 3-phrase detector's vocabulary would raise the peak to
  0.679-0.701, clearing the floor
  ([[mistral-atlas-site-write-abstains-below-canonical-detector-floor]]).

The contrast between the two legs establishes a general methods finding,
[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]:
an exact-phrase refusal/abstention detector calibrated on one family
systematically undercounts another family's abstention idioms, and this
undercount is family-specific rather than a uniform correction. Source of
truth: `experiments/rr-cross-family-raw-refusal/AMENDMENT.md`.
