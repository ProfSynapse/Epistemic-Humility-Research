---
amendment: W
slug: base-model-training-free-mechanism
question: >-
  Does the full two-signal mechanism (gate + dial + hallucination veto)
  hold on the raw untrained Instruct base with no adapter?
predictions:
  orchestrator:
    call: >-
      PASS; gate and dial are representation properties present pre-training
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  SUCCESS — full mechanism reads training-free (gate 0.997, veto 0.754);
  training does not create the veto, it sharpens it (0.754 to 0.980).
scoreboard: null
---

# Amendment W — Training-Free Base-Model Two-Signal Mechanism

**Status:** RESOLVED — SUCCESS (2026-06-30). Both locked gates passed; falsifier did
not fire. Tier-2 exploratory cell (new evidence, falsifier pre-stated; reported
separately from the locked PROTOCOL v0.3 matrix). Result in §7.

**Sign-off (2026-06-30):** gates W-G1 (primary) / W-G2 and the falsifier as written
in §4 are LOCKED; the ≥50-hallucination data-adequacy precondition is ordered before
the fit. GPU run AUTHORIZED — forced-answer generation + dual-position extraction
over the SelfAware pool on the RAW Instruct base (no adapter), local lane (smoke
first, then full). No goalpost may move after the result.

**Supersedes (governance note):** an earlier, never-signed sketch of a
"cross-recipe replication on GRPO-v3" cell occupied the working "W" slot in
session notes. It is dropped: the question below (does the mechanism need ANY
training?) strictly subsumes "does it survive a different training recipe?" No
GRPO-v3 amendment was ever minted, so no signed work is being retired.

**Instrument rationale:** Tier-2 Amendment per
`experiment-runner/reference/amendment-vs-lab-notebook.md`. Amendments S/T/U/V all
read the two-signal mechanism off a *trained* checkpoint (S: Instruct base for the
dial only; T/U/V: clean-SFT + GRPO-v2). The distinct question here — does the
FULL mechanism (answerability gate + correctness dial + hallucination veto) hold
on the **raw, untrained Instruct base** — is a new evidence cell, so it gets a new
amendment with its own pre-stated falsifier.

**Compute:** GPU — ONE new forced-answer generation + dual-position extraction pass
over the SelfAware pool on the **raw Instruct base (no adapter)**. No training run.
Launch requires explicit user approval per operator discipline.

**Model/surface:** `unsloth/Qwen3-4B-bnb-4bit` (the RAW Qwen3-4B Instruct base,
model_tag `qwen3-4b-instruct`), NO LoRA adapter — identical surface to Amendment S.
Amendment S's answer-encouraging system prompt (NOT the forced-best-guess T/U
prompt), so the new base-hallucination post-gen vectors lie on the SAME generation
surface the S base dial was fit on.

## 1. Facts this builds on

- The correctness **dial** reads per-answer correctness on the RAW Instruct base
  post-gen at AUROC **0.834** (L20; 500 correct / 1336 wrong) — already training-free
  ([[amendment-s-correctness-readout-success]]).
- On the *trained* checkpoint the dial flags hallucinations as lowest-trust at
  AUROC **0.980** (U-G3) ([[amendment-u-dial-vetoes-hallucinations]]) — but that
  veto leg has only ever been measured on the trained checkpoint.
- The answerability **gate** read off RAW base activations (`h_base`, no adapter)
  on the frozen 256-row TriviaQA known/unknown set scores AUROC **0.836** (L24) vs
  **0.851** for the GRPO-v2 LoRA on the same rows — the adapter buys +0.015. The
  gate is essentially fully present in the untrained base (CPU, this session).
- Program findings N/M/R: GRPO moves the emitted/behavioral channel and the
  abstention policy, NOT the internal axis ([[amendment-n-beta005-structural-decoupling]],
  [[amendment-m-r3-factual-axis-retarget]], [[amendment-r-phase-b-falsified]]).
- Synthesis: the deliverable (a thresholdable surfaced confidence read from
  activations) appears to be a PROBE property, present pre-training. The one leg
  never tested training-free is the **hallucination veto**.

## 2. Hypothesis and prediction

**H_W (the full two-signal mechanism is training-free).** On the raw Instruct base
with no adapter, the gate separates answerable from unanswerable, and the base-fit
correctness dial ranks base-hallucinations (unanswerable questions the base chose
to answer) below base-correct answers.

