---
amendment: X
slug: cross-model-size-sweep
question: >-
  Does the training-free two-signal readout generalize across model
  scale (Qwen3 1.7B-14B), or is it a 4B artifact?
predictions:
  orchestrator:
    call: PASS at every size; veto plausibly sharpens with scale
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  COMPLETE — all four sizes PASS all three gates (size-robust); scaling of
  sharpness is non-monotonic (peaks at 8B), monotonic-sharpening expectation
  not supported.
scoreboard: null
---

# Amendment X — Cross-Size Generalization of the Training-Free Two-Signal Readout

**Status:** COMPLETE (2026-06-30) — gates §4 LOCKED; all four sizes (1.7B/4B/8B/14B)
PASS all three gates. VERDICT: the training-free two-signal readout is size-robust
across an order of magnitude; scaling of sharpness is non-monotonic (peaks at 8B),
descriptive only — no goalpost moved. Tier-2 exploratory cell (new evidence, falsifier
pre-stated; reported separately from the locked PROTOCOL v0.3 matrix). See §7 roll-up.

**Instrument rationale:** Tier-2 Amendment per
`experiment-runner/reference/amendment-vs-lab-notebook.md`. New evidence surface
(additional models), reported separately from the headline matrix. This is the
generalization axis for the [[AMENDMENT-W]] training-free finding: the question is
not "does the *trained* readout survive training seeds" (we are deliberately
de-emphasizing training) but "is the training-free readout a property of
instruction-tuned LMs, or a Qwen3-4B artifact?" Replicating across model *scale*
is the controlled first cut at that question.

**Compute:** GPU — one mixed-pool generation + dual-position extraction pass per
model on the RAW instruct base (no adapter). No training run. Launch requires
explicit user approval per operator discipline.

**Models (raw instruct bases, `unsloth/*-bnb-4bit`, NO adapter):** Qwen3-1.7B,
Qwen3-8B, Qwen3-14B. Qwen3-4B is already done (Amendments S + W). One family, four
sizes (1.7B / 4B / 8B / 14B) — a controlled size axis.

**Scope note (honest limitation):** this sweeps SIZE within ONE family. It does NOT
test cross-family generalization (Llama, Mistral, etc.); a Qwen-wide replication
leaves open that the mechanism is a Qwen-lineage property. Cross-family is named as
the next generalization axis and a §5 limitation, not claimed here.

## 1. Facts this builds on

- The two-signal readout (answerability gate + post-gen correctness dial +
  hallucination veto) is recoverable on the RAW Qwen3-4B instruct base with no task
  training: gate 0.997, dial 0.834, veto 0.754 ([[amendment-w-base-model-training-free]]).
- The dial reads per-answer correctness post-generation ([[amendment-s-correctness-readout-success]])
  and the gate reads answerability at the prompt anchor; the two axes are orthogonal
  ([[two-signal-pipeline-not-fused]]).
- All of this is single-model (Qwen3-4B), single-seed. The open question every prior
  amendment flagged: is it just this model?

## 2. Hypothesis and prediction

**H_X (the training-free readout generalizes across model scale).** On each raw Qwen3
instruct base (1.7B/8B/14B), with no adapter and no task training, a linear probe
recovers (a) an answerability gate at the prompt anchor, (b) a post-generation
correctness dial, and (c) a hallucination veto (correct ranked above confident
confabulation).

Per model:
- **X-G3 (veto — PRIMARY):** AUROC(correct vs hallucination), the model's own
  post-gen dial fit on its correct/wrong answers, ≥ **0.65**, CI excludes 0.50.
- **X-G1 (gate):** AUROC(known vs unknown) at the prompt anchor ≥ **0.65**, CI
  excludes 0.50.
- **X-G2 (dial):** AUROC(correct vs wrong) post-gen ≥ **0.65**, CI excludes 0.50.

**Predicted direction:** PASS at every size, with the gate near-ceiling throughout
and the veto plausibly sharpening with scale (descriptive, not gated).

If H_X holds, the readout is a scale-general property of the Qwen3 instruct family,
not a 4B artifact — a much stronger basis for the training-free headline. If it fails
at some size, that bounds the claim (e.g. "emerges above N parameters") — a
publishable scale-dependence finding.

## 3. Method (GPU extraction + CPU score), per model

**Checkpoint load.** RAW `unsloth/Qwen3-<size>-bnb-4bit`, NO adapter. Thinking off.
**Amendment S's answer-encouraging system prompt VERBATIM** (so the base answers a lot
and a wrong/hallucination class exists; identical surface to S/W on 4B).

**Pool.** ONE mixed pool per model (reuses the Amendment V builder): PopQA + TriviaQA
answerable (graded correct/wrong vs gold aliases) + SelfAware-unknown (unanswerable;
hallucination if answered). One generation pass yields all three outcome classes plus
the known/unknown gate labels — no separate runs.

**Procedure (reuses S grading + V mixed pool + W raw-base load):**
1. Greedy generation per question; classify answered/refused.
2. Grade: answerable ∧ answered → correct/wrong; unanswerable ∧ answered → hallucination.
3. Dual-position extraction on answered rows (pre-gen anchor + post-gen content token,
   all layers, fp32).
