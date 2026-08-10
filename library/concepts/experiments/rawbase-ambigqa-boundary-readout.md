---
title: rawbase-ambigqa-boundary-readout
aliases:
- Raw-base AmbigQA boundary readout
- pretraining-flavor vs training-warp fork
- raw Qwen3-4B base AmbigQA boundary probe
tags:
- kg/experiment
- experiment
- epistemic-humility
kg:
  id: experiment:rawbase-ambigqa-boundary-readout
  type: experiment
  status: canonical
related:
- '[[ood-breadth-beyond-selfaware]]'
- '[[known-unknown-direction]]'
- '[[answerability-subspace]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
- '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
relationships:
- type: builds_on
  target: '[[ood-breadth-beyond-selfaware]]'
  target_id: experiment:ood-breadth-beyond-selfaware
  confidence: high
  evidence:
  - "AMENDMENT.md Design (reuses the identical 2748-row AmbigQA internal panel,
    pool sha256 b0f93658...48bfd, and the pinned internal_panel_probe_gate.py
    protocol unchanged from item 26's G7)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "AMENDMENT.md Design (extraction at layer 35, anchor position, the same
    known-unknown-direction locus item 26 read)"
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: medium
  evidence:
  - "AMENDMENT.md Question (asks whether the pretrained representation carries a
    general answerability signal or a SelfAware-flavored one)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: medium
  evidence:
  - "AMENDMENT.md Reporting (feeds paper 3's Result 1 internal-axis claim as the
    scoping sentence for its pretraining-origin boundary)"
- type: supports
  target: '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
  target_id: mechanism:ambigqa-boundary-signal-is-pretraining-flavor-specific
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-09T23:30Z RESULT (heldout_probe_auroc 0.6338, prediction
    supported, falsifier not fired)"
- type: related_to
  target: '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
  target_id: mechanism:ambigqa-internal-readout-does-not-transfer-from-selfaware
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-09T23:30Z RESULT (resolves the fork item 26's G7 FAIL
    opened: flavor-specific pretraining origin, not a training-induced warp)"
---

Tier-3 exploratory probe-fit cell, single forward-only extraction plus a CPU
probe fit, no dose/steering/generation beyond one mechanical token. Asks the
fork the PI stated on 2026-08-09 after item 26
([[ood-breadth-beyond-selfaware]]) found the internal known-unknown readout,
near-perfect on SelfAware (0.997), reads the AmbigQA answerability boundary
at only 0.63 held-out on both trained panel checkpoints: is the pretrained
activation flavored to SelfAware-style unanswerability from the start
(flavor-specific), or did pretraining install a broader answerability signal
that post-training warped or narrowed (training-warp)? The measurement is the
identical AmbigQA internal panel and probe protocol run on the raw, untrained
`unsloth/Qwen3-4B` base (revision `64033659d5caf1b8ed7f929b29de705e93a4d468`,
no adapter, bf16).

Resolved 2026-08-09T23:30Z. **RG0, RG1, RG2 all PASS** (panel-pool sha match
and exact 2748/1245/1503 counts; extraction n_rows == n_answered == 2748;
pinned runtime image digest and provenance line present). **M1
heldout_probe_auroc = 0.6338** (5-fold std 0.0104, n=2748), within 0.006 of
both trained comparators fixed at signing (A1 0.6279, A4 0.6349).

Adjudicated against the pre-registered bands: 0.6338 <= 0.73, so the
**prediction is SUPPORTED** (flavor-specific reading) and the falsifier
(>=0.85, training-warp) **does not fire**. Detailed in
[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]. The raw pretrained
base sits at the same low level as the trained checkpoints on the AmbigQA
answerability boundary at this locus: post-training neither installed nor
destroyed AmbigQA boundary information, and item 26's G7 non-transfer is a
property of the pretrained representation rather than a training-induced
warp. This resolves item 26's open fork and directly scopes paper 3's
pretraining-origin framing for the internal known-unknown axis.

Source of truth: `experiments/rawbase-ambigqa-boundary-readout/AMENDMENT.md`,
`gates.yaml`, `experiment.yaml`, and `NOTEBOOK.md` (RESULT entry,
2026-08-09T23:30Z).
