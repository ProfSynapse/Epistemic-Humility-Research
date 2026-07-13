---
title: 'Held-Out Propensity Reading Gate Is Inconclusive by Power on the AI-TRUE Checkpoint (Amendment H9)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-h9-reading-gate-inconclusive-by-power
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
fulltext: ../../experiments/h9-propensity-reading-gate/AMENDMENT.md
provenance: 'Internal amendment (Tier-2 probe-fit). Source of truth: experiments/h9-propensity-reading-gate/AMENDMENT.md section 10 (outcome resolved 2026-07-11); experiment.yaml records status: resolved, registered: true. Checkpoint: the Amendment AI TRUE-mapping probe-as-reward GRPO model (clean-SFT-merged Qwen3-4B base plus GRPO-TRUE LoRA adapter, section 2). Surface: a stratified held-out draw disjoint from AL''s 1,662-row fit surface, drawn from the 16,834-row AH-pool complement (500 rows, then the single registered +250 enlargement to 750), scored by a frozen scorer that re-derives AL''s exact fit recipe (L24 PCA-128 seed 20260705, caution-residualized mean-diff, z-scale).'
related:
- '[[confabulation-propensity-direction]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[internal-al-injection-null--true-checkpoint]]'
- '[[internal-ai-probe-as-reward-null--true-vs-permuted]]'
- '[[internal-bb-base-propensity-fit-read--qwen3-4b-base]]'
relationships:
- type: studies
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
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
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: medium
- type: related_to
  target: '[[internal-al-injection-null--true-checkpoint]]'
  target_id: paper:internal-al-injection-null
  confidence: high
- type: related_to
  target: '[[internal-ai-probe-as-reward-null--true-vs-permuted]]'
  target_id: paper:internal-ai-probe-as-reward-null
  confidence: medium
- type: related_to
  target: '[[internal-bb-base-propensity-fit-read--qwen3-4b-base]]'
  target_id: paper:internal-bb-base-propensity-fit-read
  confidence: high
---

## Summary

Amendment H9 supplies the missing held-out number for the "reads" half of Paper
5's two-part claim about the confabulation-propensity direction on the AI-TRUE
checkpoint (the actuation half was already resolved as a use-the-signal null by
Amendment AL, [[internal-al-injection-null--true-checkpoint]]). It freezes a
scorer that re-derives AL's exact fit recipe, draws a stratified held-out row
population AL's fit never saw, and scores the frozen direction on it. The result
is **INCONCLUSIVE-BY-POWER**, not a pass or a fail: the evaluability
precondition (H9-G0, at least 20 confabulations and 20 honest unanswerable
refusals) was never met, on either the original 500-row draw or the one
registered +250 enlargement to 750 rows, so the reading gate (H9-G1) was never
adjudicated per the pre-registered read-once rule. The starvation is a real
behavioral fact, not a pipeline defect: the caution positive control passed both
reads at AUROC 0.97+, and the AI-TRUE checkpoint turns out to refuse 99.3% of
held-out unanswerable rows, far above the ~91% the fit-surface rate predicted.
The propensity direction's held-out reading claim on this checkpoint therefore
remains untested at adequate power. This pairs with
[[internal-bb-base-propensity-fit-read--qwen3-4b-base]] as the trained-checkpoint
half of a before/after-training bookend: BB reuses this experiment's exact
750-row read draw on the untrained base model, where the positive cell that
starved here has ample mass.

## Claims

- Evidence label: pre-registered evaluability precondition (H9-G0). NOT MET
  twice: the original 500-row stratified draw yielded 4 confabulations against
  the >=20 floor (399 honest unanswerable refusals; ~35 confabs were expected
  from fit-surface rates). The single registered +250 enlargement (RNG-stream
  continuation verified by a replay assertion against the committed manifest)
  added zero further confabulations: 4 confabs in 605 unanswerable rows (601
  honest refusals) on the full 750-row draw. Per the pre-registered rule, no
  further enlargement or re-draw is permitted, so the result stands.
  (`experiments/h9-propensity-reading-gate/AMENDMENT.md` section 10.)
- Evidence label: held-out propensity reading gate (H9-G1). NOT READ (AUROC
  null, CI null) — the pre-registered inconclusive-by-power outcome, not a pass
  and not a falsification, following directly from the H9-G0 miss.
- Evidence label: pre-registered caution positive control (H9-G2, floor >=0.90).
  PASS on both reads: AUROC 0.9734 on the 500-row draw, 0.9702 on the 750-row
  enlarged draw. The extraction, frozen-scorer, and grading pipeline is healthy;
  the confab scarcity is real model behavior, not an instrumentation failure.
- Evidence label: scorer-fidelity gates (pre-registered, CPU-only). FID-1
  (exact-replication of AL's on-disk `d_raw.npy`) cosine 1.0, max absolute
  elementwise difference 3.57e-9. FID-2 (OOF consistency) Pearson r=1.0, AUROC
  0.68016, within 0.02 of AL's recorded in-cell 0.6802.
- Evidence label: registered near-duplicate sensitivity sweep (KUQ paraphrase
  overlap, threshold 0.90). 0 rows flagged on both draws, max token overlap
  0.75; no verdict flip.
- Evidence label: behavioral observation (non-gating, for the record). The
  AI-TRUE checkpoint is far more refusal-prone on this held-out complement than
  fit-surface rates predicted: 99.3% honest refusal on unanswerable rows (vs
  ~91% expected) and refusal on 30 of 97 answerable rows. The 4 confabulations
  observed are genuine confident fabrications, stated confidence 0.71-0.82.
- Caveats: single checkpoint, single seed. An inconclusive-by-power result is
  reported as such, per the pre-registered no-goalpost-moves rule; it licenses
  no reading claim, pass or fail, for the propensity direction on this
  checkpoint. Exploratory lab-notebook evidence, never pooled with the locked
  headline matrix.
