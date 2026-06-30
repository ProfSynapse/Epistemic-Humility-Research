---
title: 'Knows but Doesn''t Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-paper3
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
- expected-calibration-error
fulltext: ../../experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md
provenance: 'Internal program paper (Paper 3). Source of truth: experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md. Evidence: experiment/protocol/AMENDMENT-{K,L,M,N}-*.md and experiment/phase1 probe/eval analyses. Not an external publication.'
related:
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[internal-twosignal-readout--training-free]]'
- '[[linear-probe]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[abstention]]'
- '[[hallucination]]'
relationships:
- type: supports
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: high
- type: supports
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: high
- type: related_to
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: measures
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: studies
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: studies
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: studies
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

## Summary

Internal program paper (Paper 3) for the Epistemic-Humility-Research program. It
separates *performing* humility from *possessing* it in Qwen3-4B by reading three
signals on the same questions - an internal confidence axis (linear probe on hidden
states), the stated confidence the model verbalizes, and the answer/abstain behavior
- and shows the internal axis is calibrated while the stated channel is decoupled and
training-resistant. Canonical text: `experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md`.

## Claims

- Evidence label: within-model population read (n=3369). The internal answerability
  axis separates known from unknown at AUROC 0.997 with a 1-D readout ECE 0.004, while
  the stated confidence ranks appropriateness at 0.52-0.56 and is near-constant - the
  model represents what it does not know and does not report it (Result 1).
- Evidence label: held-out probe geometry. The internal signal is two correlated but
  separable axes - a graded doubt axis and a separable caution gate (caution-specific
  refuse/answer AUROC 0.825 after orthogonalizing out doubt); raw cosine -0.83
  overstates collinearity (Result 2).
- Evidence label: causal steering. Ablating the caution residual cuts over-refusal on
  known questions 0.994 to 0.030 with clean specificity, but no intervention installs
  abstention on true unknowns - asymmetric controllability (Result 3).
- Evidence label: training-intervention panel + dissociation. The stated-confidence
  gap survives DPO, KTO, GRPO v1/v2/v3, and contrastive SFT; a clean answer-supervised
  vs answer-masked contrastive-SFT dissociation localizes the calibration signal to the
  supervised wrong-answer text, and Amendments N/M show two opposite repairs failing on
  the same emission channel (Result 4).
