---
amendment: P
slug: xdataset-probe-transfer
question: >-
  Does an answerability probe fit on KUQ transfer cold to SelfAware,
  showing Amendment O's ceiling is not an in-distribution-CV artifact?
predictions:
  orchestrator:
    call: partial transfer, AUROC 0.80-0.92, margin +40-75pt
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  SUCCESS — cold transfer AUROC 0.9834 (near in-distribution ceiling),
  action margin +89.6pt; beat the pre-stated partial-transfer call. Axis
  not dataset-specific; still not correctness-ranking.
scoreboard: null
---

# Amendment P — Cross-Dataset Answerability-Probe Transfer Test

**Status:** SIGNED 2026-06-29 (user: "proceed"). Tier-2 exploratory cell
(new evidence, falsifier pre-stated; reported separately from the locked PROTOCOL
v0.3 matrix). Gates, primary metric, and falsifier below are LOCKED on sign-off — no
goalpost-moving after the result.
**Instrument rationale:** Tier-2 per
`experiment-runner/reference/amendment-vs-lab-notebook.md` — it produces a result
*reported as evidence* (whether the head's premise survives a cold cross-dataset
transfer) and carries a real falsifier. It is the natural follow-up named in
Amendment O §7 caveat 1 ("in-distribution CV ceiling, not a transfer test"). Kept as
a NEW amendment rather than an O revision so O's SUCCESS record (the in-distribution
ceiling) stays immutable and this falsifier is clean.
**Compute:** CPU-only re-analysis of cached artifacts — **no training run, no new GPU
extraction.** Launch still requires explicit user approval.
**Model/surface:** Qwen3-4B clean-SFT→GRPO-v2 (seed 1) checkpoint. Single-model,
single-seed, exploratory.

## Revision history
- **R1 (2026-06-29, SIGNED):** initial pre-registration; signed off as-is by the user
  ("proceed"). CPU-only run authorized.

## 1. Facts this builds on

