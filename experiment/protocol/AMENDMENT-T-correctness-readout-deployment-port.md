# Amendment T — Correctness-Readout Deployment-Checkpoint Port

**Status:** SIGNED (2026-06-30) — user sign-off + GPU authorization recorded.
Gates / primary metric / falsifier below are LOCKED — no goalpost-moving after
the result. Tier-2 exploratory cell (new evidence, falsifier pre-stated; reported
separately from the locked PROTOCOL v0.3 matrix).

**Sign-off (2026-06-30):** abstention-suppression method = forced-best-guess
system prompt (locked choice; distribution-shift caveat in §3 bounds the claim);
GPU run authorized (free-answer generation + dual-position extraction on the
clean-SFT + GRPO-v2 checkpoint, local lane). Gates T-G1/T-G2/T-G3 and the
falsifier as written in §4 are LOCKED.

**Instrument rationale:** Tier-2 Amendment per
`experiment-runner/reference/amendment-vs-lab-notebook.md`. Amendment S
([[amendment-s-correctness-readout-success]]) established the correctness readout
on the **Instruct base**; it explicitly scoped the **deployment-checkpoint port**
as a separate follow-up. This cell carries a distinct mechanistic question — does
the post-gen correctness readout **survive calibration training** (clean-SFT →
GRPO-v2), the checkpoint we would actually ship, or was it an Instruct-base
artifact? Distinct question ⇒ a new amendment.

**Compute:** GPU — a NEW free-answer generation (abstention suppressed) +
dual-position hidden-state extraction pass on the deployment checkpoint. No
training run. Launch requires explicit user approval per operator discipline.

**Model/surface:** Qwen3-4B **clean-SFT merged base + GRPO-v2 LoRA adapter** (the
Phase-3 "current clean" deployment subject; the same checkpoint family the
answerability axis was validated on in O/P, so the eventual two-signal mechanism
sits on one checkpoint). Single-model, single-seed, exploratory.

## 1. Facts this builds on

### 1.1 Amendment S succeeded — on the Instruct base
On `unsloth/Qwen3-4B-bnb-4bit` (Instruct base, pre-abstention), per-answer
correctness is linearly readable post-generation (AUROC **0.834**, L20) and reads
**+0.065** stronger after the answer than before (95% CI [0.040, 0.090], excludes
0). That is the first positive P(True)/self-eval evidence in the program, but it
was measured on the base model, NOT the deployed (calibration-trained) checkpoint.

### 1.2 Why the deployed checkpoint is a different question
The two-signal mechanism (answerability gate + correctness dial) must live on ONE
shipped checkpoint. The answerability gate is validated on clean-SFT/GRPO
([[amendment-o-probe-as-oracle-ceiling]], [[amendment-p-xdataset-transfer]]); the
correctness dial is so far only validated on the Instruct base. Calibration RL
(GRPO-v2) reshapes the **answer/abstain policy and the emitted channel** — the
program's repeated finding is that this leaves the **internal factual
representations intact** while only the emitted channel/policy moves
([[amendment-r-phase-b-falsified]], [[amendment-n-beta005-structural-decoupling]]).
Prediction follows in §2; this cell tests it directly.

### 1.3 Why abstention must be suppressed at generation
The deployment checkpoint is abstention-trained: left to itself it answers only
when ~94% likely right (clean-SFT SelfAware = 407 correct / 27 wrong), so it
yields no wrong class to fit a correctness probe on (the
[[correctness-probe-underpowered-reframe]] blocker). The fix used here is a
**forced-best-guess system prompt** (never abstain; always give one best-guess
answer), the cheapest deployment-realistic "answer mode". This produces a labeled
correct/wrong set. Distribution-shift caveat is stated in §3 and bounds the claim.

## 2. Hypothesis and prediction

**H_T (the correctness readout survives calibration training).** On the deployment
checkpoint, a linear probe on hidden states discriminates correct vs wrong
answered attempts at useful strength, and still reads this **more strongly after
the answer than before**:

- **H_T1 (signal exists on the deployed model):** best post-gen correctness-AUROC
  ≥ **0.70** (5-fold CV, out-of-fold).
- **H_T2 (self-eval gain replicates — THE BET, primary):** best post-gen
  correctness-AUROC exceeds best pre-gen by ≥ **+0.05** (delta CI excludes 0).

**Predicted direction:** PASS on both. Rationale: the base is the same Qwen3-4B;
GRPO-v2 moves the policy/emitted channel, not the factual representation, so the
post-gen correctness signal should persist. The genuinely uncertain part is the
secondary cross-checkpoint cold-transfer (§4), not H_T1/H_T2.

If H_T holds, the correctness dial is buildable on the shipped checkpoint and the
full two-signal mechanism becomes the next amendment. If H_T fails, the readout is
an Instruct-base property that does NOT survive calibration training — a
publishable negative that redirects the mechanism toward training the readout
INTO the checkpoint rather than reading it off.

## 3. Method (GPU extraction + CPU probe)

**Checkpoint load.** Base = clean-SFT merged-16bit
(`scratch/.../sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`);
active adapter = GRPO-v2
(`scratch/.../schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`),
applied via PEFT exactly as the existing extraction backend does. Both present on
disk (gitignored scratch artifacts). Thinking off.

