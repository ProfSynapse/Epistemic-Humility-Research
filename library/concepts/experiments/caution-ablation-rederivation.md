---
title: caution-ablation-rederivation
aliases:
- Re-deriving the archived caution-ablation over-refusal collapse
- refusal-axis ablation provenance repair
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:caution-ablation-rederivation
  type: experiment
  status: canonical
related:
- '[[write-direction-naming-battery]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[ku-readout-coupling-actuates-selective-refusal-release]]'
- '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
- '[[directional-ablation]]'
relationships:
- type: builds_on
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - "experiments/caution-ablation-rederivation/AMENDMENT.md Motivation and posture (write-direction-naming-battery documents the figure's only sources are paper-3 prose and archived phase-1 intervention configs whose declared output paths no longer exist)"
- type: uses
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
  evidence:
  - "experiments/caution-ablation-rederivation/AMENDMENT.md Design (archived intervention pipeline re-run verbatim: erase the raw-theta / caution_perp direction from the L35 residual stream)"
- type: supports
  target: '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
  target_id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  confidence: high
  evidence:
  - "experiments/caution-ablation-rederivation/AMENDMENT.md#outcome (CA-G0 PASS all three configs; CA-G1 raw-theta reproduced, caution_perp not the 0.030 source; falsifier NOT fired)"
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: high
- type: related_to
  target: '[[ku-readout-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:ku-readout-coupling-actuates-selective-refusal-release
  confidence: high
---

Provenance-repair, exploratory tier-2 cell, resolved 2026-08-16, queued behind [[prompt-crossing-completion]]. [[write-direction-naming-battery]] found paper 3's cited known-item over-refusal collapse (0.994 to 0.030) un-re-derivable from its declared sources; the PI ruled paper 3 carries the governed [[ku-readout-coupling-actuates-selective-refusal-release]] numbers (0.994 to 0.524) and asked for the archived pipeline to be re-run so the 0.030 figure either regains a governed source or is formally retired.

Re-ran the archived phase-1 intervention pipeline byte-faithfully on the frozen legacy mech-interp machinery (no modernization), on `clean_sft_grpo_v2_seed1`, with direction files pinned by sha256 and configs verified unmodified against archive originals. The run stopped twice pre-GPU on archival path breaks (a renamed probe module, moved direction-file inputs); both were fixed by symlinks after verifying byte-identity to the archived-run-era files, with zero config or instrument-code bytes changed (see `NOTEBOOK.md`).

CA-G0 passed on all three configs (direction shas match the pins, full declared coverage, both baselines reproduce 0.994 within +/-0.02, lead-verified by independent recompute on every arm). Step-0 attribution, recorded before results existed, traced the archived 0.030 citation to the raw-theta variant, not caution_perp. Falsifier not fired: see [[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]].

**Why it matters here:** the 0.030 figure now has a governed, freshly generated source, and the standing 0.030-vs-0.524 tension in the KU-readout-coupling lineage resolves as variant identity, not drift or error.

**Scope:** this cell does not itself re-promote 0.030 into any paper. Paper 3 keeps the governed KU-readout-coupling numbers unless a further registered confirmatory step promotes the re-derived figure.

Source of truth: `experiments/caution-ablation-rederivation/AMENDMENT.md`, Outcome section, resolved 2026-08-16.
