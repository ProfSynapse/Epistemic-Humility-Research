---
amendment: S
slug: correctness-confidence-probe
question: >-
  Is per-attempt correctness linearly readable, and is it read more
  strongly after the answer than before (self-eval gain)?
predictions:
  orchestrator:
    call: >-
      post-gen beats pre-gen; correctness readable, self-eval gain positive
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  SUCCESS — post-gen AUROC 0.834, self-eval gain +0.065 (CI excludes 0);
  G1+G2 pass, G3 misses by 0.001 (not a green-light gate).
scoreboard: null
---

# Amendment S — Correctness-Confidence Probe (post- vs pre-generation readout)

**Status:** RESOLVED — **SUCCESS** (run + scored 2026-06-30; see §7). Signed
2026-06-30 ("1 approved 2 authorized"). Tier-2
exploratory cell (new evidence, falsifier pre-stated; reported separately from the
locked PROTOCOL v0.3 matrix). Gates, primary metrics, and falsifier below are LOCKED
as of sign-off — no goalpost-moving after the result. GPU authorized for the Stage-2
free-answer generation + dual-position extraction on the Qwen3-4B Instruct base.

**Instrument rationale:** Tier-2 Amendment per
`experiment-runner/reference/amendment-vs-lab-notebook.md` (decision Q2). It
introduces a NEW eval/extraction cell reported as evidence, and it carries a
distinct mechanistic rationale from every prior amendment: all of O/P/Q/M/N/R
target the **answerability** axis read **pre-generation** (end-of-prompt, "do I
know this"). This cell targets **per-attempt correctness** read **post-generation**
("is the answer I just produced right") — a different signal at a different
position. Distinct mechanism ⇒ a new amendment, not tier-3 tuning.

**Compute:** GPU — a NEW free-answer generation + hidden-state extraction pass
(cached data is provably underpowered for correctness; see §1.3). No training run.
Launch requires explicit user approval per operator discipline.

**Model/surface:** Qwen3-4B **Instruct base** (pre-abstention) for the pilot;
hard open-domain QA with gold. Single-model, single-seed, exploratory.

## Revision history
- **R1 (DRAFT, 2026-06-30):** initial pre-registration; awaiting user sign-off and
  GPU authorization.
- **R2 (SIGNED, 2026-06-30):** gates anchored to the in-run pre-gen baseline (G2
  primary; G1 floor 0.70; generous sizing); Stage-0 data check GREEN. User signed
  off and authorized the Stage-2 GPU run ("1 approved 2 authorized"). Gates LOCKED.
- **R3 (RESOLVED, 2026-06-30):** Stage-2 run executed (1836 answered, 500/1336),
  scored against the locked gates. SUCCESS: G1 PASS (post-AUROC 0.834), G2 primary
  PASS (delta +0.065, CI [0.040, 0.090]); G3 misses by 0.001 (not a green-light
  gate). Result written to §7; no goalpost moved. See §7 for full disposition.

## 1. Facts this builds on

### 1.1 The user-facing goal (this is what the cell serves)
The deliverable is a **surfaced confidence the user can threshold to decide how
much to trust a response.** Preferred behavior: abstain ("I don't know") on true
unknowns; accepted compromise: answer with a **low** surfaced confidence on
borderline cases. The surfaced number must therefore track **whether the specific
answer is correct**, not merely whether the topic is answerable.

### 1.2 Two signals, two maturities
- **Answerability (signal 1, abstention gate):** VALIDATED. A linear probe ranks
  known vs unknown at AUROC ≈ 0.997 ([[amendment-o-probe-as-oracle-ceiling]]) and
  transfers cross-dataset cold at 0.983 ([[amendment-p-xdataset-transfer]]). This
  drives the "say I don't know" gate; it is reused, not re-derived here.
- **Correctness (signal 2, the surfaced dial):** UNVALIDATED. O's only non-circular
  number — answered-knowns correct-vs-wrong AUROC — was **0.640**, and even that was
  computed on **27 wrong examples** (noise; see correctness-probe-underpowered memo).
  Whether a correctness signal is linearly readable at useful strength is the open
  question this cell answers.

### 1.3 Why this needs a new GPU surface (not cached data)
A correctness probe cannot be powered on any cached extraction: abstention-trained
arms answer only when ~94% likely right (clean-SFT SelfAware = 407 correct / 27
wrong), and every other cached extraction is labeled by *answerability*, not
single-attempt correctness. The fix, stated in that memo: a surface where the
model **answers a lot AND errs a lot** — the *instruct* base (pre-abstention) on a
hard QA set, or re-generation with abstention suppressed. The Instruct base is the
cheapest such surface and is the pilot here.

## 2. Hypothesis and prediction

**H_S (correctness is readable, and self-evaluation helps).** A linear probe on
hidden states discriminates correct vs wrong answered attempts, and reads this
**more strongly after the model has generated its answer than before**:

- **H_S1 (signal exists):** best post-generation correctness-AUROC ≥ **0.70**
  (5-fold CV, out-of-fold; useful floor — see §4 bands).
- **H_S2 (self-eval gain — THE BET, primary):** best post-generation
  correctness-AUROC exceeds the best pre-generation (end-of-prompt)
  correctness-AUROC by ≥ **+0.05** (delta CI excludes 0).

Rationale: pre-generation, the only available signal is prospective answerability
("do I know this topic"), which caps near 0.64 because topic-knowledge ≠ this
answer is right. Post-generation, the residual stream has *seen the produced
answer* and can carry a self-evaluation signal (the P(True) / Kadavath et al.
hypothesis), never tested in this program.

If H_S holds, a surfaced correctness-confidence dial is achievable by linear
readout; the two-signal mechanism (answerability gate + correctness dial) becomes
buildable on the deployment checkpoint (follow-up). If H_S fails, the model does
not linearly represent its own correctness — itself a publishable negative.

## 3. Method (GPU extraction + CPU probe)

**Surface (resolve loaders/gold in §6 before running):** a hard open-domain QA set
with gold answers that makes the Instruct base err substantially — PopQA (long-tail
entities) and/or TriviaQA unfiltered no-context, pooled if needed to reach the §4
data-adequacy precondition. Correctness scored against gold aliases with the
existing eval scorer.

**Procedure:**
1. **Free-answer generation (GPU).** Greedy-decode one answer per question on the
   Instruct base, abstention NOT suppressed-by-prompt is unnecessary (the instruct
   base is pre-abstention and answers freely). Label each attempt correct/wrong vs
   gold.
2. **Dual-position hidden-state extraction (GPU).** For every answered row, extract
   residual hidden states at BOTH read positions across a layer band (all 37 layers,
   or at minimum L20–L36):
   - **pre-gen:** the generation-anchor token (end-of-prompt, `add_generation_prompt
     =True`; the cos-0.9998 faithful position from the Amendment R / session 0029
     render fix — reuse it, do not read a full-conversation token);
   - **post-gen:** the final answer token (end of the generated answer, before EOS).
3. **Probe fit (CPU).** Logistic probe on correct(1)/wrong(0), 5-fold CV
   out-of-fold, fit independently per (layer × position). Report the AUROC surface.
4. **Surface + score (CPU).** Surfaced confidence = probe probability. Report
   correctness-AUROC, ECE-vs-correctness, and a selective-prediction curve
   (accuracy vs coverage) for the best post-gen (layer, position).

**Checkpoint-consistency.** Pilot is self-contained on the Instruct base (probe,
generations, and hidden states all from `unsloth/Qwen3-4B-bnb-4bit` instruct). No
claim is made across checkpoints. Porting the validated probe to the deployment
(clean-SFT) checkpoint with abstention suppressed is a SEPARATE follow-up amendment,
explicitly out of scope here.

## 4. Gates and falsifier (to be LOCKED at sign-off)

**The baseline (anchored, not guessed).** Existing correctness-ranking AUROCs in
the program: chance 0.50; model's own verbalized confidence (M) 0.504; base emitted
scalar 0.559; **pre-generation answerability probe read as correctness (O) ≈ 0.64**
(noisy, 27 wrong). The principled baseline is therefore **the run's own
pre-generation read (~0.64)** — the "free" number the already-validated
answerability probe gives with no new idea. The novel question is whether reading
*after* the answer beats it, so the baseline is measured in-run, not assumed.

**Data sizing.** Data is abundant (PopQA 14.3k + TriviaQA-gold 11.3k, with gold
aliases; PopQA `s_pop` gives a difficulty gradient that guarantees a wrong class on
long-tail entities). **Target ≈ 500 correct AND ≈ 500 wrong** answered attempts so
the post-vs-pre delta has tight CIs.

**Data-adequacy precondition (checked BEFORE fitting; not a result).** Hard floor:
≥ **150 correct** AND ≥ **150 wrong**. Below this is a data-stage stop (pool more
datasets / more questions), NOT a probe verdict — we do not fit an underpowered
probe and call the line dead (the 27-wrong lesson).

**Metrics (threshold-free):**
- **G2 — PRIMARY (self-eval gain, the scientific question):** best post-gen
  correctness-AUROC − best pre-gen correctness-AUROC ≥ **+0.05**, AND the delta's
  bootstrap/DeLong 95% CI excludes 0. Baselined on the run's own pre-gen read.
- **G1 — usefulness floor:** best post-gen correctness-AUROC ≥ **0.70** (5-fold CV,
  out-of-fold) — conservatively above chance (0.50), emitted (0.55), and the free
  answerability read (0.64). Descriptive bands: 0.70 useful · 0.75 moderate · 0.80+
  strong.
- **G3 — calibration:** ECE of surfaced confidence vs correctness < **0.15** at the
  best post-gen (layer, position).

**SUCCESS — correctness dial achievable:** G2 (primary) AND G1 pass (G3 reported; a
clean selective-prediction curve strengthens but is not required for the
green-light).

**FALSIFIER — kills the correctness-readout line on this model:** best post-gen
correctness-AUROC < 0.70 **AND** post−pre ≤ +0.05 (no self-eval gain). The model
does not linearly represent its own correctness any better after answering than
before; a surfaced correctness-confidence dial is not achievable by linear readout
here. Report as a negative; do NOT open a tweak-amendment — escalate to a richer
readout only with a distinct mechanistic rationale.

**No goalpost-moving.** Thresholds above are fixed at sign-off. The
selective-prediction curve and any τ are descriptive only; the verdict is read on
the threshold-free metrics. Ambiguous straddle (e.g. G1 passes, G2 marginal) is
reported as ambiguous, not retuned.

## 5. Reporting and promotion

Exploratory, single-model, single-seed; reported **separately** from the locked
matrix. A success is a **lead** that motivates (a) the deployment-checkpoint port
(clean-SFT, abstention suppressed) and (b) the full two-signal mechanism
(answerability gate + correctness dial). Promotion to a headline claim requires a
confirmatory replication (fresh seeds / 8B / held-out) registered before running,
per the firewall. Written into Paper 3 §8 as evidence on whether trustworthy
surfaced confidence is latently readable.

## 6. Sign-off checklist
- [x] Prediction, falsifier, and gates stated above before any run (this doc).
- [x] Data-adequacy precondition stated (≥150/≥150) and ordered before the fit.
- [x] Checkpoint-consistency: Instruct-base self-contained pilot; deployment port
  scoped as a separate follow-up.
- [x] Distinct mechanistic rationale vs prior amendments (correctness/post-gen, not
  answerability/pre-gen).
- [x] Stage-0 data check (2026-06-30, CPU): PopQA (`datasets/popqa/test.jsonl`,
  14,267 rows, gold `possible_answers`) and TriviaQA
  (`datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl`, 11,313 rows, gold
  `aliases`) present with gold for alias-grading; PopQA `s_pop` gradient guarantees
  a wrong class on long-tail entities. Ample to clear ≥150/≥150 and the ~500/500
  target. Actual Instruct-base error rate measurable only at generation (Stage 2).
- [x] GPU launch authorization (explicit): Stage-2 free-answer generation +
  dual-position extraction on the Qwen3-4B Instruct base, local lane. Authorized
  2026-06-30 ("2 authorized").
- [x] User sign-off recorded: 2026-06-30, "1 approved 2 authorized". Gates LOCKED.

## 7. Result

**VERDICT: SUCCESS** (run 2026-06-30, Qwen3-4B Instruct base, single seed). The
primary self-eval gate G2 and the usefulness floor G1 both pass; the
green-light condition (G2 AND G1) is met. Reported separately from the locked
matrix; this is an exploratory lead, not a headline claim.

**Run provenance.** Free-answer greedy generation + dual-position extraction on
`unsloth/Qwen3-4B-bnb-4bit` (Instruct base, no adapter), thinking off,
answer-encouraging neutral system prompt (recorded in the run manifest), PopQA +
TriviaQA-gold pool (25,580 questions, shuffled seed 20260630), graded by the
verbatim Cheng alias scorer. `n_answered = 1836` → **500 correct / 1336 wrong**
(error rate ≈ 73% on the long-tail-heavy pool — the "answers a lot AND errs a
lot" surface §1.3 required). Data-adequacy precondition cleared (≥150/≥150;
actual 500/1336). Probe: 5-fold stratified CV logistic on standardized hidden
states, out-of-fold, fit independently per (position × layer). Full AUROC surface
+ verdict: `experiment/phase1/probe/amendment_s_stage2_result.json`. Scripts:
`amendment_s_correctness_probe_extract.py` (GPU) +
`amendment_s_correctness_probe_score.py` (CPU).

**Headline numbers (vs LOCKED gates).**

| Metric | Value | Gate | Result |
|---|---|---|---|
| best **post-gen** correctness-AUROC | **0.834** (L20) | G1 ≥ 0.70 | **PASS** (strong band, > 0.80) |
| best **pre-gen** correctness-AUROC | 0.769 (L22) | — (in-run baseline) | — |
| **post − pre delta** | **+0.065** | G2 ≥ +0.05 | **PASS** |
| delta bootstrap 95% CI (2000×, paired over rows) | **[0.040, 0.090]** | G2: excludes 0 | **PASS** (lower bound > 0) |
| ECE(best post) | 0.151 | G3 < 0.15 | **FAIL by 0.001** (not a green-light gate) |

**SUCCESS condition (§4): G2 (primary) AND G1 → both PASS → green light.** G3 is
reported, not required for the green light (§4 verbatim); it misses by 0.001, a
calibration-of-the-readout matter (post-hoc Platt/temperature scaling), not a
signal-existence problem — AUROC is threshold-free and clears strongly. No
goalpost was moved: the verdict is read on the threshold-free primary metrics
exactly as locked at sign-off.

**Selective-prediction curve (best post-gen, L20).** Accuracy rises from 27.2%
(full coverage) → 34.9% @75% → 47.2% @50% → 64.9% @25% → **75.5% @10%**. The
surfaced confidence is a usable trust dial: thresholding to the top-confidence
decile nearly triples answer accuracy. (Descriptive; strengthens but is not
required for the verdict.)

**Scientific reading.**
1. **Correctness IS linearly readable** at useful strength (0.834) — the open
   question of §1.2 is answered yes for this model.
2. **Self-evaluation helps (THE BET, confirmed).** Reading *after* the answer
   beats reading *before* by +0.065 with a CI excluding 0 — the first positive
   evidence in this program for the P(True)/Kadavath self-eval hypothesis. The
   gain is real but modest; the larger result is the absolute post-gen readability.
3. **The correctness signal peaks mid-network (L19–L24, post ≈ 0.82–0.83), not
   late.** It sits earlier than the L35 caution gate and the late layers
   (L34–L36 post ≈ 0.79) read slightly weaker — correctness is represented before
   the answer/abstain decision layer, distinct from both the answerability axis
   and the caution gate.

**Promotion / next.** Exploratory, single-model, single-seed — NOT promoted to a
headline claim. This is a lead that motivates (a) the deployment-checkpoint port
(clean-SFT, abstention suppressed) and (b) the full two-signal mechanism
(answerability gate + correctness dial), each a separate registered amendment.
A G3 follow-up (temperature-scale the readout, re-measure ECE) is a cheap CPU
refinement on the same extraction. Promotion requires a confirmatory replication
(fresh seeds / 8B / held-out) registered before running, per the firewall.