- **H_W1 (dial vetoes base hallucinations — PRIMARY):** AUROC(base-correct vs
  base-hallucination), the S base-fit dial applied COLD, ≥ **0.65**, CI excludes 0.50.
- **H_W2 (gate reads on the base SelfAware anchor):** AUROC(known vs unknown) from
  this run's pre-gen anchors ≥ **0.65**, CI excludes 0.50.

**Predicted direction:** PASS — if the dial and gate are representation properties
(S 0.834, gate 0.836), the untrained base should already support the veto. The
genuinely uncertain part is whether confident confabulation reads as low-trust
*without* the policy training that taught the model to abstain.

If H_W holds, the entire mechanism is training-free: training buys behavioral
abstention (the model refuses on its own), not the latent signal the probe reads —
the headline reframe. If H_W1 fails, the veto leg specifically requires training (a
publishable negative bounding the "training-free" claim: gate + dial-on-correct/wrong
are training-free, the veto is not).

## 3. Method (GPU extraction + CPU score)

**Checkpoint load.** RAW `unsloth/Qwen3-4B-bnb-4bit`, NO adapter (identical to S).
Thinking off. **Amendment S's system prompt VERBATIM** (answer-encouraging, not the
forced T/U prompt), recorded in the manifest. The base is pre-abstention, so it
answers freely — no forced suppression is needed and none is applied.

**Pool.** SelfAware frozen row manifest (the exact known/unknown questions the gate
was validated on), read from the gate extraction's `rows.jsonl` — identical pool
source to U.

**Procedure (reuses U's SelfAware path + S's raw-base load + S/T grading helpers):**
1. Generation (GPU). Greedy-decode one answer per question; classify answered vs
   refused (verbatim `scorers.is_stated_confidence_refusal`).
2. Label (structural, ungraded — verbatim U): unknown ∧ answered = HALLUCINATION;
   known ∧ answered = answerable_attempt (ungraded directional control).
3. Dual-position extraction (GPU) on answered rows (pre-gen anchor + post-gen
   content token, all layers, fp32).
4. Score (CPU). Fit the correctness dial on the S base extraction (post-gen L20,
   correct vs wrong) and apply it COLD to base-correct / base-hallucination; also
   compute the gate AUROC on this run's pre-gen anchors and the within-SelfAware
   control. The S reference groups are scored OUT-OF-FOLD; the dial applied to this
   run's hallucinations is full-fit-on-S (cold), mirroring the vetted U scorer.

