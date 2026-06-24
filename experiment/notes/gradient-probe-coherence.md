---
title: 'Gradient probes as an L-gradient coherence layer'
kg:
  id: experiment:gradient-probe-coherence
  type: experiment
  status: canonical
tags:
- kg/experiment
status: proposed
governance: exploratory
phase: phase3
lane: local
est_compute: '~6-10 GPU-hours on one RTX 3090 for E1/E2/E4; E3 reuses Phase-1 checkpoints'
relationships:
- type: tests
  target: '[[gap-4-probe-transfer]]'
  target_id: gap:4-probe-transfer
  confidence: high
- type: builds_on
  target: '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
  target_id: paper:2606.24790
  confidence: high
- type: builds_on
  target: '[[gradient-structure-encodes-output-correctness]]'
  target_id: mechanism:gradient-structure-encodes-output-correctness
  confidence: high
- type: builds_on
  target: '[[final-layers-concentrate-discriminative-gradient-signal]]'
  target_id: mechanism:final-layers-concentrate-discriminative-gradient-signal
  confidence: medium
related:
- '[[gap-4-probe-transfer]]'
- '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
- '[[grad-detect]]'
- '[[gradient-structure-encodes-output-correctness]]'
- '[[final-layers-concentrate-discriminative-gradient-signal]]'
---

## Question & Hypothesis

Does a gradient-based probe (Grad Detect) add a usable, truth-tracking signal to
the coherent-humility stack, and does that signal survive humility fine-tuning?

The coherent-humility frame (`experiment/protocol/RESEARCH-DIRECTIONS.md`)
measures L-token, L-hidden, and L-stated on the same model and asks whether they
agree. Grad Detect proposes a fourth modality, L-gradient: a per-layer gradient
read of "is this output wrong / should I abstain," from a single forward-backward
pass.

- **Hypothesis.** The gradient probe discriminates correct from incorrect answers
  at least as well as an activation probe and better than output baselines, and a
  base-trained gradient probe still transfers to humility-tuned checkpoints.
- **Falsifier.** The gradient probe's discrimination collapses within a
  knowledge-popularity stratum (it reads recall, not truth), or it fails to
  transfer to tuned models while the activation probe does.

## Design

Shared setup for all variations:

- **Model.** One repo-native small model (Qwen2.5-1.5B or Gemma-2-2B); match the
  Phase-1 base for E3.
- **Data.** TriviaQA, SciQ, PopQA, TruthfulQA; generate answers at temperature 0,
  label correctness. The same outputs feed every detector so comparisons are on
  equal footing.
- **Detectors compared.** (a) gradient features (Grad Detect), (b) hidden-state
  linear probe, (c) p(True), (d) verbalized confidence / semantic entropy.
- **Metric panel.** AUROC and AUPRC for error detection and abstention
  prediction, plus per-layer AUROC for localization. Recall controls and diverse
  probe-training data are mandatory (the Gap-4 cautions).

This is an `exploratory` note: it is not part of PROTOCOL v0.3 and produces no
headline results. If any arm graduates to a signed experiment it goes through the
`amendment-governance.md` 7-point rule first.

## Prerequisites & Gating

- GPU available (single RTX 3090 is enough; one forward-backward pass per item on
  a <=3B model). E1/E2/E4 need no training.
- Base-model weights and the four datasets staged locally.
- E3 additionally requires the Phase-1 SFT/DPO/KTO checkpoints to exist.
- Probes stay held-out evaluation and never enter a reward loop.
- Read `experiment/protocol/PHASE3-control-system-protocol.md` before building.

## Runbook

1. Setup: confirm GPU and stage datasets; pin the base model.
2. Generate + label: produce temperature-0 answers over the four datasets and
   correctness labels (the shared evaluation set).
3. Activation baseline: run the existing hidden-state probe via
   `experiment/phase1/probe/hidden_state_linear_probe.py` (scored with
   `experiment/phase1/probe/scoring.py`).
4. Gradient probe: implement a gradient-feature extractor as a sibling of the
   hidden-state extractor (per-layer gradient statistic from one backward pass);
   lift the exact recipe from the Grad Detect paper appendix
   (`library/fulltext/2606.24790.html`) before building.
5. Score all detectors on the same splits; emit the metric panel.
6. Document: write a run record and a `docs/sessions/` checkpoint; update the
   Status log below.

Bake in approval gates for any cost-incurring or destructive action. Do not add
experiment-specific code to the `synaptic-tuner` submodule.

## Validation contract

- **Pre-run.** The four datasets resolve; the base model loads; for E3 the
  Phase-1 checkpoints referenced exist.
- **Post-run.** Each detector has an AUROC/AUPRC row on every dataset; per-layer
  curves exist for E4; a run record and session checkpoint are written.
- **Definition of done.** E1 reports the four-detector comparison; E2 reports
  within-stratum AUROC (the recall-contamination index); E4 reports the layer
  profile; E3 (when checkpoints exist) reports probe-transfer AUROC base->tuned
  per method arm and the coherence delta.

## Outputs & provenance

- Run records: `experiment/phase1/run_records/` (or a Phase-3 sibling).
- Episodic log: `docs/sessions/` checkpoints via the experiment-runner helper.
- Meta-analysis: results are detection-quality, not training-effect sizes, so
  they do NOT enter `meta-analysis/evidence/effects.csv`; they inform Gap 4 /
  Phase 3 discussion (the paper is logged as a v1 candidate in
  `meta-analysis/evidence/prisma-flow.md`).

## Variations

- **E1 - Controlled modality bake-off (foundation).** Gradient vs activation vs
  output detectors on equal footing. Establishes the L-gradient baseline.
- **E2 - Truth vs recall (novel hook).** Stratify by PopQA entity popularity;
  test whether each detector still discriminates correct/incorrect within a
  stratum. A drop from pooled to within-stratum AUROC is the recall-contamination
  index. Adds TruthfulQA adversarial items as a second dissociation.
- **E3 - Probe transfer across humility training (deepest integration).** Fit on
  the base model, re-read on each Phase-1 SFT/DPO/KTO checkpoint; report transfer,
  per-layer localization, and the coherence delta. Gated on Phase-1 checkpoints.
- **E4 - Layer-localization replication (byproduct).** Per-layer ablation of the
  gradient features; overlay the activation-probe per-layer profile. Checks the
  paper's last-5-layers / >97% claim on our models.

Sequencing: E1 + E4 together, then E2 on the same outputs; E3 waits on Phase-1
checkpoints.

## Status log

- 2026-06-24: created (proposed). Migrated from the session's exploratory draft;
  the design originates with the Grad Detect ingest.
