---
amendment: U
slug: unified-two-signal-dial-veto
question: >-
  Does the correctness dial flag hallucinated answers to unanswerable
  questions as low-trust (independent hallucination defense)?
predictions:
  orchestrator:
    call: >-
      PASS in 0.65-0.85 band; risk falsifier fires on confident confabulation
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  SUCCESS — dial flags hallucinations as lowest-trust of all (U-G3 AUROC
  0.980, within-SelfAware control 0.93); confident confabulation reads
  opposite to correctness.
scoreboard: null
---

# Amendment U — Unified Single-Stream Two-Signal Mechanism (Dial-Veto on Unknowns)

**Status:** RESOLVED — SUCCESS (2026-06-30). The correctness dial flags
hallucinations on unanswerable questions as lowest-trust (U-G3 AUROC 0.980, the
falsifier did NOT fire). Gates were LOCKED at sign-off; no goalpost moved. Tier-2
exploratory cell (new evidence, falsifier pre-stated; reported separately from the
locked PROTOCOL v0.3 matrix). Full result in §7.

**Sign-off (2026-06-30):** gates U-G1/U-G3 and the falsifier as written in §4 are
LOCKED; data-adequacy precondition (≥50 hallucinations) ordered before the fit.
GPU run AUTHORIZED — forced-best-guess generation + dual-position extraction over
the SelfAware pool on the clean-SFT + GRPO-v2 checkpoint, local lane (smoke first,
then full 1,233-item run). No goalpost may move after the result.

**Instrument rationale:** Tier-2 Amendment per
`experiment-runner/reference/amendment-vs-lab-notebook.md`. The Stage 1 / Stage 1.5
CPU diagnostics ([[two-signal-pipeline-not-fused]], PR #128) composed existing
extractions to validate the gate and dial as a two-stage pipeline and showed the
gate transfers cross-pool/cross-prompt. They could NOT test one thing, because the
data does not exist on disk: **post-generation reads on hallucinations** — i.e.
whether the correctness dial assigns LOW trust to a fabricated answer on a question
that has no answer. That is a distinct mechanistic question requiring a NEW GPU
generation pass ⇒ a new amendment.

**Compute:** GPU — a NEW forced-best-guess generation + dual-position hidden-state
extraction pass over the SelfAware pool on the deployment checkpoint. No training
run. Launch requires explicit user approval per operator discipline.

**Model/surface:** Qwen3-4B **clean-SFT merged base + GRPO-v2 LoRA adapter** — the
identical deployed checkpoint and identical forced-best-guess prompt as Amendment
T ([[amendment-t-deployment-readout-survives]]), so T's answerable extraction and
this run compose into ONE per-item stream with no checkpoint or prompt mismatch.
Single-model, single-seed, exploratory.

## 1. Facts this builds on

### 1.1 The two-signal mechanism is a pipeline (Stage 1 / 1.5, PR #128)
On the deployed clean-SFT → GRPO-v2 checkpoint, on CPU from existing tensors:
- **Gate** (answerability, pre-gen prompt anchor): AUROC **0.997** (L33), and it
  transfers COLD onto T's prompt anchors at mean P(answerable) **0.997** across the
  question-pool AND forced-best-guess prompt shift. Near-perfect abstention: on a
  mixed stream it drives hallucination-of-answered 0.31 → ~0.01 at any τ∈[0.1,0.95]
  while keeping ~99.9% of answerable items.
- **Dial** (per-answer correctness, post-gen): AUROC **0.819** (L22, T), ECE
  0.168 → 0.030 isotonic.
- The two axes are **orthogonal**: fusing the gate score into the dial does NOT
  improve correctness triage (Δ −0.014, CI excludes 0). Keep them as two stages.

### 1.2 The one thing Stage 1.5 could not test
Stage 1.5's mixed stream paired T-answerable items (which have post-gen reads) with
SelfAware-unknown items (which do **not** — the gate extraction only stored the
prompt anchor, never generated an answer). So the dial could not be applied to any
unanswerable item. The gate is near-perfect, so few unanswerables slip it — but the
ones that DO slip are exactly the dangerous, deployment-relevant case, and we have
zero post-gen reads on hallucinations to know whether the dial would catch them.

### 1.3 GRPO-v2 abstention is prompt-robust
T observed the deployed checkpoint refused ~82% of attempts even under the
forced-best-guess prompt. So on the SelfAware-unknown pool the model will refuse
most items (its native abstention), and the **residual** answered-unknown items are
the hallucinations of interest. This both bounds the data yield (§4 adequacy) and
is itself the deployment threat model: the gate + native abstention catch most
unknowns; do the residual hallucinations carry a low-trust internal signature?

## 2. Hypothesis and prediction

**H_U (the dial provides independent hallucination defense).** The correctness dial
fit on answerable correct-vs-wrong answers ALSO reads a hallucinated answer to an
unanswerable question as low-trust — i.e. the post-gen correctness representation is
not just "is this answerable-and-right" but tracks whether THIS answer is to be
trusted, so a confabulation lands in the low-trust region with genuinely wrong
answers, not with correct ones.

- **H_U1 (gate replicates single-pipeline, confirmatory):** within-SelfAware
  known-vs-unknown answerability AUROC on the pre-gen anchor under the
  forced-best-guess prompt ≥ **0.90**.
- **H_U3 (dial flags hallucinations — THE BET, primary):** the dial score
  (T-fit correctness probe, applied to post-gen vectors) separates
  **{answerable-correct}** from **{unanswerable-hallucination}** at AUROC ≥ **0.65**,
  CI excludes 0.50.

**Predicted direction:** PASS on H_U1 (the gate already transfers cross-prompt at
0.997). H_U3 is the genuinely uncertain bet — I predict PASS in the **0.65–0.85**
band: a fabricated answer to an unanswerable question should lack the internal
"correctness signature" the dial keys on. The real risk that the falsifier fires:
**confident confabulation** may carry the same internal signature as a confident
correct answer (the model does not "know it is making it up"), in which case the
dial cannot defend against hallucinations and the gate is the sole abstention
mechanism. Either outcome is publishable.

## 3. Method (GPU extraction + CPU score)

**Checkpoint load.** IDENTICAL to Amendment T: base = clean-SFT merged-16bit
(`scratch/.../sft_schema_clean_seed1_full/.../merged-16bit`); active adapter =
GRPO-v2 (`scratch/.../schema_clean_sft_grpo_v2_seed1_full/.../final_model`), applied
via PEFT, adapter active for generation and extraction. Thinking off. Forced-
best-guess system prompt VERBATIM from T (recorded in the manifest).

**Pool.** ALL SelfAware items from the gate's frozen row manifest (the exact 556
known + 677 unknown questions the answerability gate was validated on;
`extraction__55254a04aa1f/rows.jsonl`). Unknown = unanswerable (any forced answer is
a hallucination by construction; `aliases = []`). Known = answerable-pool control
(answered items used ungraded — see §3 caveat).