**Caveats.** Single-model, single-seed, exploratory. SelfAware rows are ungraded so
the hallucination label is structural (unknown ∧ answered), exactly as in U. The
"base-correct" reference comes from a different dataset (S's PopQA/TriviaQA) than the
hallucinations (SelfAware), so the within-SelfAware control (known-answered vs
hallucination) is reported to bound dataset-shift, exactly as in U.

## 4. Gates and falsifier (LOCKED at sign-off)

**Data-adequacy precondition (checked BEFORE scoring; not a result).** Hard floor
≥ **50 base-hallucinations**. The raw base is pre-abstention and should answer
freely, so unlike the trained checkpoint this floor is expected to clear easily;
below floor is a DATA-STAGE stop, not a probe verdict.

**Metrics (threshold-free):**
- **W-G1 — PRIMARY:** AUROC(base-correct vs base-hallucination) ≥ **0.65**,
  bootstrap 95% CI excludes 0.50. (Base analog of U-G3.)
- **W-G2:** AUROC(known vs unknown) from this run's pre-gen anchors ≥ **0.65**,
  CI excludes 0.50. (Gate reads on the base SelfAware surface.)
- **Descriptive (NOT gated):** 3-way dial-score distribution (base-correct,
  base known-answered, base-hallucination); within-SelfAware control
  AUROC(known-answered vs hallucination) to bound dataset shift.

**SUCCESS — the full mechanism is training-free:** W-G1 (primary) AND W-G2 pass.

**FALSIFIER — the hallucination veto requires training:** W-G1 < 0.65 AND its CI
includes 0.50 (the base dial does not rank base-hallucinations below base-correct).
Then the veto leg is training-dependent even though gate + dial-on-correct/wrong are
not; report as a negative bounding the training-free claim. Do NOT open a
tweak-amendment.

**No goalpost-moving.** Thresholds fixed at sign-off; descriptive numbers do not
move the verdict; an ambiguous straddle is reported as ambiguous.

## 5. Reporting and promotion

Exploratory, single-model, single-seed; reported separately from the locked matrix.
A SUCCESS establishes that the two-signal mechanism is a readout property of the
untrained base, not a training outcome — what GRPO buys is behavioral abstention,
not the latent signal. Promotion to a headline claim still requires a confirmatory
replication (fresh seeds / 8B / held-out) registered before running. Written into
Paper 3 §8 alongside S/T/U.

## 6. Sign-off checklist
- [x] Prediction, falsifier, gates stated before any run (this doc).
- [x] Data-adequacy precondition stated (≥50 base-hallucinations) before scoring.
- [x] Distinct rationale vs S/T/U/V (raw untrained base, full mechanism incl. veto).
- [x] Checkpoint resolved = raw `unsloth/Qwen3-4B-bnb-4bit`, no adapter (= S surface).
- [x] GPU launch authorization (explicit). **Authorized 2026-06-30** (smoke then full).
- [x] User sign-off recorded; gates LOCKED. **Signed 2026-06-30.**

## 7. Result

**SUCCESS — both locked gates pass; the falsifier did NOT fire.** The full
two-signal mechanism reads off the RAW Qwen3-4B Instruct base with NO adapter and
NO training. Run: 1,233 SelfAware questions, **0 refused** (the base is
pre-abstention and answered every question), 677 hallucinations + 556
known-answered — the ≥50 adequacy floor cleared decisively.

| Leg | Gate | Raw base (W) | Trained checkpoint (prior) |
|-----|------|--------------|----------------------------|
| Answerability **gate** (known vs unknown, pre-gen anchor) | **W-G2** | **0.997** @L18, CI [0.995, 0.999] — PASS | 0.999 (U-G1) |
| Correctness **dial** (correct vs wrong, post-gen) | — | 0.834 (Amendment S) | 0.819 (T) |
| Hallucination **veto** (S-correct vs hallucination) | **W-G1 PRIMARY** | **0.7545** @L20, CI [0.728, 0.782] — PASS | 0.980 (U-G3) |

**Headline:** the mechanism is a readout property of the untrained base, not a
training outcome. What GRPO training buys is *behavioral* abstention (the model
refuses on its own) and a *sharper* veto — not the latent signal itself.

**The honest nuance (no goalpost moved — W-G1 was locked at 0.65 and cleared at
0.75):** the veto is training-free but markedly WEAKER on the base than after
training (0.754 vs 0.980). On the base, hallucinations read as *middling* trust
(dial mean 0.271, sitting between wrong 0.141 and correct 0.613); on the trained
checkpoint they read as lowest-of-all (U: 0.018). The within-SelfAware confound
control is correspondingly weaker (known-answered vs hallucination 0.699,
CI [0.669, 0.727], vs U's 0.93). So training does not CREATE the veto — it
SHARPENS confident confabulation into a clearly-lowest-trust signal. The gate, by
contrast, is essentially saturated on the base already (0.997 vs 0.999); training
adds nothing there.

**What this answers (the originating question — "do we even need the training?"):**
For the deliverable (a thresholdable surfaced confidence read from activations),
the gate and dial are fully training-free, and the veto is present training-free.
Training is not required to expose the signal; it is an *amplifier* for the
hallucination-veto leg specifically. Consistent with program findings N/M/R
(training moves the behavioral/emitted channel, not the existence of the internal
axis) — here quantified: +0.226 AUROC of veto sharpening, ~0 gate gain.

**Caveats.** Single-model, single-seed, exploratory. Structural hallucination label
(unknown ∧ answered), ungraded SelfAware rows — identical to U. The base-correct
reference is cross-dataset (S's PopQA/TriviaQA) vs SelfAware hallucinations; the
within-SelfAware control (0.699) bounds but does not eliminate the dataset-shift
contribution to W-G1. Promotion to a headline claim still requires a confirmatory
replication (fresh seeds / 8B / held-out) registered before running.

Result JSON: `experiment/phase1/probe/qwen3-4b-instruct/amendment_w/stage2/amendment_w_base_model_result.json`.
