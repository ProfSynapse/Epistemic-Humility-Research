---
title: 'Caution Assembly Timeline: SFT Rotates the Answerability Readout Once and RL Rides It (diagnostics item 9)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-diag-item9
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: lab-notebook
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- qwen3-4b
metrics:
- auroc
provenance: 'Internal lab-notebook diagnostics (item 9). Script experiment/phase1/probe/diag_item9_caution_timeline.py (commit a354ad73); extraction at repo commit d5a90b3b; data staging professorsynapse/eh-al-prep-staging tags diag-item9-{raw,cleansft,grpov2,partrue}-r3. Forward-only L0..L36 over the 1,662-row A0 pool (324 known / 1,338 unknown); probe = PCA-128 shared basis plus saga logistic, 5-fold OOF, seed 20260705. Analysis artifact experiment/phase1/probe/analysis/diag_item9/. Ungated exploratory evidence, never pooled with the locked headline matrix.'
related:
- '[[sft-rotates-boundary-readout-rl-rides-it]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[answerability-probe-transfers-across-qa-datasets]]'
- '[[internal-twosignal-readout--training-free]]'
- '[[known-unknown-direction]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[unanswerable-questions]]'
relationships:
- type: supports
  target: '[[sft-rotates-boundary-readout-rl-rides-it]]'
  target_id: mechanism:sft-rotates-boundary-readout-rl-rides-it
  confidence: high
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: high
- type: related_to
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: high
- type: related_to
  target: '[[answerability-probe-transfers-across-qa-datasets]]'
  target_id: mechanism:answerability-probe-transfers-across-qa-datasets
  confidence: medium
- type: related_to
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

## Summary

Internal lab-notebook diagnostics (item 9) asking when across training the answerability
(known-vs-unknown) readout is assembled and how its direction moves. A forward-only
extraction over the 1,662-row A0 pool at four training stages (raw base, clean-SFT,
GRPO-v2, GRPO-par-true) is probed in a shared PCA-128 basis so directions are comparable
across stages. The finding: the readout is already present at full strength in the raw
base and no stage sharpens it; SFT rotates the direction once to a near-orthogonal
orientation without improving separability, and both GRPO variants ride the
SFT-installed direction with negligible further rotation. This mechanizes the known
refit-per-checkpoint drift and the low caution-direction cosine seen elsewhere in the
program: the rotation is a one-time SFT event, not gradual. Label caveat: the pool label
is answerability (known/unknown), not answered-versus-refused behavior, because the
capture is forward-only.

## Claims

- Evidence label: shared-basis CV AUROC across four training stages (5-fold OOF, seed
  20260705). Mid-to-late (L20-L36) mean AUROC is highest in the raw base (0.951) and no
  training stage improves it: clean-SFT 0.922, GRPO-v2 0.923, GRPO-par-true 0.926. The
  answerability readout is present at full strength before any of our task training and
  is slightly reduced, never sharpened, by it (script diag_item9_caution_timeline.py,
  commit a354ad73; staging diag-item9-*-r3; extraction commit d5a90b3b).
- Evidence label: direction rotation cosine in the shared PCA-128 basis. The raw base to
  clean-SFT rotation is near-orthogonal across mid and late layers (cosine 0.06-0.25,
  e.g. L14 0.062, L20 0.094, L28 0.226, L35 0.196), whereas clean-SFT to GRPO-v2 is
  near-identity (0.91-0.997) and GRPO-v2 to GRPO-par-true stays high with a late-layer
  drift (0.74-0.99, 0.736 at L35). The reorientation is a single SFT event that RL then
  rides (supports [[sft-rotates-boundary-readout-rl-rides-it]]).
- Caveats: single model (Qwen3-4B), single seed; forward-only capture so the label is
  pool answerability, not answered-versus-refused behavior; cross-family cosine against
  the Qwen3.5-4B gate axis is a heuristic and reads near zero at every layer. Exploratory
  lab-notebook evidence, reported separately from and never pooled with the locked
  headline matrix.
