---
title: 'The Two-Signal Readout: A Training-Free Answerability-and-Correctness Mechanism for Epistemic Humility'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-twosignal
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: draft
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- qwen3-4b
metrics:
- auroc
related:
- '[[answerability-axis-present-without-task-training]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[linear-probe]]'
- '[[residual-stream]]'
- '[[auroc]]'
- '[[hallucination]]'
- '[[abstention]]'
provenance: 'Internal program paper (Paper 3, working). Evidence: experiments/probe-as-oracle-readout-ceiling/AMENDMENT.md, experiments/xdataset-probe-transfer/AMENDMENT.md, experiments/aux-head-trainable-readout/AMENDMENT.md, experiments/correctness-confidence-probe/AMENDMENT.md, experiments/correctness-readout-deployment-port/AMENDMENT.md, experiments/unified-two-signal-dial-veto/AMENDMENT.md, experiments/base-model-training-free-mechanism/AMENDMENT.md, the Stage 1.5 integration (PR #128), experiment/phase1/probe/amendment_*_result.json, and the synthesis papers/paper-4-two-signal-readout/notes/framework.md. Not an external publication.'
relationships:
- type: supports
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: high
- type: supports
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
- type: supports
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
- type: supports
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: high
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: studies
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: studies
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

## Summary

Internal program paper (Paper 3, working) for the Epistemic-Humility-Research
program. Where Paper 3 ([[internal-paper3--knows-but-doesnt-say]]) establishes the
representation-verbalization gap and proposes a confidence-head engine change, this
paper shows the route works and that its core signal is recoverable with no task
training: the internal state carries two orthogonal linearly-decodable axes -
answerability (read at the prompt anchor) and per-answer correctness (read
post-generation) - that compose into a deployable two-stage trust pipeline. Working
synthesis: `papers/paper-4-two-signal-readout/notes/framework.md`.

## Claims

- Evidence label: probe-as-oracle ceiling + through-engine replication. A linear
  readout of the internal axis drives a policy passing all behavior+calibration gates
  (Amendment O: margin +95pt, AUROC 0.997, ECE 0.015), and a head trained through the
  production aux_head engine reproduces the ceiling (Amendment Q: transfer 0.983).
- Evidence label: post-generation correctness readout. A linear probe at the
  post-generation content token ranks per-answer correctness at AUROC 0.834 (Amendment
  S, Instruct base) and 0.819 (Amendment T, deployed checkpoint); reading after the
  answer beats before by +0.065 (CI excludes 0).
- Evidence label: orthogonality / pipeline. The answerability and correctness scalars
  are orthogonal; fusing them degrades correctness ranking (delta -0.014, CI excludes
  0), so they deploy as a two-stage pipeline (Stage 1.5, PR #128).
- Evidence label: hallucination veto. The correctness dial assigns confident
  confabulation the lowest trust (Amendment U: AUROC 0.980; within-SelfAware control
  0.93 rules out dataset shift).
- Evidence label: training-free mechanism. On the raw instruct base with no
  abstention-SFT/RL, gate 0.997 + dial 0.834 + hallucination-veto 0.754 all hold
  (Amendment W); task training sharpens the veto (0.754 to 0.980) and adds ~0 to the
  gate - training amplifies, it does not create, the signal.
- Caveats: single-model (Qwen3-4B), single-seed (seed 1); "training-free" means no
  abstention-SFT/RL of ours (the base is upstream instruction-tuned); hallucination
  label is structural; the correctness reference is cross-dataset (within-SelfAware
  control bounds it). Promotion to a headline claim requires a pre-registered
  fresh-seed / 8B / held-out replication.
