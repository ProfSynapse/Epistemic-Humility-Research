---
amendment: AN
slug: selected-setpoint-regulator
status: >-
  SIGNED 2026-07-05 (user recorded predictions "I agree on all passing" after
  reviewing the operating point, derived gates, and the entrenched-answer
  caveat; gates in section 4 LOCKED as drafted). One amendment = one branch =
  one PR at resolution.
question: >-
  Does propensity-SELECTED, caution-ACTUATED regulation convert residual
  confabulations into refusals at low collateral on the AI-TRUE checkpoint,
  i.e. does writing the caution setpoint UP (AC's proven knob) on rows flagged
  by the confabulation-propensity readout (AL's proven sensor) reach the confab
  cloud where pushing along the propensity direction itself (AL) did nothing?
predictions:
  orchestrator:
    calls:
      AN-G1: PASS (~70%)
      AN-G2: PASS (~40%)
      AN-G3: PASS (~40%)
    recorded: 2026-07-05
    basis: >-
      G1 leans PASS because AC's only direct evidence on answering rows is
      0/7 flips under positive gain (answers resist) and just 4 corrects are
      exposed. G2/G3 sit under 50% for the same reason inverted: AN's central
      bet is that the caution setpoint can flip ENTRENCHED answering rows
      (the residual confabs), and the 0.16 compliance feeding the G2 floor
      was measured as refusal RESTORATION (coupled vs ablate), not as
      flipping established answers; if true flip compliance is half the
      estimate, expected kills fall to ~3.8 versus a floor of 5. G3 mostly
      rides G2: any kills that do happen should be selective.
  user:
    calls:
      AN-G1: PASS
      AN-G2: PASS
      AN-G3: PASS
    recorded: 2026-07-05
    quote: >-
      "I agree on all passing" - all three gates called PASS, taking the
      actuation bet at full confidence again where the orchestrator sits at
      40% on G2/G3 (same disagreement shape as AL, opposite mechanism: there
      the user bet on a new knob; here the bet is the proven knob reaching a
      new population).
outcome: >-
  NULL (falsifier fired), resolved 2026-07-06. AN-G1 PASS (collateral 0 of
  allowed 2) but VACUOUS: zero effect on the write means zero collateral by
  construction, not a real honesty guarantee, since the corrects it was
  guarding were never actually at risk. AN-G2 MISS (0 of 116 baseline confabs
  killed against a floor of 5; descriptive dose ladder g=+1/+2/+3 kills
  0/0/0 of the 47 flagged confabs). AN-G3 MISS (primary-minus-control kill
  diff 0, 1,000-resample row bootstrap 95% CI [0.0, 0.0] against a floor of 5
  with CI excluding zero). Primary arm: 244 flagged rows (47 confabs, 4
  corrects, 11 wrong, 18 answerable-refused, 164 unanswerable-refused); all 47
  flagged confabs land in confab_to_different_confab, never a refusal.
  Descriptive bidirectional arm: the same actuator at g=-2 de-refuses 0 of
  114 baseline answerable-refused rows. Smoke readback confirms the write
  lands precisely on-axis (mean observed setpoint 43.98 vs commanded 44.26,
  max abs error 0.58 against sigma 22.13; unflagged rows show zero shift),
  ruling out an injection-fidelity failure. caution_perp, reached this
  precisely on propensity-flagged rows, still does not carry the
  fabricate-vs-refuse decision: it is a correlate of the caution behavior it
  was fit on, not a general-purpose lever. Closes the imprecise-injection
  escape (already ruled out by AL, reconfirmed here) and the wrong-actuator
  escape (AC's actuator independently moves behavior on its own population)
  that earlier write-side nulls left open; consistent with, not contradicted
  by, the AF/AC/AG prime-channel wins, which are input-side rather than
  write-side.
scoreboard: >-
  AN-G1 both hit (pass is vacuous, so this is not a substantive win for
  either side). AN-G2/AN-G3, the central bet: the user called PASS at full
  confidence ("I agree on all passing"); the orchestrator called PASS but at
  only ~40% (implied lean toward miss). Both literal PASS calls missed; the
  orchestrator's sub-50% confidence was the directionally correct lean, same
  disagreement shape as AL and explicitly anticipated in the recorded basis
  ("same disagreement shape as AL, opposite mechanism: there the user bet on
  a new knob; here the bet is the proven knob reaching a new population").
  Score LOSS/WIN (user-orchestrator), same scoring convention applied to AL's
  sub-50%-counts-as-a-lean G2/G3 calls. Tally 3-4-2.
---

# Amendment AN - Selected-setpoint regulator on the AI-TRUE checkpoint

**Status:** SIGNED 2026-07-05; gates in section 4 LOCKED.
**Tier:** A (new evidence cell; causal intervention; gates pre-stated).
**Branch:** `amendment-an-selected-setpoint-regulator` (one amendment, one
branch, one PR at resolution).
**Depends on:** AC (`AMENDMENT-AC-doubt-regulated-caution.md`, PASS - proved
the activation-level regulator: sensor = per-row readout, actuator =
erase-and-write setpoint on the caution_perp coordinate,
`h' = h - (h.c_hat)c_hat + g_i*sigma_c*c_hat`, external control law) and AL
(`AMENDMENT-AL-radial-anti-propensity-steering.md`, resolved NULL - proved the
propensity direction is a SENSOR, not a knob: pushing along it moves the
readout the commanded amount and changes no behavior, 0 of 116 confab kills,
injection verified precise).
**Run lane:** LOCAL 3090 only. No cloud spend.

## 1. Motivation and strategic position

AC and AL together bracket the regulator design space and each resolved one
axis of it:

- **AC (the actuator works).** On the GRPO-v2 checkpoint, erasing the model's
  own caution gate and writing a doubt-proportional setpoint on the
  caution_perp coordinate carried information beyond deleting the gate (coupled
  vs permuted +8.7pt, CI [+5.6, +12.0]). The setpoint write is a real knob: its
  dose-response is monotone (refusal 0.000 at g=-2 rising to 0.800 at g near
  +2), and the incremental refusal it induces over erase-only is +14.4pt at
  g in [1.0, 1.5) and +16.0pt at g in [1.5, 2.0) (computed from the AC coupled
  vs ablate per-row rows.jsonl, this session). Writing the caution coordinate
  UP pushes a row toward refusal.
- **AL (the propensity direction is a sensor, not a knob).** On the AI-TRUE
  checkpoint, subtracting the confabulation-propensity direction from the
  residual stream moved the propensity readout by exactly the commanded amount
  (pushed-anchor projection -2.7133 vs commanded -2.7110) and changed no
  behavior: 0 of 116 baseline confabs killed, primary-minus-control kill diff 0
  with bootstrap CI [0.00, 0.00]. The propensity direction reads the confab
  cloud but does not actuate the fabricate-vs-refuse choice.

AL tested PROPENSITY-selected, PROPENSITY-actuated (select by the readout, push
along the same direction) and got a clean null on the actuation half. It did
NOT test the surviving combination, **PROPENSITY-selected, CAUTION-actuated**:
flag rows with the sensor that has real reach into the confab cloud, then
correct them with the knob that is proven to move behavior. That is AN.

The propensity readout genuinely separates the confab cloud from the honest
answers: at baseline on the AI-TRUE A0 surface, confabs sit high on
propensity-z (mean +0.669, median +0.656) while correct answers sit low
(mean -0.954, median -0.836). So a high-propensity flag preferentially catches
confabs and largely spares corrects (section 4 table). The caution setpoint
write is the AC-proven behavioral lever. AN asks whether pairing the reaching
sensor with the moving actuator closes the loop AL's same-direction pairing
could not.

If it passes, the program has its first SELECTIVE fabrication-suppression cell:
a sensor with reach plus an actuator with force, composed into one inference-
time regulator, and the escalation ladder (multi-seed replication, then a
propensity-gated caution-setpoint training channel) opens. If G2 and G3 both
miss, the caution setpoint does not reach the confab cloud even when aimed at
it by the reaching sensor, and the regulator needs a different sensor-actuator
pairing - a publishable boundary either way. A G1 bust with G2 pass is a
PARTIAL: the mechanism reaches but the selector is too coarse to spare honest
answers.

## 2. Hypotheses

- **H-reach:** the caution setpoint write, applied to propensity-flagged rows,
  is causally upstream of the fabricate-vs-refuse choice, so writing the
  setpoint UP (g = +2, clipped) on flagged rows converts residual confabs into
  refusals at or above the floor derived from AC's observed setpoint compliance
  (section 4).
- **H-select:** the effect runs through the propensity selection and the
  caution write together, so a permuted-flag control (same row count, same
  write, shuffled flag assignment) kills materially fewer confabs.
- **H-cheap:** because the propensity flag concentrates on confabs and spares
  correct answers (only 4 of 90 corrects flagged at the operating point),
  collateral on correct answers stays within the pre-registered ceiling.

## 3. Design

### 3.1 Surface and baseline (reuse AL's frozen A0, no re-baseline)

The baseline arm is AL's frozen AI-TRUE A0 surface: 1,662 rows, graded 116
confab / 90 correct / 120 wrong / 114 answerable-refused / 1,222
unanswerable-refused (reproduced this session from
`analysis/amendment_al_prep/amendment_al_run/per_row_exhaust.jsonl`). No
regeneration of the baseline; the steered arms regenerate the SAME 1,662
questions with the same checkpoint, system prompt, greedy decoding, and grader
as AL's A0 cell.

### 3.2 Sensor and actuator (both frozen; actuator REFIT on this checkpoint)

- **Sensor (propensity readout):** AL's frozen per-row propensity z-score
  (`prop_z` in the exhaust): L24 PCA-128 (seed 20260705), standardized,
  caution-residualized, mean-diff confab-vs-unanswerable-refused, fit on the
  full baseline surface, frozen. Row FLAGGED iff `prop_z >= 1.00` (operating
  point derived in section 4).
- **Actuator (caution setpoint write):** the AC `couple` mechanism,
  `h' = h - (h.c_hat)c_hat + g*sigma_c*c_hat`, at L35, every position from the
  pre-generation anchor onward, on flagged rows only. `c_hat = unit(caution_perp)`
  REFIT on the AI-TRUE checkpoint (see below). Flagged rows get a FIXED
  `g = +2` (clipped, setpoint UP toward refusal); unflagged rows are untouched.

**caution_perp refit (Amendment T drift - mandatory).** AC's committed
caution_perp was fit on the GRPO-v2 extraction. Directions drift across
checkpoints, so the actuator is refit on the AI-TRUE pre-generation extraction
(`analysis/amendment_al_prep/true_a0/extract/data`, L35 anchor prompt_len-1),
using the same mass-mean construction as `build_caution_perp_direction.py`,
with behavior cells joined from AL's frozen A0 grades (known_correct_answered
n=90, known_refused n=114, unknown_refused n=1,222). Refit result (this
session, `amendment_an_refit_caution_perp.py`): perp_fraction 0.673, raw
cos(caution, doubt) -0.740, sigma 22.13, kr-ka projection gap 21.06.
**cos(AI-TRUE caution_perp, GRPO-v2 caution_perp) = -0.064.** The two
directions are essentially orthogonal (and slightly anti-aligned): actuating
the GRPO-v2 direction on this checkpoint would have been near-random. This is
exactly why the refit is mandatory; the refit direction is the one AN writes.

### 3.3 Arms

1. **PRIMARY (propensity-selected caution write):** rows with baseline
   `prop_z >= 1.00` are pushed with `g = +2` (clipped) via the couple
   mechanism; everything else generates untouched. At baseline this flags 244
   rows: 47 confabs, 4 corrects, 11 wrong, 18 answerable-refused, 164
   unanswerable-refused.
2. **CONTROL (permuted flag):** identical write (`g = +2`, same direction,
   same L35), but the flagged set is a uniform random draw of the SAME COUNT
   (244) from all 1,662 rows (seeded, one draw, recorded). This is the causal
   analog of AL's permutation null, and the AN-G3 comparator.
3. **DESCRIPTIVE gain ladder (gate-free):** `g = +1` and `g = +3` on the
   flagged confabs only, mirroring AL's dose ladder, to bound the linear
   dose-response assumption.

All arms are local GPU generation sweeps on the same seed and config; the read
pass (batch-1 pre-generation forwards for the propensity flag) is shared and is
already frozen in the exhaust.

## 4. Gates (LOCK at signing)

### 4.1 Operating point (aim-small derivation from the selector table)

`amendment_an_build_selector_table.py` grids the propensity-z flag threshold
against the AL baseline grades. Reach = flagged confabs; collateral exposure =
flagged corrects. The efficiency knee is at `prop_z >= 1.00`:

| thr | flag total | confab (reach) | correct (collateral) | reach% | collat% |
|-----|-----------|----------------|----------------------|--------|---------|
| 1.5484 (AL's) | 98 | 30 | 1 | 25.9% | 1.1% |
| 1.25 | 167 | 37 | 3 | 31.9% | 3.3% |
| **1.00 (chosen)** | **244** | **47** | **4** | **40.5%** | **4.4%** |
| 0.90 | 291 | 54 | 7 | 46.6% | 7.8% |
| 0.80 | 340 | 54 | 8 | 46.6% | 8.9% |

Marginal efficiency (confabs gained per correct exposed, walking the threshold
down): +10 confab / +1 correct from 1.25 to 1.00, then +7 confab / +3 correct
from 1.00 to 0.90, then +0 confab / +1 correct from 0.90 to 0.80. The knee is
at 1.00: it captures the bulk of the reachable confab mass (47 of 116) while
holding collateral exposure to 4 of 90 corrects, and reaches deeper than AL's
own threshold at a controlled cost. Below 1.00 the marginal efficiency
collapses (0.80 buys zero additional confabs for an extra exposed correct).
Chosen operating point: **`prop_z >= 1.00`**.

### 4.2 AC-observed setpoint compliance (the floor input)

From the AC coupled-vs-ablate per-row results (this session): a setpoint-UP
write at `g in [1.5, 2.0)` induces refusal +16.0pt over the erase-only
counterfactual (absolute coupled refusal 0.800 in that bin; erase-only 0.640).
The write's OWN push toward refusal - the part beyond erasing the gate - is
~0.16 per row at g near +2. Because AN's confabs are a harder population than
AC's intervened cells (fabrication on unanswerable questions, not the ka/kr/ur
cells), AN credits the setpoint write only with this incremental 0.16 as the
conservative per-row kill probability. This is deliberately the smaller of the
two available numbers (0.16 incremental vs 0.80 absolute): AL already showed
the propensity direction alone reaches nothing, so AN must earn its result from
the caution write specifically.

### 4.3 The gates

- **AN-G1 (collateral, honesty ceiling):** at most **2 of the 4** baseline-
  correct rows flagged at the operating point flip to refusal in the primary
  arm. Derivation: the 4 flagged corrects each receive `g = +2`, which pushes
  toward refusal, so they are genuinely at risk (unlike AC, where corrects
  received negative gains and the guard passed trivially). Under a worst-case
  per-row flip probability of 0.80 (AC's absolute top-bin refusal rate),
  P(<= 2 of 4 flip) = 0.181 and P(<= 1) = 0.027 - so a ceiling of 2 is a real
  test that a working-but-blunt selector can bust. Correct-to-wrong flips
  (never refusal) are tracked descriptively and do not gate.
- **AN-G2 (reach floor):** at least **5 of the 116** baseline confabs are
  killed in the primary arm (killed = the row no longer produces a graded
  confab; refusal or hedge count; a confab that becomes a different confab does
  not). Derivation: 47 flagged confabs x 0.16 (AC g~+2 incremental write
  compliance) = 7.5 expected kills, binomial sd sqrt(47*0.16*0.84) = 2.5; the
  floor is set at expected minus one sd ~ 5. (If the true per-row kill
  probability is 0.16, the one-sided 95% lower bound is 3.4, so 5 is not
  trivially cleared - it is the aim-small point estimate minus a sigma, not a
  round number.)
- **AN-G3 (specificity):** primary-arm confab kills minus control-arm confab
  kills is at least **5**, with a 1,000-resample row bootstrap 95% CI excluding
  zero (same construction as AL-G3). Derivation: the permuted-flag control
  flags 14.7% of rows uniformly, so it flags ~17.0 confabs in expectation and
  kills ~2.7 at the 0.16 compliance; primary expects ~7.5 kills; the
  specificity margin is ~4.8, so a floor of 5 (rounded up from the derived
  margin, matched to AN-G2) is the aim-small point.

### 4.4 Falsifier and partial disposition

**FALSIFIER:** AN-G2 AND AN-G3 both missing means the caution-setpoint write
does not reach the confab cloud selectively even when the reaching sensor aims
it there; the result is recorded as a sensor-actuator-mismatch null (the
propensity sensor reads the cloud, the caution actuator moves behavior, but the
composition does not reach it) and the regulator needs a different pairing. No
goalposts move.

**PARTIAL:** AN-G1 busting (more than 2 flagged corrects flip) while AN-G2 and
AN-G3 pass is a PARTIAL outcome - the mechanism reaches the confab cloud but
the selector is too coarse to spare honest answers; claimable as
mechanism-works-selector-too-blunt, with the operating-point sweep (section 4.1)
as the map of where a finer selector would sit.

## 5. Secondary exploratory arm (flagged exploratory; never pooled)

**Over-refusal repair, same run.** To demonstrate the bidirectional regulator
in one cell, a secondary arm applies AC's NEGATIVE-gain law (`g = -2`, setpoint
DOWN toward answering) to the 114 answerable-refused rows, reusing the same
couple mechanism and the same refit caution_perp. This tests whether the
regulator can release honest-but-over-cautious refusals in the same pass it
suppresses confabs. Gates: **descriptive only in AN** - reported as de-refusal
rate and post-de-refusal correctness on the answerable-refused cell, never
pooled with the primary claim, never gated. A positive descriptive signal here
graduates to its own signed amendment (bidirectional regulator, pre-registered
gates).

## 6. Knob-discovery screen (LAB-NOTEBOOK, NOT GATED)

The user asked whether there are other decision knobs the program is missing.
AC found caution works and AL found propensity does not by testing them one at
a time against behavior. This is the systematic version: a causal actuation
screen that measures, for each candidate direction, the behavioral flip rate
per unit push at matched norms on a small row panel. **Design only in AN - not
run under this amendment.** Any candidate that flips behavior above the random-
direction control graduates to its own signed amendment.

### 6.1 Candidate directions (K ~ 9-11)

1. `caution_perp` (AI-TRUE refit) - positive control; AC proved it moves
   behavior, so it must register as a hit or the screen instrument is broken.
2. `answer-vs-refuse` axis (behavior direction, answered vs refused mass-mean).
3. `dial` / post-generation correctness axis (Amendment S/T readout).
4. `doubt` axis (`u_d`, known vs unknown mass-mean).
5. `propensity` direction (AI-TRUE) - negative control; AL proved it does not
   move behavior, so it must register at ~random or the screen mislabels.
6. per-flavor confabulation directions (item-22 / mi_controversial_flips
   per-flavor axes), one per available flavor.
7. top-k PCA components of the decision-band residual (k = 3), label-agnostic.
8. random-direction controls (5 seeds) - the null band the hits must clear.

### 6.2 Method

Small panel (~120 rows: 40 confab, 40 correct, 40 answerable-refused, drawn
seeded from the AL exhaust). For each candidate direction d and each push
variant, regenerate the panel at matched push norm and score the behavioral
flip rate (fraction of rows whose graded action changes) relative to baseline.

- **Norm matching:** every push scaled to the same L2 magnitude in the residual
  stream (the per-direction sigma * a shared alpha grid {1, 2, 3}), so a hit is
  not just a bigger vector.
- **Two write variants per direction:** ERASE-AND-WRITE (`couple`, the AC
  setpoint mechanism) AND ADDITIVE (`shift`, `h + alpha*sigma*d`), because AC's
  win was specifically erase-and-write and AL's null was additive-style - the
  screen must not confound the direction with the write form.
- **Output:** a ranked actuation table (direction x variant x alpha ->
  flip-rate, with the random-direction band as the reference), written to
  `analysis/amendment_an_prep/an_knob_screen/` (untracked). Directions whose
  flip rate exceeds the random band's upper envelope at matched norm are the
  graduates.

### 6.3 Cost and lane

Local RTX 3090. ~120 rows x (K ~ 10 directions + 5 random) x 2 variants x 3
alphas ~ 10,800 short greedy generations (max_new_tokens 96), plus one baseline
panel pass. At AL-comparable throughput this is a few GPU-hours, single
session, no cloud. The read pass (candidate directions) is CPU and reuses the
frozen AI-TRUE extraction. This screen is deferred to a lab-notebook entry; it
is described here so the design is pre-stated, but it does not run under AN and
carries no gates.

## 7. Preconditions and approvals

1. User sign-off on this document and a recorded user prediction
   (dual-prediction practice; scoreboard `docs/prediction-scoreboard.md`).
   Orchestrator and user prediction fields in the frontmatter are EMPTY until
   signing.
2. Local GPU free (`lms.exe unload --all` if LM Studio holds it).
3. No cloud spend; everything local.
4. Grader identical to AL's A0 cell; grading config byte-pinned.
5. caution_perp refit already built and provenance-recorded (section 3.2); the
   selector table and operating point already built (section 4.1). Both are
   deterministic CPU prep committed with this branch.

## 8. Instrumentation (descriptive, gate-free)

- Dose ladder {g = +1, +3} on the flagged confabs of the primary arm.
- Flavor breakdown of confab kills and any correct-answer leaks.
- Post-write caution re-read on flagged rows (did the caution projection move
  by the commanded amount; separates actuation failure from injection failure,
  the diagnostic that isolated AL's null as causal rather than instrumental).
- Wrong-answer conversions among flagged wrong rows (descriptive).
- Secondary-arm (over-refusal repair) full table for the bidirectional-
  regulator follow-up design.
- Map-territory exhaust: per-row provenance (prop_z, caution_z, flag, arm,
  written gain, grade before/after) packaged for publication with approval.

## 9. Interpretive caveats (pre-stated)

- Single checkpoint (AI-TRUE), single seed; a pass licenses a mechanism claim
  on this checkpoint only, with multi-seed replication required before any
  headline. Tier-2 exploratory, never pooled with the locked Phase 1 matrix.
- The caution_perp actuator is refit on this checkpoint (cos -0.064 to the
  GRPO-v2 direction); portability of the regulator across checkpoints is a
  separate question from whether it reaches here.
- The propensity flag is frozen from AL's read pass; the primary arm re-reads
  caution on the same rows to confirm the write landed, but the FLAG itself is
  not recomputed under intervention (open-loop selection, matching AC's
  offline-read design).
- The g = +2 write assumes a roughly linear dose-response along caution_perp;
  the {+1, +3} ladder bounds this descriptively.
- Baseline grades come from AL's single grading pass; regeneration noise on
  unflagged rows is absorbed by comparing arms on the same grader, and the
  control arm shares any regeneration drift.

## 10. Implementation plan

- `experiment/phase1/probe/amendment_an_refit_caution_perp.py` (NEW, CPU,
  DONE this session): refits caution_perp on the AI-TRUE extraction, records
  the cosine to the GRPO-v2 direction. Output:
  `analysis/amendment_an_prep/caution_perp_direction_L35_ai_true.json`
  (untracked).
- `experiment/phase1/probe/amendment_an_build_selector_table.py` (NEW, CPU,
  DONE this session): grids the propensity-z flag threshold vs AL baseline
  grades, marks the chosen operating point. Output:
  `analysis/amendment_an_prep/an_selector_table.{json,md}` (untracked). The
  chosen-threshold numbers are pre-registration constants copied into section 4.
- Run config (built at signing): a `phase3_residual_intervention` config with
  the primary (couple, per-row flag -> g=+2), control (permuted flag), and
  descriptive-ladder arms, pointing at the refit direction JSON and a flag map
  derived from the exhaust. Reuses the existing couple machinery and runner; no
  new intervention math.
- Analysis (built at signing): confab-kill / collateral / specificity tally
  with the AN-G3 row bootstrap, mirroring AL's analysis script.

## 11. Outcome (resolved 2026-07-06)

Mechanical tier per section 4: **NULL, falsifier fired** (AN-G2 and AN-G3
both missing). Scorer output:
`analysis/amendment_an_prep/amendment_an_run/gates_report.json`. Smoke
readback: `analysis/amendment_an_prep/amendment_an_run/smoke_primary/readback.json`.

### 11.1 Baseline and arms

| | confab | correct | wrong | answerable-refused |
|---|---|---|---|---|
| baseline (n=1,662) | 116 | 90 | 120 | 114 |
| primary flagged (n=244) | 47 | 4 | 11 | 18 |
| control flagged (n=244) | 21 | 17 | - | - |

### 11.2 Gates

| gate | value | threshold | result |
|---|---|---|---|
| AN-G1 collateral | 0 | <= 2 | PASS (vacuous) |
| AN-G2 reach | 0 confabs killed | >= 5 | FAIL |
| AN-G3 specificity | diff 0, CI [0.0, 0.0] | diff >= 5, CI excludes 0 | FAIL |
| overall | - | - | **FAIL** |

**AN-G1: PASS, but vacuous.** None of the 4 flagged baseline-correct rows
flip to refusal. This is not evidence the selector spares honest answers
under a real write; it is the arithmetic consequence of a write that changes
nothing for anyone, confab or correct. The gate's honesty guarantee was never
tested because the risk it guards against never materialized.

**AN-G2: FAIL.** 0 of 116 baseline confabs killed in the primary arm, against
a floor of 5. All 47 flagged confabs land in `confab_to_different_confab`:
the write changes the generated fabrication but never converts it to a
refusal. The descriptive dose ladder (g in {+1, +2, +3}) kills 0 confabs at
every gain tested, so this is not a dosing problem within the range checked.

**AN-G3: FAIL.** Primary-minus-control kill difference is 0 (primary kills
0, the permuted-flag control also kills 0 of its 21 flagged confabs), with a
1,000-resample row bootstrap 95% CI of [0.0, 0.0] against a floor of 5 with
CI excluding zero.

**Descriptive bidirectional arm (never gated).** The same actuator run in
reverse (g=-2, setpoint DOWN) on the 114 baseline answerable-refused rows
de-refuses 0 of 114 (rate 0.0), with 0 becoming correct answers. The null
holds in both directions of the same write.

**Injection-fidelity smoke.** 20 flagged / 8 unflagged rows re-read after the
write: mean observed setpoint on flagged rows 43.98 vs commanded 44.26 (max
abs error 0.58 against sigma 22.13); unflagged rows show zero coordinate
shift (mean abs shift 0.0). The write lands precisely on-axis and touches
only the intended rows, ruling out an injection-fidelity explanation for the
null.

### 11.3 Interpretation

The pre-registered question was whether pairing the sensor with proven reach
(confabulation propensity) with the actuator with proven force (AC's caution
setpoint) closes the loop AL's same-direction pairing could not. It does not:
even reached this precisely, the caution setpoint does not carry the
fabricate-vs-refuse decision for the propensity-flagged population.
caution_perp is a correlate of the caution behavior it was fit on, not a
general-purpose lever the confab cloud answers to when addressed through a
different sensor. This closes both escapes earlier write-side nulls left
open: an imprecise write (AL already ruled this out; this smoke reconfirms
it) and a weak or wrong actuator (AC's actuator independently moves behavior
on its own population, so it is not weak in general). Framing for the
program: every WRITE-side activation-edit tested on an isolated axis so far
(AA/AB, AL, AI, AN) is null; every INPUT-side / TEXT-channel intervention
tested (AF, AC itself, AG) has actuated. AN's null is consistent with, not
contradicted by, those prime-channel wins.

Both predictions called AN-G2/AN-G3 PASS; both missed. The user called PASS
at full confidence; the orchestrator called PASS but at ~40% (an implied lean
toward miss). Scored **LOSS/WIN** (user-orchestrator), the same convention
applied to AL's sub-50%-counts-as-a-lean calls; see the frontmatter
`scoreboard` field and `docs/prediction-scoreboard.md` for the ledger entry.
No goalposts moved: the gates and floors above are exactly those locked in
section 4 at signing.

## 12. Changelog

- 2026-07-05: created (DRAFT). caution_perp refit on AI-TRUE (cos -0.064 to
  GRPO-v2), selector table built (operating point prop_z >= 1.00: 47 confabs /
  4 corrects flagged), gates derived aim-small from the selector table and the
  AC setpoint-compliance measurement. Not signed; predictions unrecorded.
- 2026-07-05: SIGNED. User recorded predictions ("I agree on all passing");
  gates in section 4 locked as drafted.
- 2026-07-06: RESOLVED - NULL, falsifier fired (AN-G2 and AN-G3 both missing).
  See section 11. Scored LOSS/WIN (user-orchestrator); ledger updated in
  `docs/prediction-scoreboard.md`.
