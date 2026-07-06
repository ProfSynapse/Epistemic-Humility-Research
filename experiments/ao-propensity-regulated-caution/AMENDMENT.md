# ao-propensity-regulated-caution

Status: draft (not signed; do not launch as confirmatory evidence). Tier-2
exploratory local mechanism evidence, never pooled with the locked Phase 1
matrix.

Machine state lives in `experiment.yaml`; it is not duplicated here.

## Motivation and posture

Amendment AC wired the doubt readout to the caution gate as a live, proportional
function at inference and won: coupling beat the permuted placebo by +8.7pt on
the selectivity gap (AC-G1, CI [+5.6, +12.0]), on a caution direction that
refined B1 had already validated as a behavioral lever (ablating it moves
known_refused refusal 0.994 to 0.524 with specificity intact). AC is the
standing proof that a single-direction activation erase-write on caution
actuates behavior when it writes a validated direction.

The user's hypothesis for this cell, stated directly: the confab-cloud
propensity readout gives a good indication of when the model knows it is
hallucinating, and we should wire that readout to caution the same way AC wired
doubt, so it regulates the caution setpoint directly and proportionally, per
row.

The goal is CALIBRATION, both directions, not one-way confab suppression. This
is how AC actually won: its headline was a selectivity gap, releasing refusal on
known_refused (things it should answer) while preserving refusal on
unknown_refused (things it should not). AO targets the same bidirectional
alignment with the propensity signal: the single continuous coupling should
refuse MORE where confab-propensity is high (the model reads as knowing it is
fabricating) and refuse LESS where propensity is low (it actually knows), and it
should beat a permuted placebo on that propensity-conditioned selectivity. A
one-way "kill confabs" count (AN's framing) is not the metric.

Amendment AN attempted a version of this and produced a NULL, but that null is
confounded and does not test the hypothesis: AN wrote on a `caution_perp` refit
on the AI-TRUE checkpoint whose cosine with AC's validated direction is -0.064
(essentially orthogonal, a different vector), it was never shown to be a lever
on this checkpoint (AN's section 6 knob-validation screen was deferred, not
run), and it used a fixed gain with binary propensity flagging rather than a
continuous proportional controller. So AN cannot separate "caution cannot
suppress confabulation here" from "AN's actuator was dead." AO fixes all three:
a validated actuator, a continuous proportional gain, and the knob-validation
step in frame.

## Design

Substrate: the AI-TRUE checkpoint (same one used by AL and AN, where the confab
cloud and the confabulation-propensity direction are characterized). It carries
BOTH calibration tails on the 1,662-row AL A0 baseline pool: 116 residual
confabulations (should refuse, currently answering) and 114 answerable-refused
rows (should answer, currently refusing). Both are needed to measure the
bidirectional selectivity gap. Same system prompt, greedy decoding, and grader
as the AL A0 cell. Local RTX 3090, single seed. Pinned at `exp sign`.

GRPO-v2 is a pre-planned fast-follow (its own later cell), not part of this one:
it already has AC's validated caution lever, but its calibration problem is the
over-refusal tail only, and its confab-propensity direction has to be refit
there first. AO establishes the mechanism on AI-TRUE (both tails) before that
replication.

Two stages, each gated. Stage 2 runs only if Stage 1 passes.

STAGE 1, knob validation (the fix for AN's confound; this is a positive-control
screen, run in frame, not deferred). Fit one or more candidate caution
directions on the AI-TRUE checkpoint (the AI-TRUE `caution_perp` refit, plus the
mass-mean answer-vs-refuse contrast as a fallback lever). For each candidate,
apply AC's constant writes (ablate `g == 0`, and shift by fixed gain in both
directions) and measure whether refuse/answer behavior moves with specificity,
exactly as refined B1 did on GRPO-v2. This establishes, on this checkpoint,
whether any caution direction is a behavioral lever at all.

STAGE 2, proportional coupling (the faithful AC analog). Using the Stage-1
validated direction `c_hat`:

