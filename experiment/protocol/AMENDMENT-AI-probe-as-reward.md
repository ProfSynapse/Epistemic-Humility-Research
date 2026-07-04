---
amendment: AI
slug: probe-as-reward
question: >-
  Does GRPO with a probe-agreement reward (read from the policy's own
  pre-generation states by a sensor refit on the training-start checkpoint)
  beat the same reward computed from a permuted sensor on the AH congruence
  eval — i.e., can the model be trained to consult its own readout?
predictions:
  orchestrator:
    call: TRUE wins
    confidence: "~65%"
    recorded: 2026-07-03
    basis: >-
      AC showed the first use-the-signal win when the coupling was wired
      externally (+8.7pt over permuted); GRPO-v2's stuck quadrant is
      over-refusal at 77% occupancy, which the agreement reward directly
      prices; but the N/M history (scalar collapses onto the action) keeps
      confidence moderate — the reward channel may reproduce the collapse.
  user:
    call: TRUE wins
    recorded: 2026-07-03
    quote: >-
      Pre-authorize: I predict TRUE wins (recorded pre-launch via the
      overnight authorization; launch conditional on smoke green + refit
      sensor AUROC >= 0.9 + constants derived per the pre-stated rules).
outcome: null
scoreboard: null
---

# Amendment AI — Probe-as-Reward (PAR): training the model to consult its own readout

