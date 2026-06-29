# Amendment O — Probe-as-Oracle Readout-Ceiling Test

**Status:** DRAFT — awaiting user sign-off. Tier-2 exploratory cell (new evidence,
falsifier pre-stated; reported separately from the locked PROTOCOL v0.3 matrix).
**Instrument rationale:** classified Tier-2 per
`experiment-runner/reference/amendment-vs-lab-notebook.md` decision Q2 — it produces
a result that will be *reported as evidence* (the readout ceiling that motivates the
confidence-head engine change) and it carries a real falsifier. It does **not** touch
the headline surface (Tier-1) and is more than a re-score of an authorized cell
(Tier-3), because it defines a new inference-time policy and tests a new prediction.
**Compute:** CPU-only re-analysis of cached artifacts — **no training run, no new GPU
extraction** (see §3, feasibility). Launch still requires explicit user approval per
operator discipline.
**Model/surface:** Qwen3-4B, seed 1, SelfAware (n ≈ 3369). Single-model, single-seed,
exploratory.

## Revision history
- **R1 (2026-06-29, draft):** initial pre-registration.

## 1. Facts this builds on (from the merged Paper 3 arc)

1. The internal doubt/factual axis is **calibrated and discriminating**: a linear
   probe on hidden states ranks known vs unknown at **AUROC ≈ 0.997** (ECE ≈ 0.004),
   fit on TriviaQA (`experiment/phase1/probe/qwen3-4b-instruct/probe_manifest.json`,
   n = 20000, bands known p_correct ≥ 0.5 / unknown = 0).
2. **Neither training route routes that axis into a usable readout.** Amendment N
   (GRPO on the calibrated base) keeps stated calibration but cannot install
   knowledge-conditioned **action** — "says but doesn't act," and β = 0.05 showed this
   is **structural**. Amendment M (distill the axis directly into the stated token)
   keeps the action but the scalar **collapses onto it** — "acts but doesn't say"
   (correctness AUROC 0.504). Two opposite pressures, same single-token channel, same
   failure.
3. Paper 3 §8 therefore motivates an **engine change**: a dedicated confidence head
   reading the hidden state, supervised by a regression loss against the internal
   axis. That investment rests on one **untested premise**: that the calibrated
   representation, *if read out directly*, already implies a policy that clears both
   gates on the reporting (OOD SelfAware) surface. The probe's 0.997 is measured on
   TriviaQA; whether it transfers to SelfAware is exactly what is unverified.

## 2. Hypothesis and prediction

**H_O (readout ceiling exists).** A policy that drives **both** decision channels from
the probe readout —
- stated confidence_i = probe factual_p_i,
- action_i = *answer* iff probe factual_p_i ≥ τ —
clears **both** the §4.1 calibration gate and the §4.2 behavior gate on SelfAware.

If true, a passing policy already exists *latently* in the model's representation; the
trained channels just cannot express it. This is the strongest possible motivation for
the confidence-head engine change (it reduces it to "make the oracle differentiable /
online") and is itself a striking result (the model contains a passing policy it
cannot emit).

## 3. Method (CPU-only; reuses cached artifacts)

**Inputs (all already on disk):**
- **Probe (linear readout):** the TriviaQA-fit factual/known-unknown probe
  (`hidden_state_linear_probe.py`; weights/coefficients for the chosen checkpoint).
- **Cached SelfAware hidden states:**
  `experiment/phase1/probe/qwen3-4b-clean-sft-seed1-selfaware/hidden_states_selfaware_clean_sft_full/`
  (`h_base` per row, all layers, already extracted).
- **Existing SelfAware scored_rows** for the same clean-SFT base (answers,
  `greedy_correct`, gold answerable/unanswerable labels) — reused for the answer text
  and correctness whenever the oracle decides to *answer*.

**Procedure:**
1. For each SelfAware row, apply the probe to the cached hidden state at the probe's
   fitted layer → factual_p_i.
2. Oracle policy: stated_confidence_i = factual_p_i; action_i = answer iff
   factual_p_i ≥ τ. On *answer*, take the clean-SFT model's actual generated answer
   and its correctness; on *abstain*, count as a refusal.
3. Score §4.1 (threshold-free metrics) and §4.2 (behavior) with the existing
   `calibration_gap_report.py` / `action_conditioning_report.py`, adapted to consume
   oracle-driven decisions instead of the emitted scalar.

**Checkpoint-consistency requirement (resolve before running).** The probe and the
hidden states **must come from the same checkpoint**. The manifest probe is fit on the
instruct base (`unsloth/Qwen3-4B-bnb-4bit`); the cached SelfAware states are clean-SFT.
Resolve by either (a) using a clean-SFT-fit probe against the clean-SFT cache, or
(b) re-fitting/reusing the probe on the matching checkpoint's TriviaQA states. No claim
is made across mismatched checkpoints.

**τ pre-registration (no goalpost-moving).**
- **Primary τ = the probe's native known cutoff (0.5)** from the fit label bands —
  fixed in advance, not tuned on SelfAware.
- A full τ-sweep ROC is reported **descriptively only**; it may not be used to select
  a τ that manufactures a pass. The pass/fail verdict is read at the primary τ.

## 4. Gates and falsifier (pre-registered)

**§4.1 calibration (threshold-free — the core transfer test):**
- probe → appropriateness AUROC ≥ **0.70** (does the axis transfer OOD at all),
- emitted (= probe) → appropriateness AUROC ≥ **0.62** (the paper calibration gate),
  with discrimination (std), ECE < **0.30**.

**§4.2 behavior (the locked behavior gates, at the primary τ):**
- truthful ≥ **35.6**, correct_on_known ≥ **42.2**, over_refusal ≤ **67.5**,
  refusal_recall ≥ **82.0**.

**SUCCESS — ceiling demonstrated:** BOTH gates pass at the primary τ — a single policy
in the pass quadrant (top-right of Paper 3 Figure 2) that **no trained arm reached**.

**FALSIFIER — premise broken:** the oracle **fails either gate** at the primary τ. In
particular, if probe → appropriateness AUROC on SelfAware < **0.70**, the internal axis
does **not** transfer to the reporting surface, and the "signal is there, only the
readout is missing" premise is false there. This kills the simple ceiling story and
redirects the program: either the axis is TriviaQA-specific (needs an OOD-robust probe
target) or the obstruction is upstream of the readout — and the confidence-head engine
change is **not** justified by a latent ceiling until that is resolved.

**Ambiguity rule:** if the result straddles a gate (e.g. calibration passes, behavior
marginal), report it as ambiguous; do not retune τ or the gates to force a verdict.

## 5. Reporting and promotion

Exploratory, single-model, single-seed. Reported **separately** from the locked matrix.
A success is a **lead** that motivates the confidence-head experiment, not a headline
claim; promotion to a claim requires the engine experiment itself plus the usual
replication discipline. The result will be written into Paper 3 §8 as the ceiling that
does (or does not) justify the proposed engine change.

## 6. Sign-off checklist
- [ ] Prediction, falsifier, and gates stated above before any run (this doc).
- [ ] Checkpoint-consistency resolution chosen (§3) and recorded.
- [ ] CPU-only; no GPU extraction or training launched without separate approval.
- [ ] User sign-off recorded here with date + approval phrase.

## 7. Result
_(pending — appended after the run.)_
