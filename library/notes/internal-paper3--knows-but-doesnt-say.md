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
fulltext: ../../papers/paper-3-knows-but-doesnt-say/manuscript.md
provenance: 'Internal program paper (Paper 3 in the five-paper map, 2026-07-01; the "paper3" node slug is again accurate). Source of truth: papers/paper-3-knows-but-doesnt-say/manuscript.md. Evidence: experiments/contrastive-sft-behavior-conditional-confidence/AMENDMENT.md, experiments/answer-subspan-masked-contrastive-sft/AMENDMENT.md, experiments/quantile-balanced-probe-distilled-sft/AMENDMENT.md, experiments/grpo-v3-on-contrastive-sft-base/AMENDMENT.md, and archive/experiment/phase1 probe/eval analyses. Not an external publication.'
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
- '[[ood-breadth-beyond-selfaware]]'
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
- '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
- '[[pretrain-only-base-readout]]'
- '[[knowledge-boundary-gate-and-veto-predate-post-training]]'
- '[[flavor-atlas-rawbase]]'
- '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
- '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
- '[[caution-install-bounded-site-sweep]]'
- '[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]'
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
  target: '[[ood-breadth-beyond-selfaware]]'
  target_id: experiment:ood-breadth-beyond-selfaware
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/AMENDMENT.md (resolves paper-3
    limitations-burn-down item 26, manuscript lines 1027-1029; re-tests
    Result 1's SelfAware-only internal-vs-stated headline gap on KUQ,
    AmbigQA, and BIG-bench known-unknowns)"
- type: related_to
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: medium
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/AMENDMENT.md Reporting
    (feeds the pretraining-origin scoping sentence for Result 1's internal
    answerability axis)"
- type: related_to
  target: '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
  target_id: mechanism:ambigqa-internal-readout-does-not-transfer-from-selfaware
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/NOTEBOOK.md 2026-08-09T16:45Z
    Stage 8 (G7 FAIL: Result 1's near-perfect SelfAware internal readout,
    0.997, reads AmbigQA's boundary at only 0.63 held-out)"
- type: related_to
  target: '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
  target_id: mechanism:ambigqa-boundary-signal-is-pretraining-flavor-specific
  confidence: medium
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/NOTEBOOK.md 2026-08-09T23:30Z
    RESULT (the raw pretrained base reads AmbigQA at the same low level as
    the trained checkpoints, scoping Result 1's axis as pretraining-installed
    and SelfAware-flavored)"
- type: related_to
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: related_to
  target: '[[pretrain-only-base-readout]]'
  target_id: experiment:pretrain-only-base-readout
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md line 1325
    provenance table (Section 4 pretraining-origin test, four
    pretrain-only bases at 0.997+; Section 8 origin claim downgraded to
    open question at registration, answered here SUPPORTED 4/4)"
- type: related_to
  target: '[[knowledge-boundary-gate-and-veto-predate-post-training]]'
  target_id: mechanism:knowledge-boundary-gate-and-veto-predate-post-training
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md line 1325
    provenance table (Section 4's pretraining-origin test)"
- type: related_to
  target: '[[flavor-atlas-rawbase]]'
  target_id: experiment:flavor-atlas-rawbase
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 1056-1094,
    Section 8 'Where the internal readout fails: covert ambiguity' (cites
    experiments/flavor-atlas-rawbase/AMENDMENT.md directly for the M1/M4
    numbers)"
- type: related_to
  target: '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
  target_id: mechanism:pretrained-base-carries-broad-overt-unanswerability-code
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 1065-1069
    (six KUQ flavors separate at 0.98 to 0.999 with free cross-transfer)"
- type: related_to
  target: '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
  target_id: mechanism:overt-vs-covert-unanswerability-is-the-boundary-not-flavor
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 1070-1075
    ('The dividing line is therefore not flavor but overt versus covert')"
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
- type: related_to
  target: '[[caution-install-bounded-site-sweep]]'
  target_id: experiment:caution-install-bounded-site-sweep
  confidence: high
  evidence:
  - "experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome
    (falsifier does not fire; on a silent falsifier, the section 9
    single-site/few-layer caveat is replaced by a statement naming the
    searched space per the amendment's own registered rule)"
- type: related_to
  target: '[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]'
  target_id: mechanism:caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b
  confidence: medium
  evidence:
  - "experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome
    (Gate results, resolved 2026-08-13; G1 actuation clears broadly while
    G3 specificity and G2 selectivity remain unresolved)"
---

## Summary

Internal program paper (Paper 3) for the Epistemic-Humility-Research program. It
separates *performing* humility from *possessing* it in Qwen3-4B by reading three
signals on the same questions - an internal confidence axis (linear probe on hidden
states), the stated confidence the model verbalizes, and the answer/abstain behavior
- and shows the internal axis is calibrated while the stated channel is decoupled and
training-resistant. Canonical text: `papers/paper-3-knows-but-doesnt-say/manuscript.md`.

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
