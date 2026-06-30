# Amendment W — Training-Free Base-Model Two-Signal Mechanism

**Status:** DRAFT — pending sign-off. Tier-2 exploratory cell (new evidence,
falsifier pre-stated; reported separately from the locked PROTOCOL v0.3 matrix).
Result pending in §7.

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
- [ ] GPU launch authorization (explicit). _pending_
- [ ] User sign-off recorded; gates LOCKED. _pending_

## 7. Result

_(to be written after the run; verdict on the locked §4 primary, no goalpost moved)_
