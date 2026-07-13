# RR2: mistral confirmatory with detector v2 + blinded adjudication lane

Status: draft (not signed; do not launch as confirmatory evidence). Cannot sign
until PR #285 (rr-cross-family-raw-refusal resolve) merges: this experiment's
instruments mirror and pin modules from that experiment directory.

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
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results with Wilson CIs on
every rate (adjudicated and detector-v2-only), the adjudication pool size and
credited counts per population, and the one-sentence summary that also goes
into `verdict:` in the manifest.
