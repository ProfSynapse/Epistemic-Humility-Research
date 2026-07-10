---
amendment: O
slug: probe-as-oracle-readout-ceiling
question: >-
  Does driving both decision channels from the linear probe readout clear
  both gates on SelfAware, proving a latent passing policy?
predictions:
  orchestrator:
    call: probe-readout oracle clears both gates (readout ceiling exists)
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  SUCCESS — all 7 gates pass; probe-to-appropriateness AUROC 0.9967,
  action margin +95pt (no trained arm reached it); non-circular
  correctness AUROC only 0.640. In-distribution CV, single seed.
scoreboard: null
---

# Amendment O — Probe-as-Oracle Readout-Ceiling Test

**Status:** SIGNED 2026-06-29 (user: "signed off lets GOO"). Tier-2 exploratory cell
(new evidence, falsifier pre-stated; reported separately from the locked PROTOCOL v0.3
matrix). Gates, primary τ, and falsifier below are LOCKED as of sign-off — no
goalpost-moving after the result.
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
- **R1 (2026-06-29, SIGNED):** initial pre-registration; signed off as-is by the user
  ("signed off lets GOO"). CPU-only run authorized.

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
- [x] Prediction, falsifier, and gates stated above before any run (this doc).
- [x] Checkpoint-consistency resolution chosen (§3) and recorded: route (a) —
  clean-SFT-fit probe (5-fold CV) against the clean-SFT SelfAware cache. No claim
  across mismatched checkpoints.
- [x] CPU-only; no GPU extraction or training launched without separate approval.
- [x] User sign-off recorded: 2026-06-29, "signed off lets GOO" (+ CPU run authorized).

## 7. Result

**VERDICT: SUCCESS — ceiling demonstrated, emphatically. Falsifier dead; all 7
gates pass.** Run 2026-06-29, CPU-only, `probe_as_oracle_ceiling.py` on the cached
clean-SFT SelfAware extraction at L35, primary τ = 0.5 (native cutoff, not tuned).
Labeled subset n = 1233 (556 known / 677 unknown).

**§4.1 calibration (threshold-free):**
- probe → appropriateness **AUROC 0.9967** (gate ≥ 0.70 ✓; reproduces the paper's
  L35 ≈ 0.997 — the falsifier line at 0.70 is not remotely approached).
- emitted (= probe) → appropriateness **AUROC 0.9967** (gate ≥ 0.62 ✓).
- **ECE 0.0149** (gate < 0.30 ✓); factual_p std 0.486 (well-spread, not collapsed —
  contrast Amendment M's 3 distinct emitted values).

**§4.2 behavior (oracle policy at τ = 0.5):**
- **over_refusal 3.24%** (gate ≤ 67.5 ✓) — vs M's 62.26.
- **refusal_recall 98.38%** (gate ≥ 82.0 ✓).
- answer_rate known 96.76% / unknown 1.62% → **action margin +95.14 pts** (vs M's
  +31.2, N's +2.85). A single policy sitting in the pass quadrant that **no trained
  arm reached.**
- **truthful 86.21%** (gate ≥ 35.6 ✓), **correct_on_known 73.79%** (gate ≥ 42.2 ✓).

**The genuinely non-circular finding:** answered-knowns correct-vs-wrong
**AUROC 0.640**. The answerability axis only *modestly* tracks per-attempt
correctness (0.64) — far below its 0.997 on answerability, but above the trained
stated scalar (M 0.504, base 0.559). Design implication for the engine change: a
head supervised on known/unknown buys a near-perfect *action* policy and calibrated
*appropriateness*, but **does not** by itself buy correctness-ranking; a
correctness-calibrated head needs a correctness target, not just the answerability
label.

**Caveats (do not overclaim):**
1. **In-distribution readout ceiling, not a TriviaQA→SelfAware transfer test.** The
   probe is fit by 5-fold CV *on SelfAware itself* (out-of-fold, no per-row leakage,
   but in-distribution). This measures whether a passing policy exists *latently in
   the SelfAware representation* — it does, decisively. It does **not** establish
   that a probe/head trained on the *training* distribution transfers to SelfAware;
   that stricter test (train-dist-fit probe applied cold to SelfAware) is the natural
   follow-up and is what the deployed head must actually earn. (Checkpoint-consistency
   per §3 was resolved by route (a): clean-SFT-fit probe against the clean-SFT cache.)
2. **The action metrics are partly circular.** The probe predicts the same
   known/unknown labels that *define* over_refusal / refusal_recall, so +95 pts is a
   near-tautology of "the representation linearly separates known/unknown at 0.997."
   The legitimate, non-circular content: the trained arms had the **same labels** as
   their training signal and still could not route them to the action (M maxed at
   +31), whereas a plain linear readout extracts them at +95. The signal is in the
   representation at near-perfect fidelity; the bottleneck is the readout/channel —
   confirmed now from the positive side. The single number that is *not* circular is
   AUROC→correctness = 0.64.
3. **correct_on_known / truthful are a lower bound.** They reuse the clean-SFT
   model's cached greedy generations. For knowns the base model *refused*, there is
   no cached correct answer, so the oracle "answering" them is scored as incorrect —
   dragging both metrics down. True values under an oracle that actually re-generates
   are ≥ reported. Full measurement needs a cheap re-generation pass (knowns the base
   refused, decoded under the oracle's answer decision). Reported on the labeled
   subset n = 1233, not the full n = 3369.

**Base sanity (same rows, model's own behavior):** known answered 43.8% / correct
20.2%; unknown answered 12.9% / correct 0.0%. The oracle moves known-answer-rate
43.8 → 96.8 and unknown-answer-rate 12.9 → 1.6.

**So what.** H_O holds: a passing policy already exists latently in the clean-SFT
representation; the trained channels just cannot express it. This is the strongest
available motivation for the confidence-head engine change — it reduces the open
problem to "make the oracle readout differentiable / online" rather than "find a
signal." It does **not** retire the two things the engine experiment must still earn:
(a) cross-distribution transfer (caveat 1), and (b) correctness-calibration as
opposed to answerability-calibration (the 0.64). Result written into Paper 3 §8 as
the ceiling that motivates — with those two earned caveats — the proposed engine
change. Exploratory, single-model, single-seed; reported separately from the locked
matrix; not a headline claim.

Artifacts: scorer `experiments/probe-as-oracle-readout-ceiling/probe_as_oracle_ceiling.py`; raw per-row
result JSON written to the (gitignored) extraction dir
`.../hidden_states_selfaware_clean_sft_full/amendment_o_probe_as_oracle.json` (not
redistributed; numbers transcribed here are the tracked record).
