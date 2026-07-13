---
title: j-space-layer-contrast-rep2-multisource
aliases:
- J-space layer contrast rep-2 (multi-source)
- ceiling-robust mid-band vs late-band replication
tags:
- kg/experiment
- experiment
- j-space
kg:
  id: experiment:j-space-layer-contrast-rep2-multisource
  type: experiment
  status: canonical
related:
- '[[j-space-mediated-actuation-fragility]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[j-space-midband-dose-calibration-qwen3-4b]]'
relationships:
- type: supports
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: high
  evidence:
  - experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md#outcome
  - experiments/j-space-layer-contrast-rep2-multisource/analysis-committed/full_summary.json
- type: builds_on
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: high
  evidence:
  - experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md (Motivation and posture)
- type: builds_on
  target: '[[j-space-midband-dose-calibration-qwen3-4b]]'
  target_id: experiment:j-space-midband-dose-calibration-qwen3-4b
  confidence: high
  evidence:
  - experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md (Design, frozen predecessor inputs)
---

Held-out raw-base Qwen3-4B bf16 second same-model replication of the
mid-band-vs-late-band J-space layer contrast, mining a fresh multi-source
confab pool (kuq_ku_unknown, kuq_ku_unknown_x, selfaware_unanswerable, with
per-source floors) so the late hs34 reference arm has real headroom, and
adding ceiling-robust paired gates (McNemar G1', a cost-per-win readout G2',
an interpretability-window G3'). Resolved FULL PASS on 2026-07-09: hs34
landed at 73.76% clean_tighten (inside the registered interpretability
window), the best mid-band arm (hs29) beat it by +19.0 percentage points with
42 late-only failures against 0 mid-only failures (exact McNemar p =
4.5e-13), and the known-correct cost delta stayed within the registered +2pp
bar at +1.43pp.

This traces an unmerged predecessor replication's G1 miss to a reference-arm
ceiling artifact from a single-source confab pool, not to an absence of the
mid-band effect: with the same frozen directions, thresholds, and doses, the
advantage reappears at near-predecessor magnitude (the original calibrated
contrast found +22.7pp) once the reference arm has real headroom. Source of
truth: `experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md`.