4. Score (CPU), per model: fit the correctness dial on THIS model's correct/wrong
   (OOF for the honest reference, full-fit applied to its hallucinations); sweep layers
   for the best gate (known vs unknown, pre-gen) and best dial (correct vs wrong,
   post-gen); report X-G1/G2/G3 + the within-SelfAware control + the scaling trend.

**Caveats.** Single-seed per model; greedy decode (one trajectory); structural,
ungraded hallucination label (unknown ∧ answered); correctness reference is
cross-dataset (PopQA/TriviaQA vs SelfAware) with the within-SelfAware control
reported to bound dataset shift — identical caveats to W. Best layer is chosen per
model from its own surface (reported, not cherry-picked across a gate set).

## 4. Gates and falsifier (LOCKED at sign-off)

**Data-adequacy precondition (per model, BEFORE scoring; not a result).** ≥ **30
wrong** AND ≥ **50 hallucinations**. Raw bases are pre-abstention and answer freely,
so this is expected to clear; below floor on a model is a DATA-STAGE stop for that
model, not a probe verdict.

**Metrics (threshold-free, per model):**
- **X-G3 — PRIMARY:** AUROC(correct vs hallucination) ≥ **0.65**, CI excludes 0.50.
- **X-G1:** AUROC(known vs unknown) ≥ **0.65**, CI excludes 0.50.
- **X-G2:** AUROC(correct vs wrong) ≥ **0.65**, CI excludes 0.50.
- **Descriptive (NOT gated):** per-size scaling trend of gate/dial/veto; 3-way
  dial-score distribution; within-SelfAware control AUROC(known-answered vs halluc).

**SUCCESS — the readout is scale-general (within Qwen3):** X-G1 AND X-G2 AND X-G3
pass on ALL THREE new sizes.

**PARTIAL — scale-dependent:** the gates pass on some sizes but not all; report the
threshold (e.g. "veto emerges ≥ N params") as a scale-dependence finding, no goalpost
moved.

**FALSIFIER — the mechanism is 4B-specific:** X-G3 < 0.65 AND its CI includes 0.50 on
the MAJORITY of new sizes (≥2 of 3) — the training-free readout does not generalize
across scale. Report as a negative bounding the claim to ~4B.

**No goalpost-moving.** Thresholds fixed at sign-off; descriptive scaling numbers do
not move the per-model verdicts; an ambiguous straddle is reported as ambiguous.

## 5. Reporting and promotion

Exploratory, multi-model (one family), single-seed; reported separately from the
locked matrix. A SUCCESS extends the training-free two-signal readout across Qwen3
scale. **Remaining limitation:** cross-FAMILY generalization (Llama/Mistral/Gemma)
is untested and is the next axis; a headline claim still requires it plus, ideally,
a held-out dataset, registered before running. Written into Paper 3 (the two-signal
readout paper) as the generalization section.

## 6. Sign-off checklist
- [x] Prediction, falsifier, gates stated before any run (this doc).
- [x] Data-adequacy precondition stated (≥30 wrong, ≥50 halluc per model) before scoring.
- [x] Distinct rationale vs W (scale generalization, not training-seed).
- [x] Scope limitation stated (size within one family; cross-family deferred).
- [x] Models resolvable in cache/hub (`unsloth/Qwen3-{1.7B,8B,14B}-bnb-4bit`).
      Only 4B cached; 1.7B/8B/14B download on first load (expected).
- [x] GPU launch authorization (explicit, 2026-06-30): smoke Qwen3-1.7B then full
      sweep 1.7B -> 8B -> 14B, single GPU, local Docker lane.
- [x] User sign-off recorded; gates LOCKED (2026-06-30).

## 7. Result

Per-model verdict on the locked §4 gates. Roll-up assembled once all three sizes
are scored. No goalpost moved.

### Qwen3-1.7B — PASS (all three gates)

Raw `unsloth/Qwen3-1.7B-bnb-4bit`, no adapter. Pool answered=3000
(correct 377 / wrong 1476 / hallucination 629 / known_answered 518); adequacy floors
met (wrong >=30, halluc >=50).

| Gate | metric | AUROC | 95% CI | pass |
|------|--------|-------|--------|------|
| X-G1 gate | known vs unknown (L20) | 0.9958 | [0.9925, 0.9981] | yes |
| X-G2 dial | correct vs wrong (L21) | 0.8152 | [0.7871, 0.8416] | yes |
| X-G3 veto (PRIMARY) | correct vs hallucination (L21) | 0.7574 | [0.7288, 0.7855] | yes |

Dial means ordered as predicted: correct 0.558 > known 0.431 > hallucination 0.219
> wrong 0.122. Replicates the 4B mechanism at the smallest size (4B ref: gate 0.997,
dial 0.834, base veto 0.754). **Caveat:** the within-SelfAware control
(known vs hallucination, same dataset) is 0.6675 [0.6351, 0.6979] here, weaker than
4B's 0.93 — the veto's cross-source component is stronger than its within-source
component at 1.7B. Primary gates unambiguous. Result:
`experiment/phase1/probe/amendment_x_qwen3-1.7b-bnb-4bit_result.json`.

