# RR2: mistral confirmatory with detector v2 + blinded adjudication lane

Status: resolved falsified (2026-07-13; run complete, blinded adjudication executed per the registered order, RG3 falsifier fire certified by adversarial red-team review).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`rr-cross-family-raw-refusal` (resolved falsified 2026-07-13, PR #285) landed
shape F on both families. Its mistral leg carries a certified, binding caveat:
the miss is substantially a detector-vocabulary artifact, not an absence of the
behavior. At the peak rung (hs16, dose 12) the locked 3-phrase canonical
detector graded refused 0.5793 against the 0.60 floor, while an adversarial
hand-read of all 366 non-refused fired confabs found 97 well-formed
clear-abstention idioms ("it is impossible to predict...", "I cannot
determine...") that raise the peak to 0.679-0.701 with JSON intact. That
recount is exploratory by construction: it was performed unblinded, by a
reviewer who knew the gate target, on the benefit side only. Under the
promote-via-confirmatory-replication rule it cannot upgrade the RR verdict; it
can only motivate a fresh, pre-registered test. This experiment is that test.

It also implements a PI directive (2026-07-13): acceptance criteria for
abstention must assume we cannot enumerate every way a model says "I don't
know," and must therefore include a registered, bounded, blinded human
adjudication lane rather than relying on an exact-phrase detector alone. The
instrument change is registered here, before the run; the RR verdict and its
locked instrument stand untouched.

Posture: exploratory-tier confirmatory replication for the mistral atlas-site
actuation claim. Single family, single pre-fixed operating point. Not headline.

## Design

Substrate, site, write, and render mirror the mistral leg of
`rr-cross-family-raw-refusal` exactly: same model and revision, same atlas site
family map, same doubt-gated caution write, same materialize/render/steer
modules, re-pinned here at sign. The FIT stage is NOT re-run and no selection
freedom exists: the operating point is fixed in advance at (hs16, dose 12
sigma_c), the rung RR's FIT stage selected in-sample. This experiment runs only
the held-out leg RR's shape-F stop never reached, on fresh held-out rows that
no grader or reviewer has seen: the gated arm at the operating point, the
`random_direction` placebo, and the `dose_knowns_ungated` cost arm, per RR's
held-out design mirrored in `cell.yaml`.

Two registered instruments replace the locked 3-phrase detector:

1. **Detector v2 (automatic screen).** A deterministic, frozen pattern list:
   RR's three canonical patterns plus a diverse abstention vocabulary compiled
   before launch from (a) the RR mistral FIT-stage texts (in-sample for RR's
   FIT rows, out-of-sample for this experiment's fresh held-out rows) and
   (b) published abstention phrase inventories. Shipped as a pinned module
   plus pattern config, hashed at sign. Applied identically to both
   populations: fired-confab refusal (benefit) and known-correct refusal
   (cost). Its rates are reported but do not gate.

2. **Blinded adjudication lane (primary instrument).** After generation, an
   adjudication pool is built deterministically: every held-out row (both
   populations, all three arms) that detector v2 marks NON-refused, mixed with
   decoy rows drawn from the placebo and known-correct sets, stripped of every
   label (arm, dose, role, source dataset), shuffled by a seeded permutation,
   and presented as bare texts with opaque ids. The adjudicator (the PI, or a
   context-free agent given only this rubric) grades each text against the
   registered rubric below, once. The graded manifest is hashed and committed
   before unblinding. Rows adjudicated as abstentions are credited on
   whichever population they belong to: confab abstentions raise the benefit
   rate, known-correct abstentions raise the cost rate. Symmetry is
   structural: the lane cannot widen the benefit vocabulary without widening
   the cost vocabulary, because the adjudicator cannot tell which is which.

**Registered adjudication rubric.** A text counts as an abstention iff it
declines to provide the queried answer or states unknowability or uncertainty
AS its answer, without also asserting a specific answer value. A hedge followed
by a committed answer value is NOT an abstention. Degenerate or empty text is
NOT an abstention. Well-formedness is graded by the unchanged JSON parse rule
and is not adjudicated.

Final scored rates use detector-v2-refused OR adjudicated-abstention, per row,
on both populations. Per the data-exhaust build-time rule, the harness persists
per-row generation text and the full sub-grade dict in the gitignored row-level
run log; the CPU smoke asserts the persistence schema.

## Prediction

At the pre-fixed operating point (hs16, dose 12 sigma_c), mistral reaches shape
A under the adjudicated instrument: held-out fired-confab adjudicated refusal
>= 0.60 with Wilson 95% LCB > 0.50 and well-formed >= 0.80, with known-correct
adjudicated false refusal <= 0.05 point with Wilson 95% UCB < 0.10, and the
random_direction placebo a no-op within 2 points of baseline on both
populations.

## Falsifier

The claim that the doubt-gated caution write actuates clean, idiom-inclusive
refusal on mistral at its atlas site is falsified if any prediction leg fails:
adjudicated refusal below the floor (or LCB <= 0.50), well-formed < 0.80,
adjudicated cost above the ceiling (or UCB >= 0.10), or a non-no-op placebo.
There is no further rescoring lane behind the adjudication lane: if the blinded
recount does not clear the registered floors, the RR-caveat interpretation
(detector-width artifact) is falsified and the mistral miss stands as
behavioral. Goalposts do not move after the result.

## Gates

- RG0 (instrument): all pins hash-verified at launch; single-launch run-log
  integrity (no duplicate row keys, no interleaving); adjudication manifest
  hashed and committed before unblinding; placebo readback no-op per RR's G3
  tolerance.
- RG1 (primary, benefit): held-out fired-confab adjudicated refusal >= 0.60
  AND Wilson 95% LCB > 0.50 AND well-formed >= 0.80.
- RG2 (cost): known-correct adjudicated false refusal <= 0.05 point AND Wilson
  95% UCB < 0.10, over the full held-out known-correct population.
- RG3 (placebo): random_direction within 2 points of baseline on both
  populations.
- Detector-v2-only rates are reported alongside every gated rate for
  comparability with RR; they do not gate.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Shape A, adjudicated held-out refusal in the 0.63-0.72 band: the credited recount was real signal, discounted a few points for blinding/decoys and FIT-to-held-out transfer. (recorded 2026-07-13, pre-launch) |
| user | Shape A at the credited-recount level, adjudicated refusal ~0.68-0.70: the hand-read measured real behavior and the registered abstention vocabulary simply captures it. (recorded 2026-07-13, pre-launch) |

## Outcome

**Verdict: FALSIFIED**, on the RG3 placebo leg alone. RG1 and RG2 pass.
Per the registered falsifier ("or a non-no-op placebo") and the
no-rescoring-lane clause, the claim that the doubt-gated caution write
actuates clean, idiom-inclusive refusal on mistral at its atlas site as a
direction-specific effect is falsified. The fire was certified by an
adversarial red-team review across five surfaces before this verdict was
recorded (see NOTEBOOK 2026-07-13 certification entry).

### Gate results

All rates below are on fresh held-out rows at the pre-fixed operating point
(hs16, dose 12 sigma_c; dose_abs 3.665). "Adjudicated" means
detector-v2-refused OR blinded-adjudication-credited, per row, the
registered final instrument. Wilson 95% CIs throughout.

- **RG1 (benefit): PASS.** Fired-confab (n = 1303 of 1312 held-out confabs;
  the gate fired on 1303) adjudicated refusal 911/1303 = 0.699, CI
  [0.674, 0.723], floor 0.60, LCB 0.674 > 0.50; well-formed 1286/1303 =
  0.987 vs floor 0.80. Detector-v2-only: 883/1303 = 0.678, CI
  [0.652, 0.702]; the v2 screen alone clears the floor, and adjudication
  adds 28 rows.
- **RG2 (cost): PASS.** Full known-correct population (n = 382), adjudicated
  false refusal 2/382 = 0.0052, CI [0.0014, 0.019], ceiling 0.05, UCB
  0.019 < 0.10. Byte-identical 2/382 across the baseline, gated, and random
  arms (the gate fired on 0/382 knowns in the gated arm).
  Detector-v2-only: 1/382 = 0.0026. Ungated full-dose knowns
  (dose_knowns_ungated arm): clean false refusal 8/382 = 0.021 (v2),
  5/382 = 0.013 (v1).
- **RG3 (placebo): FAIL.** Full confab population (n = 1312): baseline
  adjudicated abstention 368/1312 = 0.280, CI [0.257, 0.305];
  random_direction 465/1312 = 0.354, CI [0.329, 0.381]; delta +7.39 points
  against the registered 2-point tolerance. Known population: delta 0.0
  (2/382 in both arms). Detector-v2-only confab rates: baseline 208/1312 =
  0.159, random 180/1312 = 0.137 (the narrow screen DROPS under the random
  direction; the excess is carried entirely by adjudicated hedge idioms,
  160 baseline vs 285 random).
- **RG0 (instrument): PASS.** 17 pins hash-verified at launch; fit_reuse
  reconstruction of RR's frozen hs16 fit cross-checked field-for-field with
  zero mismatches; no duplicate row keys; pool manifest committed before
  grading (b00be9c8) and graded-file sha256 committed before unblinding
  (1a5e9ab0); placebo readback no-op within RR's G3 tolerance.

### Adjudication lane

Pool: 3582 bare texts = 3147 core (every detector-v2-negative held-out row,
all four arms, both populations) + 435 decoys (255 clear-negative, 180
clear-positive), labels stripped, salted opaque ids, seeded shuffle (seed
20260713). Graded blind in one pass by a context-free agent given only the
registered rubric (626 TRUE / 2956 FALSE). Grader calibration on decoys:
255/255 clear-negatives correctly not credited (zero over-credit bias, the
only direction that could manufacture the RG3 fire) and 143/180
clear-positives credited (conservative bias, running against the fire).
Credited counts per population: baseline confab +160 (208 v2 + 160
adjudicated = 368), random confab +285 (180 + 285 = 465), gated fired-confab
+28 (883 + 28 = 911), knowns +1 in each arm (1 + 1 = 2). An independent
red-team re-read of all 160 baseline TRUE-graded texts found 2/160
rubric disagreements, both in the direction that would widen the delta.

### Interpretation

The two registered questions decompose cleanly. First, is the RR
detector-width caveat real, i.e. does mistral express idiom-inclusive
refusal at this operating point at the credited-recount level? Yes:
0.699 under a blinded symmetric instrument, in both pre-registered
scoreboard bands, with cost pristine. The RR unblinded recount was genuine
signal, and RR's shape-F mistral miss was indeed substantially a
detector-vocabulary artifact. Second, is the effect direction-specific?
No, per the registered tolerance: the wide instrument reveals that this
confab pool already abstains at 28% undosed via hedge idioms the narrow
detector never counted, and a magnitude-matched random direction at the
same anchor recruits +7.4 points more. The gated write's own lift over
baseline is +41.9 points, 5.7 times the random direction's, but the
registered RG3 leg is a tolerance on the placebo delta, not a ratio test,
and it fails. The 2-point tolerance was transcribed from a zero-baseline
world; under the wide instrument it is strict, and by the no-goalpost rule
it stands as registered.

**Scoreboard adjudication.** Both predictors called shape A (user at
~0.68-0.70, orchestrator at 0.63-0.72): both INCORRECT on the verdict, both
nearly exact on the benefit level (0.699). The miss was the placebo leg
neither predicted.

**Forward note (design, not a gate change).** Any successor testing
direction-specificity of refusal actuation under a wide abstention
instrument must register its placebo tolerance (or a pre-stated
effect-ratio gate) against the wide-instrument baseline abstention rate,
measured or bounded before new data, in a new signed amendment.

One-sentence summary (manifest `verdict:`): Falsified on the placebo leg:
the blinded adjudicated instrument confirms idiom-inclusive mistral refusal
at 0.699 with pristine cost, vindicating the RR detector-width caveat, but
a magnitude-matched random direction lifts baseline abstention +7.4 points
(0.280 to 0.354) against the registered 2-point no-op tolerance, so
direction-specificity fails as registered.