- Sensor (read, offline, CPU): the confabulation-propensity readout on the
  frozen AI-TRUE pre-generation extraction. Each eval row gets a propensity
  projection standardized over the eval-row population, `prop_z_i`. Computed
  from frozen activations BEFORE any intervention, so there is no within-item
  feedback (AC's design property).
- Actuator (write, during generation): erase the model's own caution value and
  write a propensity-proportional setpoint at every position, the AC `couple`
  mechanism:

  ```
  h' = h - (h . c_hat) c_hat + g_i * sigma_c * c_hat
  g_i = +alpha * prop_z_i, clipped to [-2, +2], alpha = 1 (pre-registered)
  ```

  Plus sign (mirror of AC's minus for doubt): high confab-propensity, the model
  reads as knowing it is fabricating, writes caution HIGH, refuses; low
  propensity leaves the gate low and answers.
- Orthogonality: `c_hat` is residualized against the propensity sensor direction
  so the write does not disturb the variable being read (mirror of AC's
  `caution_perp` orthogonal to `u_d`). Pinned at sign.

Arms (one pre-registered configuration; no alpha sweep, no coupling-form
fishing), on the confab and answerable-refused cells:

| arm | mode | gain |
|-----|------|------|
| baseline | baseline | none |
| coupled | couple | `g_i = +prop_z_i` (real, clipped) |
| permuted | couple | same gains, row-shuffled (fixed seed) |
| ablate | couple | `g == 0` (constant comparison, nested) |

Smoke gate before the full run (25 rows/cell): coupled shows any directional
confab-vs-refuse separation vs permuted; if nothing, report the smoke and stop.

Instrument configs to pin at sign: `cell.yaml`, `gates.yaml`, the grader module,
and the propensity + caution direction JSONs. Named in the manifest.

## Prediction

(orchestrator) Stage 1 finds at least one caution lever on AI-TRUE, but weaker
than GRPO-v2's; Stage 2 coupled beats permuted by a small positive margin
(roughly 3 to 10pt) on confab suppression, smaller than AC's doubt result. Real
risk that Stage 1 finds no lever, in which case AN's null is explained as a dead
actuator and the hypothesis is untestable on this checkpoint until a caution
lever exists.

(user, recorded 2026-07-06) Stage 1 PASS (there is a caution lever on AI-TRUE)
and Stage 2 PASS (propensity coupling beats the placebo). "yes and yes."

## Falsifier

Given Stage 1 passes (a validated caution lever exists on AI-TRUE): coupled is
within the gate margin of permuted (margin below the G1 floor, or bootstrap CI
includes 0). Then the confab-propensity readout adds nothing at the intervention
site beyond a constant caution write, and this is a CLEAN null on a validated
actuator, unlike AN. Pre-committed consequence: report as a negative, no
alpha-tuning or alternative-coupling rescue runs under this amendment.

If Stage 1 fails (no caution lever validates on AI-TRUE), the coupling stage does
not run; the reported result is "no caution actuator on this checkpoint," which
is the clean explanation AN could not provide.

## Gates

Selectivity gap (the primary metric, bidirectional, analogous to AC-G1). Define
per arm:

```
gap = (delta_refusal on high-propensity confab rows)
      - (delta_refusal on low-propensity answerable-refused rows)
```

where `delta_refusal = refusal_arm - refusal_baseline` on that cell. A
well-calibrated coupling drives delta_refusal UP on confabs (refuse the
fabrications) and DOWN on answerable-refused (release the knowable), so a large
positive gap means the propensity signal is moving refusal the right way on both
tails at once. The permuted arm has the same gain distribution with the signal
scrambled, so any coupled-minus-permuted gap is attributable to the signal.

- G0 (Stage 1, precondition, pass/fail): at least one caution direction moves
  the refusal rate on this checkpoint by a margin whose bootstrap CI excludes 0,
  with specificity intact (correct-answered refusal rise <= 5pt). Exact
  effect-size floor locks from the Stage-1 pilot via a pre-stated formula before
  the Stage-2 readout, so no goalpost can move.
- G1 (Stage 2, primary): coupled beats permuted on the bidirectional selectivity
  gap by >= 5pt, row-level bootstrap 95% CI (10k resamples) excluding 0. This is
  the whole claim: the propensity wire carries calibration information beyond a
  constant caution write, in both directions.
- G2 (Stage 2, specificity guard, pass/fail): on known_correct_answered rows,
  refusal rise <= 5pt and correctness drop <= 3pt vs baseline (the B1 and AC
  convention). The coupling must not sacrifice rows the model already gets right.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Stage 1 weak-lever PASS; Stage 2 small positive (3-10pt); nontrivial chance Stage 1 fails |
| user | Stage 1 PASS; Stage 2 PASS (yes and yes) |

## Outcome

Filled at resolve.