1. Amendment O (PR #120) demonstrated a **readout ceiling**: a linear probe of the
   internal axis, fit by 5-fold CV **on SelfAware itself**, drives a policy passing
   all gates (transfer AUROC 0.997, action margin +95 pts). Its load-bearing caveat:
   the probe is fit *in-distribution*; it shows a passing policy is **latent in the
   SelfAware representation**, not that a probe fit on a **different** distribution
   transfers to SelfAware.
2. The deployed confidence head would be trained on a **training** QA distribution
   and read out on the **reporting** surface (SelfAware). If the answerability axis
   is dataset-specific, that head needs an OOD-robust target before the engine change
   is justified by O's ceiling.
3. Cached, checkpoint-consistent extractions exist to test this **without any GPU
   run**: on the grpo-v2 checkpoint, both **KUQ** (known/unknown gold, 600/400) and
   **SelfAware** (known/unknown gold, 556/677) are extracted with h_base at all
   layers. Existing `kuq_vs_selfaware_caution_transfer_L35.json` measured only the
   *caution-direction cosine* (0.185, "partial-shared") — a direction-geometry
   statistic, **not** the answerability-probe transfer AUROC, which is what this cell
   measures.

## 2. Hypothesis and prediction

**H_P (cross-dataset transfer).** An answerability probe fit on KUQ (known/unknown)
and applied **cold** to SelfAware ranks SelfAware known vs unknown at AUROC ≥ 0.70.

**Pre-stated prediction (not a gate; recorded to avoid hindsight):** **PARTIAL
transfer.** I expect transfer AUROC comfortably above the 0.70 floor but **materially
below** O's in-distribution 0.997 ceiling — best guess **0.80–0.92** — and the
fixed-τ action margin to shrink from O's +95 pts toward roughly +40–75 pts. Rationale:
answerability is a strong, fairly global feature (so it should clear 0.70), but the
cross-dataset caution-direction cosine was only 0.185, so the geometry only partially
aligns and a cold operating point will be miscalibrated by the KUQ→SelfAware base-rate
shift (60%→45% known).

## 3. Method (CPU-only; reuses cached artifacts)

Script: `experiments/xdataset-probe-transfer/probe_xdataset_transfer.py`.
- **FIT (train distribution):** KUQ grpo-v2 extraction
  `.../qwen3-4b-clean-sft-grpo-v2-seed1-kuq/hidden_states_kuq_clean_sft_grpo_v2_full`,
  h_base, layer 35. StandardScaler + LogisticRegression(C=1.0) on **all** rows.
- **TEST (cold, reporting surface):** SelfAware grpo-v2 extraction
  `.../qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full`,
  h_base, layer 35. Apply the KUQ-fit scaler+probe cold → factual_p; compute transfer
  AUROC, ECE, std, and the oracle action at τ.
- **Checkpoint-consistency:** FIT and TEST are the **same** (grpo-v2) checkpoint, so
  the residual-stream feature space is shared. (Note: this is **not** the clean-SFT
  checkpoint O used; see §5. No claim is made across mismatched checkpoints.)
- **Sanity:** in-distribution 5-fold CV AUROC on each set (expect KUQ ~0.97 /
  SelfAware ~0.99) to confirm both feature spaces are healthy before reading transfer.
- **Layer 35 fixed a priori** (paper's reported best layer, O's layer). A full
  `--scan-layers` transfer curve is reported **descriptively only**; the verdict is
  read at L35. h_lora reported descriptively if informative; primary is h_base.

## 4. Gates and falsifier (pre-registered)

**PRIMARY (locked) — threshold-free, isolates transfer of the axis:**
- **transfer AUROC (KUQ-fit → SelfAware appropriateness) ≥ 0.70** — the falsifier
  line. Below 0.70 ⇒ the axis does **not** transfer across datasets.
- ECE < 0.30 on the cold scores.

**SECONDARY (descriptive only — NOT pass/fail):** oracle action at primary τ = 0.5
(native cutoff, not tuned): over_refusal ≤ 67.5, refusal_recall ≥ 82.0, action margin.
These are reported but **not** verdict-bearing, because a fixed τ across the
KUQ→SelfAware base-rate shift conflates *threshold* calibration with *axis* transfer;
the honest transfer number is the threshold-free AUROC. A τ-sweep is descriptive only
and may **not** be used to manufacture a pass.

**SUCCESS — transfer holds:** transfer AUROC ≥ 0.70 (and, encouragingly, near the
in-distribution ceiling). The axis is not dataset-specific; O's latent-ceiling premise
survives a cold cross-dataset transfer and the head is further de-risked.

**FALSIFIER — premise dataset-specific:** transfer AUROC < 0.70. The answerability
axis is substantially dataset-specific; O's ceiling does **not** imply a deployable
readout, and the confidence head needs an OOD-robust target (or the obstruction is
upstream) before the engine change is justified by a latent ceiling.

**Ambiguity rule:** if transfer AUROC lands marginal (≈0.70) or clears the floor but
falls far short of the in-distribution ceiling, report it as **partial transfer** with
the explicit number; do not retune τ, layer, or source to force a cleaner verdict.

## 5. Reporting and promotion

Exploratory, single-model, single-seed. Reported **separately** from the locked
matrix, into Paper 3 §8/§9 as the cross-dataset robustness check on the O ceiling.
**Checkpoint caveat (pre-stated):** this runs on the grpo-v2 checkpoint (the only one
with both KUQ and SelfAware cached), not the clean-SFT checkpoint O used. It tests
*cross-dataset* transfer on a trained checkpoint; the *checkpoint-matched* version
(clean-SFT TriviaQA→SelfAware) would require a new GPU extraction and is a separately
authorizable follow-up if this cheap test is encouraging. A success is a **lead**, not
a headline claim; promotion requires the engine experiment plus replication.

## 6. Sign-off checklist
- [x] Prediction, falsifier, and gates stated above before any run (this doc).
- [x] CPU-only; no GPU extraction or training launched without separate approval.
- [x] User sign-off recorded: 2026-06-29, "proceed" (+ CPU run authorized).

## 7. Result

**VERDICT: SUCCESS — transfer holds, near the in-distribution ceiling. Falsifier
dead.** Run 2026-06-29, CPU-only, `probe_xdataset_transfer.py`, grpo-v2 checkpoint,
L35. FIT = KUQ (n=1000, 600 known / 400 unknown); TEST = SelfAware (n=1233, 556 known
/ 677 unknown), cold.

**PRIMARY (locked) — h_base L35:**
- **transfer AUROC (KUQ-fit → SelfAware, cold) = 0.9834** (falsifier ≥ 0.70 ✓; not
  remotely approached). **ECE 0.0358** (< 0.30 ✓). factual_p std 0.478.
- In-distribution CV sanity: KUQ 0.9639, SelfAware 0.9966 — both feature spaces
  healthy, and the cold transfer (0.983) sits **essentially at** the SelfAware
  in-distribution ceiling. The axis is **not** dataset-specific.

**Robustness — h_lora L35:** transfer AUROC **0.9837**, ECE 0.0377 (CV 0.9642 /
0.9967). The two residual-stream sources agree to within 0.0003; the result does not
depend on the source choice.

**SECONDARY (descriptive, fixed τ = 0.5, h_base):** even with a cold, un-recalibrated
threshold across the KUQ→SelfAware base-rate shift, the oracle action policy nearly
matches O: over_refusal 4.68%, refusal_recall 94.24%, answer_rate known 95.32% /
unknown 5.76%, **action margin +89.56 pts** (vs O's in-distribution +95.14). The
predicted threshold miscalibration barely materialized — the cold operating point is
already good.

**Prediction vs outcome:** I pre-stated PARTIAL transfer at 0.80–0.92 with the margin
sagging to +40–75. The actual transfer (0.983, margin +89.6) **beat** that — I
under-estimated. The lesson is a real one: the cross-dataset **caution-direction
cosine** is only 0.185 ("partial-shared"), but the **answerability readout** transfers
almost fully. A steering *direction* and a linear *readout* of the same axis are
different objects — direction-geometry disagreement across datasets does **not** imply
the readout fails to transfer. I anchored on the wrong statistic.

**Caveats (do not overclaim):**
1. **Checkpoint, not the one O used.** This is grpo-v2 (the only checkpoint with both
   KUQ and SelfAware cached), not clean-SFT. It establishes cross-*dataset* transfer
   on a trained checkpoint; the checkpoint-matched clean-SFT TriviaQA→SelfAware
   version would need a GPU extraction (separately authorizable). The two in-dist CV
   sanity numbers reproducing the paper's ~0.97/~0.99 give confidence the grpo-v2
   feature space is the same axis, but strictly the claim is checkpoint-local.
2. **KUQ and SelfAware are both "is this answerable?" datasets.** Transfer here is
   across two *unanswerable-question* benchmarks, which share construct. It is
   stronger evidence than in-distribution CV (O) but weaker than transfer from a
   generic *factuality/known* training distribution (e.g. TriviaQA p_correct bands)
   to SelfAware. The latter is the deployment-faithful test and remains future work.
3. **Answerability, still not per-attempt correctness.** As in O, this measures the
   appropriateness/answerability axis; the correctness-ranking question (O's 0.64) is
   untouched here.

**So what.** Combined with O, the head's premise now survives the obvious failure
mode: the calibrated axis is **not** an in-distribution-CV artifact — a probe fit on a
*different* QA dataset reads SelfAware at 0.983 cold. The "signal is there, only the
readout is missing" story holds across datasets, not just within one. This further
de-risks the confidence-head engine change. It does **not** retire (a) the
checkpoint-matched / generic-train-distribution transfer test, or (b) the
correctness-vs-answerability gap. Written into Paper 3 §8/§9 as the cross-dataset
robustness check on the O ceiling. Exploratory, single-model/single-seed; reported
separately from the locked matrix; not a headline claim.

Artifacts: scorer `experiments/xdataset-probe-transfer/probe_xdataset_transfer.py`; raw result
JSON written to scratch (h_base + h_lora), numbers transcribed here are the tracked
record. The gitignored extraction-dir default output path is not redistributed.