**Surface.** SAME PopQA + TriviaQA-gold pool, SAME dual-position extraction, SAME
probe recipe and grading (verbatim Cheng alias scorer) as Amendment S — only the
checkpoint and the abstention-suppressing system prompt change, so the
S-vs-T comparison is clean.

**Procedure (mirrors S §3):**
1. **Free-answer generation (GPU), abstention suppressed.** Greedy-decode one
   answer per question under a forced-best-guess system prompt (never abstain).
   Label correct/wrong vs gold. Record the system prompt in the run manifest.
2. **Dual-position extraction (GPU).** For each answered row, one forward over
   [prompt + answer]; read pre-gen (end-of-prompt generation anchor) and post-gen
   (last answer content token) across all layers.
3. **Probe fit (CPU).** Logistic probe on correct(1)/wrong(0), 5-fold stratified
   CV out-of-fold, per (layer × position). AUROC surface.
4. **Surface + score (CPU).** correctness-AUROC, ECE, selective-prediction curve
   at the best post-gen (layer, position).
5. **Cross-checkpoint cold transfer (CPU, secondary).** Fit the probe on the
   Amendment S Instruct-base extraction (already on disk) and apply it COLD to
   this checkpoint's post-gen vectors; report transfer AUROC (descriptive).

**Distribution-shift caveat (bounds the claim).** Fitting on forced-best-guess
answers measures whether correctness is *readable on this checkpoint*, not whether
the probe generalizes to the model's *natural* (un-forced) answers. The latter is
an explicit follow-up, out of scope here.

## 4. Gates and falsifier (to be LOCKED at sign-off)

**Baseline (anchored, not guessed).** Same chain as S: chance 0.50; verbalized 0.504;
emitted 0.559; the run's own **pre-gen read** is the in-run baseline. On the
Instruct base, S measured pre-gen 0.769 / post-gen 0.834. The novel question is
whether *post beats pre on the deployed checkpoint*, measured in-run.

**Data sizing / adequacy precondition (checked BEFORE fitting; not a result).**
Hard floor ≥ **150 correct** AND ≥ **150 wrong**; target ≈ **500 correct AND ≈ 500
wrong**. Below the floor is a data-stage stop (suppress abstention harder / pool
more questions), NOT a probe verdict.

**Metrics (threshold-free):**
- **T-G2 — PRIMARY (self-eval gain replicates):** best post-gen correctness-AUROC
  − best pre-gen correctness-AUROC ≥ **+0.05**, AND the delta's bootstrap 95% CI
  excludes 0. Baselined on the run's own pre-gen read.
- **T-G1 — usefulness floor (signal exists on deployed model):** best post-gen
  correctness-AUROC ≥ **0.70** (5-fold CV). Bands: 0.70 useful · 0.75 moderate ·
  0.80+ strong.
- **T-G3 — calibration:** ECE of surfaced confidence vs correctness < **0.15** at
  the best post-gen (layer, position). Reported, NOT a green-light gate (matches S).
- **Secondary (descriptive, NOT gated):** cross-checkpoint cold-transfer AUROC of
  the S-fit probe on this checkpoint's post-gen vectors.

**SUCCESS — readout survives, dial buildable on the shipped checkpoint:** T-G2
(primary) AND T-G1 pass (T-G3 and cold-transfer reported).

**FALSIFIER — readout does NOT survive calibration training:** best post-gen
correctness-AUROC < 0.70 **AND** post−pre ≤ +0.05. The deployed checkpoint does
not linearly represent its own correctness post-generation any better than before;
the correctness dial is not achievable by linear readout on the shipped model, and
the mechanism must train the readout in rather than read it off. Report as a
negative; do NOT open a tweak-amendment.

**No goalpost-moving.** Thresholds fixed at sign-off. The selective-prediction
curve, cold-transfer number, and any τ are descriptive only; the verdict is read
on the threshold-free primary metrics. An ambiguous straddle is reported as
ambiguous, not retuned.

## 5. Reporting and promotion

Exploratory, single-model, single-seed; reported **separately** from the locked
matrix. A success is the de-risking step that makes the **full two-signal
mechanism** (answerability gate + correctness dial on one checkpoint) the next
amendment. Promotion to a headline claim requires a confirmatory replication
(fresh seeds / 8B / held-out) registered before running, per the firewall.
Written into Paper 3 §8 alongside the Amendment S result.

## 6. Sign-off checklist
- [x] Prediction, falsifier, and gates stated above before any run (this doc).
- [x] Data-adequacy precondition stated (≥150/≥150) and ordered before the fit.
- [x] Distinct mechanistic rationale vs Amendment S (deployment checkpoint +
  abstention suppression + survives-calibration question, not Instruct base).
- [x] Checkpoint resolved and confirmed present on disk (merged base + GRPO-v2
  adapter).
- [x] GPU launch authorization (explicit): free-answer generation (abstention
  suppressed) + dual-position extraction on the clean-SFT + GRPO-v2 checkpoint,
  local lane. **Authorized 2026-06-30.**
- [x] User sign-off recorded; gates LOCKED. **Signed 2026-06-30** (forced-best-guess
  suppression method selected).

## 7. Result

_Pending sign-off and run._