**Status: SIGNED — all three launch conditions verified 2026-07-04
(smoke v2 all-green, sensor v2 AUROC 0.9945, constants recorded §1.2–1.3);
arms launched under the user's 2026-07-03 pre-authorization (frontmatter).
Gates §2 locked as written; verdict adjudication waits for the user.**
**Tier:** A (new evidence cell; gates pre-stated before launch).
**Branch:** `amendment-ai-probe-as-reward` (off main after PR #178).
**Depends on:** AH (H-COMPLIANCE certified via A1 — the text channel does not
consult the readout, motivating the reward-channel attempt), AC (external
coupling win), T (refit-per-checkpoint), PAR design + recalibration + refit
(PR #178: mining yield, blind-sensor finding, clean-SFT sensor refit).

## 1. Design

### 1.1 Sensor (the decisive change from the original design)

The reward sensor is an L24 linear probe REFIT on the training-start
checkpoint (clean-SFT merged base), frozen for the whole run. Rationale:
the frozen raw-base AF-600 probe is blind on trained lineages (p≈1.0 on
99.9% of GRPO-v2 states; recalibration 2026-07-03, PR #178). Refit recipe:
AF-600 lineage byte-matched (StandardScaler + LogisticRegression C=1.0
max_iter=5000, known=1, p_unanswerable = sigmoid(−score)) on union-surface
clean-SFT pre-gen states (18,496 rows, gold answerable/unanswerable labels).

**REFIT RESULT v1 (2026-07-04, `par_sensor_refit.json`): L24 held-out (5-fold
OOF, rs=0) AUROC = 0.9947 vs gold ≥ the 0.9 acceptance floor.** (L20 0.9934,
L28 0.9945 fit as provenance / consensus sensitivity.) All derived statistics
use OOF scores (each row scored by a fold model that never trained on it) so
constants are not inflated by in-sample saturation.

**SENSOR v2 (pre-launch instrument fix, 2026-07-04).** Smoke v1 failed
criterion 2 (in-loop p unfaithful, max_abs_diff 0.97): the GRPO trainer
loads the checkpoint 4-BIT (QLoRA lineage recipe) while the v1 sensor was
fit on merged-16bit batch-1 states — a serving-configuration mismatch
(sensor-integrity audit read 0.815 in-loop vs 0.9947 on faithful states).
Fix extends Amendment T's refit-per-checkpoint to refit-per-serving-
configuration: re-extract the union + mining pre-gen states through the
4-bit-loaded model (batch-1, eval mode, same anchor/prompts/config) and
refit the sensor on those states. Launch conditions 2 and 3 are
RE-ADJUDICATED under sensor v2 (same rules, same floors) before any arm
starts; the in-loop reward read is a dedicated batch-1 prompt-only forward
so it is byte-reproducible against the v2 offline reference. No gate or
floor changes — this is instrument alignment before launch, with v1 numbers
retained above for provenance.

**SENSOR v2 RESULT (2026-07-04, `par_sensor_refit_v2.json`): L24 held-out
OOF AUROC = 0.9945 on the 4-bit training-configuration states → LAUNCH
CONDITION 2 RE-SATISFIED** (quantization costs the readout essentially
nothing: 0.9947 → 0.9945; L20 0.9922, L28 0.9935). Frozen sensor:
`analysis/par_sensor_refit/probes_v2/probe_L24_cleansft4bit.joblib`.
Extraction provenance: runner's `par_sensor_refit_extract_4bit.py`
(byte-identical model load to the trainer: unsloth load_in_4bit +
train-time LoRA identity + for_inference, batch-1, determinism spot-check
max_abs_diff 0.0 both surfaces).

### 1.2 Reward

Per rollout, with p = P(unanswerable) = sigmoid(−score_L24) read at the
PRE-GENERATION anchor (identical for all G rollouts of a prompt):

- R_agree = p if abstained else (1 − p)
- + w_c (answered ∧ gold-answerable ∧ correct)   [correctness bonus]
- + w_a (abstained ∧ gold-unanswerable)          [right-abstention bonus]
- format hard gate −1.0 (schema-invalid overrides everything)
- honest ignorance protected: abstain + doubting + gold-answerable earns
  plain agreement, no bonus, no penalty (gold grades EXECUTION of a
  state-consistent action, never the state).

w_c and w_a are DERIVED, not tuned: w_c = the largest grid value keeping the
answer-side flip fraction ≤ 2% on the REFIT p distribution's
gold-unanswerable stratum (the rule that produced the raw-base 0.20 cap;
grid 0.05–0.50, step 0.05); w_a symmetric unless the gold-answerable stratum
curve binds smaller.

**DERIVED CONSTANTS (LAUNCH CONDITION 3, recorded before arms start):
w_c = 0.50, w_a = 0.50.** The refit distribution is sharper than raw-base
(saturation 0.974, mean |2p−1| 0.983): gold-unanswerable-stratum flip is
1.67% at w=0.50 and gold-answerable 1.03%, so the budget never binds on the
grid and the largest-grid-w rule returns the grid maximum for both.

### 1.3 Training pool

Divergent mixture **30.5%** (smallest m with divergent advantage-mass share
≥ 25% on the refit margins: mean |2p−1| divergent 0.754 vs concordant
0.990). Divergent rows CATEGORY-STRATIFIED: no category may exceed 60% of
divergent mass — this cap BINDS (AmbigQA is ~85% of refit supply).
D-over membership is classified under the REFIT L24 sensor (the sensor the
reward actually reads): mining re-classification finds 6,518/9,397 sensor
D-over; excluding TruthfulQA (414, quarantined pending construct audit) and
v1 local remnants (14, duplicates of the locked AH pool) leaves **~6,090 new
training D-over** (ambigqa 5,183 / falseqa 896 / bigbench 11), plus union
divergent 524 (249 D-over / 275 D-under). Eval holdout: the AH divergent
pool (locked) is never trained on; additionally hold out 400
refit-classified divergent rows (category-stratified, seed 0) for the
verdict eval. FalseQA rows are train-only (NO LICENSE: question text never
enters committed files or any publication).

### 1.4 Arms

clean-SFT → GRPO-probe(TRUE sensor) vs clean-SFT → GRPO-probe(PERMUTED
sensor: p permuted within gold class, seed 0, same marginal distribution)
vs existing GRPO-v2 (reference, no new training). Same steps/LR/seed as the
GRPO-v2 lineage recipe (single seed, as the line's GRPO runs are).

### 1.5 Tripwires (during training)

- Sensor integrity: frozen refit probe AUROC vs gold on a 500-row audit set
  every 100 steps; < 0.8 → halt and flag (Goodhart on the sensor).
- Behavior floor: rolling abstain rate within [0.10, 0.90]; outside → halt.
- Degeneracy: schema-invalid fraction > 10% over any 100-step window → halt.

## 2. Gates (locked at signing)

- **AI-G0 (integrity):** both arms complete ≥ 90% of scheduled steps with no
  tripwire halt; fresh-probe falsifier at end (a probe refit on the FINAL
  checkpoint still reads gold at AUROC ≥ 0.8 — training didn't destroy the
  signal).
- **AI-G1 (primary, use-the-signal):** on the held-out divergent eval,
  TRUE-arm congruence differential (own-readout-consistent behavior, AH
  instrument with fresh-refit eval probe per Amendment T) exceeds
  PERMUTED-arm by ≥ +10pt with bootstrap CI excluding 0.
- **AI-G2 (no-regression):** TRUE arm within 5pt of GRPO-v2 on the standard
  answerable/unanswerable behavior panel (abstain-when-unanswerable,
  answer-when-answerable, correctness among answered).
- Verdict tiers: G1 pass + G2 pass = POSITIVE (readout-consulting trained);
  G1 fail + G0 pass = NULL (reward channel also doesn't couple the readout —
  strengthens the H-compliance generality); G0 fail = INSTRUMENT/RUN INVALID.

## 3. Launch conditions (pre-authorized, all three required)

1. Reward-plumbing smoke green (probe-in-loop micro-run: R varies within
   groups, advantages nonzero, tripwires demonstrably fire on synthetic
   trigger). **SATISFIED — smoke v2 (`amendment_ai_smoke_v2.json`)
   all-green with the v2 sensor: reward variance 71.9% of steps (mean group
   std 0.417); in-loop p exact-zero diff vs the persisted serving-aligned
   states (8/8); integrity audit 0.99 on the 500-row balanced set with both
   tripwire halts demonstrably firing (shuffled sensor 0.479 < 0.8; forced
   invalid 1.0 > 0.1); checkpoint save/load clean. Smoke v1
   (`amendment_ai_smoke.json`) is retained as the honest record of the
   serving-mismatch catch.**
2. Refit sensor held-out AUROC ≥ 0.9 vs gold. **SATISFIED under sensor v2:
   0.9945 on 4-bit training-configuration states (§1.1; v1 16-bit value
   0.9947 retained as provenance).**
3. w_c / w_a / mixture derived and recorded in this doc per §1.2–1.3 rules
   BEFORE the arms start. **SATISFIED under sensor v2 (same rules):
   w_c = w_a = 0.50 (gold-unanswerable stratum flip 1.3% at grid max —
   budget still unbinding); mixture 29.0%; pool = 2,902 train divergent
   (ambiguous capped at 60%: 1,741 / false_premise 833 / unsolved_other
   328), 16,345 concordant, 400-row category-stratified holdout (seed 0);
   TruthfulQA excluded (now audit-CONFIRMED: 0/82 sampled rows genuinely
   unanswerable — `amendment_ai_truthfulqa_audit.md`); v1 values (mixture
   30.5%, pool 2,909) superseded.**

Any condition failing ⇒ no launch; doc holds as DRAFT for morning review.
