---
title: jspace-family-atlas
aliases:
- cross-family workspace-band layer atlas
- Llama/Mistral J-space family atlas
tags:
- kg/experiment
- experiment
- j-space
- cross-family
kg:
  id: experiment:jspace-family-atlas
  type: experiment
  status: canonical
related:
- '[[j-space-mediated-actuation-fragility]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[refused-vs-known-contrast-carries-norm-position-confound]]'
relationships:
- type: tests
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#prediction
  - experiments/jspace-family-atlas/AMENDMENT.md#falsifier
- type: builds_on
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md (Motivation and posture)
  - experiments/jspace-family-atlas/NOTEBOOK.md (2026-07-12 instrument-build entry, anchor-position parity with prep_tuner_cell.py)
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/jspace-family-atlas/NOTEBOOK.md (2026-07-12 instrument-build entry, eff_dim_frac estimator ported from jlens_qwen35.py)
- type: supports
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: low
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome
- type: supports
  target: '[[refused-vs-known-contrast-carries-norm-position-confound]]'
  target_id: mechanism:refused-vs-known-contrast-carries-norm-position-confound
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome (random_direction_control.json diagnostic)
---

Read-only, capture-only mapping experiment on two non-Qwen instruction-tuned
families (`unsloth/Llama-3.2-3B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`,
reusing the `doubt-snap-cross-family-confirmatory` fleet's row pools and
splits verbatim). It computed a per-layer effective-dimension-fraction
(`eff_dim_frac`, a representation-variance participation-ratio profile) and a
per-layer held-out AUROC read panel for three axes (doubt, caution, raw
refusal), to test whether an interior workspace-like band predicts where the
doubt-snap fleet's ported single depth fraction should have been placed per
family.

Both predictions (orchestrator and user, both registered pre-launch as
holds-on-both) failed: the `eff_dim_frac` profile peaks early-exterior rather
than interior in both families (llama layer 4 of 28, 0.14 depth; mistral
layer 3 of 32, 0.09 depth), a shape neither the registered prediction nor its
falsifier named. The falsifier was not triggered either, since an interior
band where all three axes clear 0.80 held-out AUROC does exist in both
families: llama layers 15-23 (best simultaneous three-axis read ~L20-23),
mistral layers 7-27 (best ~L15-17). All three gates (AG0 capture/refit
integrity, AG1 profile reproducibility, AG2 read-panel CIs) passed, and the
lead independently re-derived the full profile, refits, and subsample peak
locally from the pulled captures.

The atlas delivers a layer map for future per-family actuation design (llama
~L20-23, mistral ~L15-17) and two findings that outlive this one run: the
readable band and the profile peak sit at different depths per family rather
than a shared portable fraction
([[workspace-band-peak-location-is-family-relative]]), and the doubt axis's
apparent separability at this anchor is partly a norm/position artifact
rather than doubt-specific
([[refused-vs-known-contrast-carries-norm-position-confound]]). Source of
truth: `experiments/jspace-family-atlas/AMENDMENT.md` and `NOTEBOOK.md`.
