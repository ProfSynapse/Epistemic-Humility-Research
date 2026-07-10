---
title: qwen35-4b-midband-doubt-snap
aliases:
- Qwen3.5-4B mid-band doubt-snap decoupling test
tags:
- kg/experiment
- experiment
- j-space
kg:
  id: experiment:qwen35-4b-midband-doubt-snap
  type: experiment
  status: draft
related:
- '[[j-space-mediated-actuation-fragility]]'
- '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
- '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[j-space-layer-contrast-rep2-multisource]]'
relationships:
- type: tests
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#prediction
- type: tests
  target: '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
  target_id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  confidence: medium
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#falsifier
- type: builds_on
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Stage B fit result table)
- type: supports
  target: '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
  target_id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/NOTEBOOK.md (2026-07-10 batch-size probe entry)
- type: builds_on
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Motivation and posture)
- type: builds_on
  target: '[[j-space-layer-contrast-rep2-multisource]]'
  target_id: experiment:j-space-layer-contrast-rep2-multisource
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Motivation and posture)
---

Registered, signed exploratory test of whether writing the doubt-gated
caution snap at a J-space workspace-band (mid-band) layer on
Qwen/Qwen3.5-4B (bf16, hybrid linear-attention architecture) decouples confab
refusal induction from output-format corruption, where the registered late
write site (0.94-depth, hs30) produced a well-characterized G0
dose-viability null in `doubt-snap-cross-family-confirmatory`. A local
J-lens profile localized a workspace-like effective-dimensionality band at
hs20/hs23/hs26 (peak at hs23), distinct from the late hs30 site, mirroring
the Qwen3-4B same-model mid-band-vs-late-band lesson
(`j-space-layer-contrast-rep2-multisource`, resolved FULL PASS). FIT-only
direction and gate fits are complete for all four candidate layers (hs20,
hs23, hs26, hs30), each clearing the registered minimum-AUC-0.90 gate.

As of this writing the experiment is signed and its Stage C per-layer dose
ladder is running as a background local RTX 3090 process (launched
2026-07-10, estimated 48-55 hours); no held-out or dose-ladder outcome exists
yet, and this note asserts none. It records one resolved pre-launch finding:
a batch-size probe found batch sizes 16 and 32 diverging from the validated
batch-8 reference on 61 of 240 row-by-field comparisons, including one
categorical flip on the primary gate metrics, confirming the same Qwen3.5
bf16 batch-composition non-determinism hazard seen on the Modal cross-family
cells; the full ladder runs at the validated batch_size=8. Source of truth:
`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` and `NOTEBOOK.md`,
currently only on the unmerged worktree
`/home/profsynapse/code/ehr-worktrees/qwen35-midband`.
