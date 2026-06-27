---
title: 'Computed-confidence alignment regimen: SFT seeds structure, GRPO/DPO/KTO align internals'
kg:
  id: experiment:computed-confidence-alignment-regimen
  type: experiment
  status: canonical
tags:
  - kg/experiment
  - grpo
  - sft
  - calibration
  - reward-design
  - regimen
status: proposed
governance: exploratory
phase: phase1
lane: local
est_compute: 'dataset rebuild GPU-free (probe outputs already exist); each training arm ≈ one SFT or one GRPO seed at 4B'
relationships:
  - type: tests
    target: '[[gap-4-probe-transfer]]'
    target_id: gap:4-probe-transfer
    confidence: medium
  - type: builds_on
    target: '[[grpo-v3-proper-scoring-confidence]]'
    target_id: experiment:grpo-v3-proper-scoring-confidence
related:
  - '[[grpo-v3-proper-scoring-confidence]]'
  - '[[caution-vs-doubt-knowledge-gate]]'
---

## Question & Hypothesis

**Division of labor (user's framing, adopted).** SFT's job is to teach the
**output structure** (the `{answer, response_confidence}` schema) and the
**vocabulary of abstention** ("I don't know"). The *alignment* of the confidence
number to reality — internal AND external — is the job of the preference-stage
trainings (GRPO / DPO / KTO). The current mech-interp probe model
(`clean-sft-grpo-v2`) is therefore **fine to keep probing**: probing is about
reading the internal axes, not about whether the emitted number is honest.

**The gap this regimen attacks.** The current `clean-sft` projection assigns
confidence by a **deterministic per-role band** (appropriate → 0.8, inappropriate
→ 0.2, ambiguous → 0.4–0.6). Every appropriate answer is labelled with the *same*
0.8 regardless of question difficulty. That plants a **flat-0.8 prior** at the SFT
stage, and the v2 GRPO reward (fixed per-cell target) gave no pressure to leave
it → the observed **collapse** (emitted confidence std 0.015, ECE 0.142, AUROC
0.56; see [[caution-vs-doubt-knowledge-gate]]). So even though "alignment is
GRPO's job," SFT sets the *prior GRPO starts from*, and a flat prior is a
collapsed basin that a broken reward never leaves.

**What already exists (do not rebuild from scratch).** A **computed**-confidence
SFT projection is already implemented:
`build_schema_response_confidence_datasets.py` `probe-scaled` mode uses
`confidence = 0.1 + 0.8 · appropriateness_p`, where `appropriateness_p` is the
model's **own per-question correctness rate from 32 stochastic samples**, Laplace-
smoothed `(k+1)/(n+2)` (refusal rows use `1 − factual_p`). That *is* "actually
computed confidence values per question." It was built/tested in session 0018 but
the model we probe was trained on the **clean-band** projection, not this one.
**Prereq before any run:** confirm whether session-0018's probe-scaled projection
was ever taken end-to-end (SFT→GRPO) and evaluated for *emitted-confidence*
calibration (ECE / std / correct-vs-wrong AUROC). If yes, this regimen extends it;
if no (likely — 0018 focused on dataset construction + smoke), that end-to-end
calibration eval is the novel contribution.

**Hypothesis.** A regimen that (a) seeds SFT with **computed per-question
confidence** (probe-scaled) and (b) applies a **proper-scoring GRPO reward**
([[grpo-v3-proper-scoring-confidence]], v3) yields emitted confidence that is
**graded and calibrated** (std ≫ 0.015, ECE ↓, correct-vs-wrong AUROC ↑) without
degrading behavior — and, because the v3 reward's optimum is the true per-question
probability already encoded on the L35 doubt axis, it should **tighten
internal→output coherence** (emitted confidence tracks the doubt projection).

## Design — a 2×2 attribution matrix

Cross **SFT confidence source** × **alignment stage** so calibration is
attributable to the seed vs the reward, not confounded:

| Arm | SFT confidence | Alignment stage | Question it answers |
|-----|----------------|-----------------|---------------------|
| A0  | clean-band (flat 0.8) | — (SFT only) | baseline prior: how flat is SFT alone? |
| A1  | probe-scaled (computed) | — (SFT only) | can SFT *alone* teach graded confidence, or only structure? |
| B0  | clean-band | GRPO-v3 | can the v3 reward fix collapse *without* a computed seed? |
| B1  | probe-scaled | GRPO-v3 | full regimen: computed seed + proper-scoring reward |

`clean-sft-grpo-v2` is the historical reference cell (clean-band SFT + v2 reward).
A1 directly tests the user's "SFT only teaches structure" claim: if A1's emitted
confidence is already graded, SFT *can* carry calibration; if A1 stays flat-ish,
calibration genuinely requires the preference stage (supports the framing).

**DPO / KTO arms (optional, later).** The same computed-confidence dataset already
emits DPO/KTO projections. Worth adding `probe-scaled → DPO` and `probe-scaled →
KTO` once the GRPO arms show signal, to compare which alignment objective best
externalizes the internal signal. Keep these behind the GRPO result to avoid
spending compute on all objectives before knowing the seed matters.

## Prerequisites & Gating

- Verify/refresh the probe-scaled dataset: the 32-sample probe outputs must exist
  for the train split (they do for the probe pool; confirm coverage). Rebuild is
  GPU-free if probe JSONL is present.
- v3 reward is drafted + tested ([[grpo-v3-proper-scoring-confidence]]); B0/B1 use
  `target_mode="group"` by default (anchors to realized appropriateness; no extra
  forward pass). An `internal`-target science arm can come later.
- **Governance:** this is a NEW regimen, exploratory. It does NOT touch the
  PROTOCOL v0.3 locked headline matrix or the v2 reward. Any training run needs
  explicit user sign-off and a governed amendment with changelog. Drafting this
  launches nothing.

## Runbook

1. (prereq) Audit session 0018: was probe-scaled ever evaluated for emitted-
   confidence calibration end-to-end? Record yes/no + pointers.
2. Build/refresh probe-scaled SFT + GRPO datasets; assert per-question confidence
   spread is non-degenerate (std of labels ≫ 0 across difficulties).
3. (gated, sign-off) Train A1 (probe-scaled SFT only). Eval emitted-confidence
   std / ECE / correct-vs-wrong AUROC vs A0.
4. (gated, sign-off) Train B1 (probe-scaled SFT → GRPO-v3). Same eval + behavior
   (over-refusal, unknown-answer) vs `clean-sft-grpo-v2`.
5. Train B0 (clean SFT → GRPO-v3) to isolate the reward's standalone contribution.
6. Re-probe B1: does emitted confidence now track the L35 doubt-axis projection
   (internal→output coherence improved)? This closes the mech-interp → RL loop.

## Validation contract

- Dataset: per-question confidence labels are graded (not a 2–3 point comb);
  appropriate-answer label std ≫ 0; behavior preference signal unchanged vs the
  clean projection (same known/unknown ordering).
- Definition of done (per trained arm): emitted confidence std ≫ 0.015 AND ECE <
  v2's 0.142 AND correct-vs-wrong AUROC > v2's 0.56, with over-refusal and
  unknown-answer rates no worse than `clean-sft-grpo-v2`.
- Attribution: report the 2×2 so the calibration delta is assigned to seed (A1−A0)
  vs reward (B0−A0) vs both (B1−A0).
- Power: correct-vs-wrong eval needs more wrong-answered rows than the 16
  currently available (shared limitation with [[caution-vs-doubt-knowledge-gate]]).

## Outputs & provenance

Datasets via `build_schema_response_confidence_datasets.py` (existing builder).
Configs alongside the existing `sft_schema_probe_scaled_response_confidence_*`
family. Findings to `docs/sessions/0026 - caution-vs-doubt-knowledge-gate.md` and
here. Does not feed meta-analysis or alter PROTOCOL v0.3 cells without amendment.

## Variations

- `internal`-target GRPO arm (v3 `target_mode="internal"`): seed SFT with computed
  confidence, then align GRPO to the L35 doubt-axis probe estimate — literal
  internal-alignment; compare convergence vs the group (truth-anchored) target.
- Probe-scaled formula sweep (`0.1 + 0.8·p` vs identity vs temperature-scaled p).
- Larger n_samples for the probe (32 → 64) to tighten the per-question target.

## Status log

- 2026-06-27: created (proposed). Motivated by the calibration-gap finding and the
  v3 reward draft. Key realization: a *computed* confidence SFT projection already
  exists (probe-scaled, session 0018) but the probed model used the flat clean-band
  projection — so the novel work is the end-to-end calibration-evaluated regimen
  (2×2 seed×reward), not building a dataset from scratch. Design only; awaiting
  sign-off and the session-0018 audit before any run.
