---
title: qwen3-4b-family-atlas
aliases:
- Qwen3-4B family atlas
- fourth family-atlas cell (post-gemma)
tags:
- kg/experiment
- experiment
- j-space
- cross-family
kg:
  id: experiment:qwen3-4b-family-atlas
  type: experiment
  status: canonical
related:
- '[[jspace-family-atlas]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[j-space-localization-qwen3-4b]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[doubt-gated-caution-tighten]]'
- '[[eff-dim-peak-decoupled-from-readable-band]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[refused-vs-known-contrast-carries-norm-position-confound]]'
relationships:
- type: tests
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: low
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#prediction
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#falsifier
- type: builds_on
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: high
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md (Motivation and posture, "identical procedure to jspace-family-atlas and gemma-4-e4b-family-atlas")
- type: builds_on
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: high
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md (Motivation and posture, fourth family-atlas cell after gemma-4-e4b-family-atlas)
- type: builds_on
  target: '[[j-space-localization-qwen3-4b]]'
  target_id: experiment:j-space-localization-qwen3-4b
  confidence: high
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md (Motivation and posture, registry-hole rationale)
- type: builds_on
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: medium
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md (Design, reused split_manifest.json promoted from doubt-gated-caution-tighten)
- type: supports
  target: '[[eff-dim-peak-decoupled-from-readable-band]]'
  target_id: mechanism:eff-dim-peak-decoupled-from-readable-band
  confidence: low
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#outcome
- type: supports
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: low
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#outcome
- type: supports
  target: '[[refused-vs-known-contrast-carries-norm-position-confound]]'
  target_id: mechanism:refused-vs-known-contrast-carries-norm-position-confound
  confidence: medium
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#outcome (doubt-axis ref_vs_known control)
---

Read-only, capture-only mapping experiment on raw-base `unsloth/Qwen3-4B`
(pinned revision `64033659d5caf1b8ed7f929b29de705e93a4d468`, 36 decoder
layers, hidden size 2560), the fourth registered family-atlas cell after
[[jspace-family-atlas]]'s Llama-3.2-3B-Instruct and Mistral-7B-Instruct-v0.3
cells and [[gemma-4-e4b-family-atlas]]'s Gemma-4-E4B-it cell. It is also the
first cell to atlas the substrate the program's own ported-layer rule
(`round(0.94 * (num_hidden_layers - 1))`) was originally copied FROM, and the
first to run this skill's capture-only representation-variance profile plus
held-out read panel on the same checkpoint [[j-space-localization-qwen3-4b]]
already probed with a different, JVP-based J-lens instrument.

Resolved 2026-07-21: the registered falsifier fired on the profile limb. The
per-layer `eff_dim_frac` (representation-variance participation-ratio)
profile peaks at hs_index 5 of 36 (value 0.0149, depth_frac 0.1389), inside
the outer-20% early-exterior region the falsifier named, with the top-5
`eff_dim_frac` layers (hs 5, 4, 6, 3, 2) all early and a 20%-FIT-row
subsample reproducing the same peak layer exactly (AG1 profile
reproducibility PASS). The falsifier's second limb did not fire: hs_index
22-36 (15 layers) clear held-out AUROC >= 0.80 on all three read axes (doubt,
caution, raw_refusal) simultaneously, with caution and raw_refusal carrying
that band over their own random-direction controls by a clean margin (doubt
is confounded, see below). Qwen3-4B is therefore the fourth family, after
Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3, and Gemma-4-E4B-it, to show
an early-exterior `eff_dim_frac` peak decoupled from a healthy interior
read band ([[eff-dim-peak-decoupled-from-readable-band]]), and the fourth
family whose peak and readable-band locations both sit at a family-relative
depth rather than a shared portable fraction
([[workspace-band-peak-location-is-family-relative]]).

At the profile's own peak (hs5), caution (0.670) and raw_refusal (0.737) both
read BELOW the 0.80 threshold, a direct instrument dissociation on the same
layer where dimensionality itself peaks; the three epistemic axes only read
well from hs22 onward. This also resolves an apparent tension with
[[j-space-localization-qwen3-4b]]'s J-lens finding on this exact substrate:
the J-lens (a different, JVP-based estimator) localized an interior
effective-dimensionality peak at hs23-29 on the same checkpoint, but this
cell's representation-variance `eff_dim_frac` profile peaks early-exterior at
hs5 instead. The read panel's own interior band (hs22-36) sits on top of the
J-lens hs23-29 band, so the J-lens was tracking the interior readable regime,
not the dimensionality peak the participation-ratio estimator finds.

The doubt (known-unknown) axis reads near-ceiling (>= 0.975 from hs5 onward)
but its own `ref_vs_known` random-direction control spikes to 0.87-0.98 at
hs 21/24/32/36, the same norm/position confound
[[refused-vs-known-contrast-carries-norm-position-confound]] documented on
llama and mistral (axis-specific) and on gemma-4-e4b (layer-patchy,
cross-axis); here the confound replicates a fourth time on the doubt axis
specifically, with caution and raw_refusal staying clean against their own
controls.

Two predictions were registered pre-sign, head to head: the orchestrator
called an early-exterior `eff_dim_frac` peak plus non-reproduction of the
J-lens interior peak in the profile (both correct: WIN); the user called an
interior `eff_dim_frac` peak following the J-lens band (the registered call
is falsified: LOSS), but the underlying interior intuition is independently
vindicated by the read panel, which does peak interior on top of the J-lens
band, so the miss is instrument attribution rather than signal location.
All three gates (AG0 capture/direction integrity, AG1 profile
reproducibility, AG2 read-panel CIs) passed. Source of truth:
`experiments/qwen3-4b-family-atlas/AMENDMENT.md` (Outcome section) and
`experiment.yaml`.