**Procedure (mirrors T §3; reuses T's extractor helpers verbatim):**
1. **Forced-best-guess generation (GPU).** Greedy-decode one answer per SelfAware
   question under the forced-best-guess prompt. Classify each attempt:
   answered vs refused (verbatim `scorers.is_stated_confidence_refusal`).
2. **Dual-position extraction (GPU).** For each ANSWERED row, one forward over
   [prompt + answer]; read pre-gen (end-of-prompt anchor) and post-gen (last answer
   content token) across all layers. Persist fp32 safetensors + rows.jsonl with
   `label∈{known,unknown}`, `answered`, `refused`, `outcome∈{answerable_attempt,
   hallucination}` (`hallucination` = unknown ∧ answered).
3. **Gate confirm (CPU).** Within-SelfAware known(1)-vs-unknown(0) probe on pre-gen,
   5-fold OOF, per layer. AUROC surface. (Confirms 1.1's 0.997 under the T prompt.)
4. **Dial-on-hallucination (CPU, PRIMARY).** Apply the **T-fit** correctness dial
   (StandardScaler + LogisticRegression on ALL T post-gen vectors at the best post
   layer, no refit) COLD to: T-correct, T-wrong, and U-hallucination post-gen
   vectors. Report AUROC(T-correct vs U-hallucination) = H_U3; the 3-way dial-score
   distribution; and the within-SelfAware control AUROC(known-answered vs
   unknown-hallucination) to separate hallucination-detection from pure SelfAware
   dataset shift.
5. **Unified end-to-end frontier (CPU).** One per-item stream = T-answerable
   (correct/wrong) + SelfAware (known-answered + unknown-hallucination). Two-stage
   policy: gate abstains low P(answerable); dial vetoes low P(correct) among
   answered. Risk-coverage vs gate-only; does the dial veto cut residual
   hallucinations at matched answerable coverage?

**Confounds and caveats (bound the claim).**
- *Dataset shift:* the dial is fit on PopQA/TriviaQA and applied to SelfAware, so a
  low dial score on hallucinations could be SelfAware-OOD rather than
  hallucination-detection. Controlled two ways: (a) U-hallucination is compared
  against **T-wrong** (also wrong answers) — if hallucinations rank with/below
  T-wrong, that is consistent with hallucination-detection; (b) the within-SelfAware
  control (known-answered vs unknown-hallucination) holds the dataset fixed.
- *Known items are ungraded* (the SelfAware row manifest carries no aliases), so the
  known-answered group is "answerable attempts" not "verified-correct." Under
  forced-best-guess the model answers a known item only when it is fairly confident,
  so this group is correct-enriched but not certified; it is a directional control,
  not a gated metric.
- *Distribution shift:* forced-best-guess, as in T — establishes readability, not
  generalization to natural (un-forced) answers.

## 4. Gates and falsifier (to be LOCKED at sign-off)

**Baseline (anchored):** chance 0.50; the answerability ceiling on correctness is
~0.64 ([[amendment-o-probe-as-oracle-ceiling]]); T's in-pool dial AUROC is 0.819.

**Data sizing / adequacy precondition (checked BEFORE fitting; not a result).**
Hard floor ≥ **50 hallucinations** (unknown ∧ answered). Target as many as the pool
yields (≤ 677). Below the floor is a DATA-STAGE stop — GRPO-v2's native abstention
is too strong even under forced suppression to yield a hallucination class (itself a
reportable behavioral finding, NOT a probe verdict). Do not weaken the prompt past
the T-verbatim forced-best-guess wording to chase yield (that would break the
single-stream comparability with T).

**Metrics (threshold-free):**
- **U-G3 — PRIMARY (dial flags hallucinations):** AUROC(T-correct vs
  U-hallucination) ≥ **0.65** AND bootstrap 95% CI excludes 0.50. Bands: 0.65 useful
  · 0.75 moderate · 0.80+ strong.
- **U-G1 — gate replicates (confirmatory):** within-SelfAware known-vs-unknown
  pre-gen AUROC ≥ **0.90** under the forced-best-guess prompt.
- **U-G2 — hallucination-vs-wrong separation (descriptive, reported NOT gated):**
  where U-hallucination sits relative to T-wrong on the dial (mean dial score and
  the within-SelfAware control AUROC). Characterizes the confound, does not gate.

**SUCCESS — dial provides independent hallucination defense:** U-G3 (primary) passes
AND U-G1 passes. The deployed mechanism is gate (abstain unanswerable) → dial (both
surface trust on answered AND veto residual hallucinations).

**FALSIFIER — dial does NOT defend against hallucinations:** U-G3 AUROC < 0.65 AND
its CI includes 0.50 (i.e. the dial cannot distinguish a hallucinated answer from a
correct one). Then confident confabulation reads like correctness; the dial is a
trust dial on ANSWERABLE items only, and abstention must be carried entirely by the
gate (+ the model's native abstention). Report as a negative; do NOT open a
tweak-amendment. (This sharpens, not contradicts, the mechanism: gate-for-abstention
+ dial-for-answerable-trust.)

**No goalpost-moving.** Thresholds fixed at sign-off. The 3-way distribution, the
within-SelfAware control, the end-to-end frontier, and any τ are descriptive only;
the verdict is read on the threshold-free primary metric. An ambiguous straddle is
reported as ambiguous, not retuned.

## 5. Reporting and promotion

Exploratory, single-model, single-seed; reported **separately** from the locked
matrix. A SUCCESS completes the two-signal mechanism demonstration on one shipped
checkpoint (gate abstains → dial both surfaces trust and vetoes residual
hallucinations) and is the unified single-stream artifact the CPU stages could not
produce. Promotion to a headline claim requires a confirmatory replication (fresh
seeds / 8B / held-out) registered before running, per the firewall. Written into
Paper 3 §8 alongside Amendments S/T and the Stage 1/1.5 diagnostics.

## 6. Sign-off checklist
- [x] Prediction, falsifier, and gates stated above before any run (this doc).
- [x] Data-adequacy precondition stated (≥50 hallucinations) and ordered before fit.
- [x] Distinct mechanistic rationale vs Stage 1.5 / Amendment T (post-gen reads on
  hallucinations = dial-veto question, which no existing extraction holds).
- [x] Checkpoint resolved = identical to T (merged base + GRPO-v2 adapter on disk).
- [x] GPU launch authorization (explicit): forced-best-guess generation +
  dual-position extraction over the SelfAware pool on the clean-SFT + GRPO-v2
  checkpoint, local lane. **Authorized 2026-06-30** (smoke then full).
- [x] User sign-off recorded; gates LOCKED. **Signed 2026-06-30.**

## 7. Result

**VERDICT: SUCCESS — and strongly.** The correctness dial DOES provide independent
hallucination defense: a fabricated answer to an unanswerable question reads as the
LOWEST-trust group of all. H_U3 (primary) and H_U1 (confirmatory) both PASS; the
falsifier did NOT fire. Confident confabulation does **not** read like correctness.

**Run provenance.** Checkpoint = clean-SFT merged-16bit base + GRPO-v2 LoRA adapter
(active), forced-best-guess system prompt VERBATIM from Amendment T, greedy decode,
thinking off, seed 20260630. Pool = the 1,233 SelfAware questions from the gate's
frozen row manifest (556 known / 677 unknown). n_attempts = 1233 →
**n_answered = 397 (121 hallucinations + 276 known-answered)**, n_refused = 836
(~68% — GRPO-v2 native abstention again resists the forced prompt, but answers
SelfAware more than the PopQA/TriviaQA pool). Data-adequacy precondition cleared
with margin (≥50 hallucinations; actual **121**). Dial = the Amendment T correctness
probe (post-gen L22), T-reference groups scored OUT-OF-FOLD (honest), U groups
COLD-applied (external to the T fit). Artifacts:
`experiment/phase1/probe/amendment_u_two_signal_result.json` (tensor outputs
gitignored under `qwen3-4b-clean-sft-grpo-v2/amendment_u/`).

**Gate table (locked §4):**

| Gate | Threshold | Result | Pass |
|------|-----------|--------|------|
| U-G3 PRIMARY (dial flags hallucinations) | AUROC(T-correct vs hallucination) ≥ 0.65, CI excl 0.50 | **0.980**, 95% CI [0.968, 0.990] ("strong" band) | ✅ |
| U-G1 gate confirm | within-SelfAware known-vs-unknown pre-gen AUROC ≥ 0.90 | **0.999** (L33) under the forced-best-guess prompt | ✅ |
| U-G2 descriptive | hallucination vs T-wrong + within-SelfAware control | see below (NOT gated) | — |

SUCCESS = U-G3 AND U-G1 → **met.**

**The dial-score ordering (U-G2, descriptive — the interpretive core).** Mean dial
P(correct) by group, in rank order:

| Group | mean dial P(correct) | n |
|-------|----------------------|---|
| T-correct (answerable, right) | 0.833 | 988 |
| known-answered (SelfAware answerable attempts, ungraded) | 0.679 | 276 |
| T-wrong (answerable, wrong) | 0.353 | 500 |
| **hallucination (unanswerable, answered)** | **0.018** | 121 |

A clean monotone: hallucinations get the LOWEST trust of any group — **below even
genuinely-wrong answers to answerable questions** (0.018 vs 0.353). The model's
internal state when fabricating an answer to an unanswerable question is the
furthest of all from its correctness signature.

**Confound controlled — it is hallucination-detection, not dataset shift.** The
within-SelfAware control AUROC(known-answered vs hallucination) = **0.93**, 95% CI
[0.899, 0.957]. Holding the question pool fixed (both groups are SelfAware), the
dial still sharply separates answerable attempts (0.679) from hallucinations
(0.018). So the low hallucination score is NOT a SelfAware-OOD artifact; the dial
reads whether THIS answer is trustworthy. (And hallucinations rank below T-wrong,
the §4 pre-stated hallucination-vs-wrong check — consistent with detection.)

**Scientific takeaways.**
1. **The dial is a second line of defense, not just a trust display.** It does not
   merely rank correct-vs-wrong among answerable items (T); it actively flags
   hallucinations on unanswerable questions as least-trustworthy. The deployed
   mechanism is gate (abstain unanswerable) → dial (surface trust on answered AND
   veto residual hallucinations the gate misses).
2. **Confident confabulation does NOT read like correctness.** The falsifier's
   failure mode — fabrication carrying a confident-correct internal signature — did
   not occur; it carries the OPPOSITE signature (lowest trust of all). This is the
   first direct evidence in the program that the post-gen correctness representation
   distinguishes "I know this" from "I am making this up."
3. **The two-signal mechanism is complete on one shipped checkpoint.** Gate
   answerability AUROC ~0.999 (here, under the deployment prompt) + dial correctness
   AUROC 0.819 (T) + dial hallucination-flagging AUROC 0.980 (here), all on the
   clean-SFT → GRPO-v2 checkpoint. Both stages validated end-to-end on the same
   model. Consistent with [[two-signal-pipeline-not-fused]]: keep them as two
   orthogonal stages.

**Caveats (as pre-stated §3).** Forced-best-guess generation — establishes
readability on the deployed checkpoint, not generalization to natural (un-forced)
answers. The known-answered control group is correct-enriched but ungraded
(SelfAware carries no gold aliases), so it is a directional control, not a certified
correct set; the gated verdict rests on T-correct (graded) vs hallucination, not on
it. The unified end-to-end risk-coverage frontier (§3 step 5) is a descriptive
extension; the verdict here rests on the locked threshold-free U-G3 and the
confound-controlled within-SelfAware AUROC, both decisive.

**Promotion / next.** Exploratory, single-model, single-seed — NOT a headline claim;
promotion needs a confirmatory replication (fresh seeds / 8B / held-out) registered
before running. With the full two-signal mechanism now demonstrated on one shipped
checkpoint (S/T/U + Stage 1/1.5), the natural next steps are (a) the natural-answer
(un-forced) generalization follow-up both S and T flagged, and (b) a confirmatory
replication to promote any of this to a headline claim.