### Qwen3-8B — PASS (all three gates)

Raw `unsloth/Qwen3-8B-bnb-4bit`, no adapter. Pool answered=3000
(correct 648 / wrong 1205 / hallucination 629 / known_answered 518); adequacy floors
met (wrong >=30, halluc >=50).

| Gate | metric | AUROC | 95% CI | pass |
|------|--------|-------|--------|------|
| X-G1 gate | known vs unknown (L21) | 0.9979 | [0.9960, 0.9992] | yes |
| X-G2 dial | correct vs wrong (L20) | 0.8621 | [0.8444, 0.8797] | yes |
| X-G3 veto (PRIMARY) | correct vs hallucination | 0.8455 | [0.8236, 0.8656] | yes |

Dial means ordered as predicted: correct 0.701 > known 0.634 > hallucination 0.184
> wrong 0.160. Stronger than 1.7B on every gate (dial +0.047, veto +0.088) and the
within-SelfAware control (known vs hallucination, same dataset) recovers to 0.7953
[0.7705, 0.8199] — markedly above 1.7B's 0.6675, so the veto's within-source
component strengthens with size. Result:
`experiment/phase1/probe/amendment_x_qwen3-8b-bnb-4bit_result.json`.

### Qwen3-14B — PASS (all three gates)

Raw `unsloth/Qwen3-14B-bnb-4bit`, no adapter. Pool answered=3000
(correct 741 / wrong 1112 / hallucination 629 / known_answered 518); adequacy floors
met (wrong >=30, halluc >=50).

| Gate | metric | AUROC | 95% CI | pass |
|------|--------|-------|--------|------|
| X-G1 gate | known vs unknown (L25) | 0.9982 | [0.9966, 0.9993] | yes |
| X-G2 dial | correct vs wrong (L28) | 0.8399 | [0.8204, 0.8574] | yes |
| X-G3 veto (PRIMARY) | correct vs hallucination | 0.7412 | [0.7157, 0.7664] | yes |

Dial means ordered as predicted: correct 0.705 > known_answered 0.700 > hallucination
0.348 > wrong 0.195. The dial best layer moves deeper with depth (L28 of 40, vs L20/L21
at 8B/1.7B). **The veto is weaker than at 8B (0.741 vs 0.846):** at 14B the
hallucination dial-mean rises to 0.348 (vs 8B's 0.184), i.e. 14B's confident
confabulations read as somewhat more trustworthy, narrowing the correct-vs-hallucination
gap. Within-SelfAware control (known vs hallucination, same dataset) is 0.7373
[0.7085, 0.7651], between 1.7B's 0.6675 and 8B's 0.7953. Primary gates unambiguous.
Result: `experiment/phase1/probe/amendment_x_qwen3-14b-bnb-4bit_result.json`.

### Cross-size roll-up — all four sizes PASS

The locked §4 gates, across an order of magnitude of scale (raw `unsloth/*-bnb-4bit`
instruct bases, no adapter, no task training). 4B is the [[amendment-w-base-model-training-free]]
reference under the identical raw-base protocol.

| Size | layers | X-G1 gate | X-G2 dial | X-G3 veto (PRIMARY) | within-SA control | verdict |
|------|--------|-----------|-----------|---------------------|-------------------|---------|
| 1.7B | 28 | 0.9958 | 0.8152 | 0.7574 | 0.6675 | PASS |
| 4B (W) | 36 | 0.997 | 0.834 | 0.754 | — | PASS |
| 8B | 36 | 0.9979 | 0.8621 | 0.8455 | 0.7953 | PASS |
| 14B | 40 | 0.9982 | 0.8399 | 0.7412 | 0.7373 | PASS |

**Verdict: the training-free two-signal readout is size-robust.** All four sizes pass
all three gates; the full mechanism (answerability gate + correctness dial + confident-
hallucination veto) is recoverable on every raw Qwen3 instruct base from 1.7B to 14B
with no adapter and no task training. The gate is effectively saturated at every size
(0.996–0.998).

**Scaling is NOT monotonic (descriptive, never gated).** The §4 descriptive note
allowed that the veto might "plausibly sharpen with scale"; the data do not bear that
out. Dial and veto rise from 1.7B to a peak at 8B (dial 0.862, veto 0.846), then dip at
14B (dial 0.840, veto 0.741); the within-SA control tracks the same arc (peak 8B 0.795).
So the readout is robustly present across scale but its sharpness peaks at 8B rather than
increasing monotonically — driven at 14B by confident confabulations reading as more
trustworthy (hallucination dial-mean 0.348 vs 8B 0.184). Per §4/§5 this is reported as a
scale-dependence finding with no goalpost moved: the gated outcome (all sizes PASS)
stands, and the monotonic-sharpening expectation is recorded as not supported.
