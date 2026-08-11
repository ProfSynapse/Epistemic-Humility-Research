# ao-propensity-regulated-caution

Status: null-result, run 2026-07-06 (machine state in `experiment.yaml`);
verdict NULL on Stage 1 knob validation, Stage 2 does not run per the
falsifier (see AMENDMENT.md "Outcome" and experiment.yaml `verdict:`). This
header was stale boilerplate reading "draft (not signed)" until 2026-08-11;
corrected to match the machine state, which was already `null-result`.
Tier-2 exploratory local mechanism evidence, never pooled with the locked
Phase 1 matrix.

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

Stage 1 (knob validation): RESOLVED — NULL. No caution direction validates as a
behavioral lever on the AI-TRUE checkpoint. Stage 2 does NOT run, per the
Falsifier pre-registration ("If Stage 1 fails ... the coupling stage does not
run; the reported result is 'no caution actuator on this checkpoint'").

Run: local RTX 3090, single seed, 2026-07-06. Two candidate directions
(caution_perp refit; mass-mean answer-vs-refuse fallback), four arms each
(baseline/ablate/shift_up/shift_down), 320 rows/arm = 1280 rows/candidate. Both
runs completed 1280/1280 with smoke passed (write_ok, parity_ok, gen_stream_fired
all true, write error within tolerance), so the intervention provably fired and
wrote: the null is a behavioral no-move, not an instrument failure.

G0 movement leg (bidirectional_gap_diff, seed 20260706, n_boot 10000,
pos_cell=known_correct_answered, neg_cell=answerable_refused, indicator=refused):
FAILS for all four candidate x arm combinations. Every bootstrap CI includes 0.

| candidate | arm | diff | 95% CI | excludes 0 |
|-----------|-----|------|--------|-----------|
| caution_perp | ablate | 0.0380 | [-0.0129, 0.0936] | no |
| caution_perp | shift_down | 0.0269 | [-0.0176, 0.0801] | no |
| fallback_mass_mean | ablate | 0.0047 | [-0.0327, 0.0444] | no |
| fallback_mass_mean | shift_down | 0.0000 | [-0.0263, 0.0263] | no |

Baseline refusal is at ceiling on the over-refusal tail (answerable_refused
111/114 = 0.974) and floor on known_correct_answered (0/90 = 0.000) for both
candidates (byte-identical baselines from independent processes, a determinism
cross-check). The point effects are near zero, not merely wide-CI, so this is a
genuine no-effect rather than an underpowered real effect.

Specificity legs:
- Refusal-rise on known_correct_answered (measured): caution_perp/ablate
  5/90 = 0.056 FAILS its own <=0.05 threshold; caution_perp/shift_down
  4/90 = 0.044, fallback both arms pass. Moot for the verdict, movement already
  fails.
- Correctness-drop: UNMEASURED / N/A. A tuner grader bug (below) left
  correct/baseline_correct null on every row, so this leg could not be computed.
  It is NOT recorded as a pass.

Independent verification: the G0 movement numbers were reproduced to the 4th
decimal by two independent code paths (a fresh re-implementation calling the
tuner's own bidirectional_gap_diff, and the run agent's diagnostic); pool-to-row
join 320/320 unambiguous on both candidates.

Two tuner infra defects surfaced by this run (both fixed on tuner main AFTER the
run, so they do not affect the recorded numbers, which were recovered by joining
the class label back from the pool on row_key):
- Grader row-context: MechInterp/cli._run_one_pass dropped pool-row fields
  (cell/aliases) before grading, so cell was null on every row (score-gates could
  not group) and correctness was ungradeable. Fixed: tuner PR #136 (f59cb22).
- Config-sha drift guard was self-referential (hashed expected_config_sha into
  its own hash), so it could never be satisfied. The guard was left unset for
  this run (skipped), so the run is valid. Fixed: tuner PR #137 (a6e9464).

Scope: whether a caution lever exists on any raw-base / instruct surface remains
OPEN and is pursued separately (dark actuator screen on the AK Stage-1
confab-rich surface, 309 confab). The GRPO-v2 fast-follow is not licensed by this
cell, since Stage 1 did not establish a lever on AI-TRUE.

Predictions scored straight: orchestrator called "nontrivial chance Stage 1
fails" (partial credit); user called "Stage 1 PASS" (missed).
