# Margin mapping: per-row tipping dose along the known-unknown direction

Status: SIGNED 2026-07-17 (bin/exp sign; cell.yaml + gates.yaml pinned in
experiment.yaml). All sign-time knobs resolved in the Decision record;
predictions registered in the scoreboard below before any generation. No
threshold moves after any result is known. Launch authorized by the PI on
the free local 3090 ("get this running", 2026-07-16), GPU preflight
mandatory before the full run.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Exploratory instrument/mechanism tier, reported separately from every locked
surface. This is experiment M1, the keystone of the margin-theory cascade
(`docs/research/margin-theory-framework.md`, section 4).

The gate-contribution factorial resolved FALSIFIED on the gate axis in both
families: at the mid-band operating points the dosed c_hat write self-sorts
(permuted-gate confab abstention 0.550 qwen / 0.600 mistral vs baselines
0.083 / 0.282) and the true gate adds only a sub-floor increment
(`experiments/gate-contribution-factorial/AMENDMENT.md`, Outcome, resolved
2026-07-16). The registered reconciliation with the opposite attribution at
Qwen3-4B/L34/dose-200 (`experiments/ungated-vs-gated-dose-matched/
AMENDMENT.md`, Outcome, Binding scope statement 2) is that the write's
content-selectivity is operating-point-dependent.

Margin theory proposes the mechanism: each row has a commitment margin, the
minimum dose along the write direction that flips its behavior to
abstention. Confab-prone rows have short margins, well-supported known rows
long ones, and who supplies selectivity is determined by where the dose
lands relative to the two margin distributions. This experiment measures
those distributions directly, per row, for the first time. Every later
cascade stage (susceptibility-as-probe M2, anisotropy M3,
evidence-responsiveness M4, training bridge M5) consumes this dataset.

## Design

Substrate and direction: the two frozen mid-band operating points, reused
byte-identically from the factorial staging: Qwen3.5-4B hs20 with the frozen
c_hat (setpoint reference dose_abs 12.608) and Mistral-7B-Instruct-v0.3 hs16
(reference dose_abs 3.665), pinned revisions as in the factorial cell.yaml.
No gate anywhere: every row in the population is dosed at every ladder step
(margins are a per-row property; gating would censor exactly the rows we
need).

Arms: one generation pass per ladder dose per family, greedy, wide
two-instrument render stack reused from the factorial. Baseline (dose 0) is
reused from the factorial baseline arm (RG0 byte-repro check on reuse).

Dose ladder (TO-DECIDE 1): a geometric ladder in setpoint units. The
original drafter span (0.125x to 64x) was REVISED after the pre-sign
threshold derivation
(`analysis-committed/threshold_derivation/threshold_derivation_report.json`,
computed 2026-07-17 from the doubt-snap hs20 permuted-gate row-level dose
ladder, which is the identical substrate/site/direction M1 uses): on that
prior measurement, well-formedness collapses to 0.000 at dose_abs 25.2
(2.0x the M1 reference), so rungs at 4x and above would spend roughly half
the generation and adjudication budget on rows that can only score
not-well-formed. Revised drafter proposal: 10 rungs at {0.0625, 0.125,
0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4} x the family reference dose_abs:
half-octave density through the expected confab-median region (fitted
confab median 7.51 dose_abs = 0.60x on qwen) and the setpoint, with the
top two or three rungs bracketing the expected collapse boundary so the
per-row collapse dose is still measured (the overdrive/H4 anchor is
retrodicted from the collapse boundary's existence, not from deep-overdrive
rungs). The GPU preflight (Gates) locates each family's actual collapse
region at the rung extremes before the full run; mistral has no prior
ladder, so its preflight is the only collapse evidence and may move its top
rungs at sign-recorded launch time under the authorized-knob rule.

Population (TO-DECIDE 2): margins require many generations per row, so the
population is a registered subsample of the factorial pools. Drafter
proposal: per family, 400 confab rows + the FULL known-correct pool (360
qwen / 382 mistral; knowns are the scarce population and the H4
retrodiction target), drawn by a registered permutation seed, opaque-id
list committed before any generation. At 10 rungs this is ~7,600 rows per
family (~15,200 total), roughly 4.5 hours per family on the 3090 at
factorial throughput.

Per-row deliverables, computed from the ladder:

- **Tipping dose (commitment margin)**: the smallest ladder dose at which
  the row's output is an abstention (refused_final under the primary
  readout, definition below) AND well-formed. Rows that never tip inside
  the ladder are recorded right-censored at the top rung, reported
  straight, never imputed.
- **Collapse dose**: the smallest ladder dose at which well-formedness is
  lost (the overdrive signature). Right-censored likewise.
- **Monotonicity flag**: rows whose abstention status is non-monotonic
  across the ladder (abstains at dose d, answers again at some d' > d) are
  flagged and reported as a separate class; their margin is the FIRST
  tipping dose, and the non-monotone fraction is a registered readout (a
  high fraction would undermine the margin construct itself; see
  Falsifier).

Primary readout (TO-DECIDE 3): full blinded adjudication of ~15,200 rows
(~20 shards) is the factorial-grade instrument but roughly doubles the cost
of the experiment. Drafter proposal: detector-v2 is the PRIMARY margin
readout for the staircase, with a registered blinded-adjudication
CALIBRATION slice (one shard-equivalent per family, ~700 rows sampled
across rungs and roles by a registered seed, clear-positive and
clear-negative decoys per the factorial recipe, CG1 floors unchanged). The
gate: detector-vs-adjudication disagreement on the calibration slice at or
below 0.05 on the abstention bit; if exceeded, the margin dataset is voided
for criterion use and the experiment reports the disagreement straight
(remedy: full-pool adjudication as a separate signed follow-up, never a
silent upgrade).

Retrodiction targets (fixed at sign, read from governed docs): the three
anchor results as cited in `docs/research/margin-theory-framework.md`
section 1. The procedure: from the measured margin CDFs, predict each
anchor's arm-level rate at its operating dose (factorial permuted/true arms
at the reference setpoints; doubt-snap permuted knowns at hs20 dose 8). The
H4 anchor (L34, dose 200, different site and substrate) is retrodicted
QUALITATIVELY only: the known-margin CDF must place the mid-band setpoint
below the known tail, and a collapse regime must exist at finite ladder
dose.

Instrument configs pinned at sign: cell.yaml (ladder, populations, seeds,
substrates, readout definitions), gates.yaml (floors below).

## Prediction

At the mid-band operating points, per-row commitment margins separate
confab from known rows with a gap containing the current setpoints: the
median known margin exceeds the median confab margin by at least the
separation floor, the family setpoint lies between the two medians, and the
measured margin CDFs retrodict the factorial and doubt-snap arm rates
within tolerance, while the ladder's top rungs exhibit the collapse regime
that explains H4's overdrive non-selectivity.

## Falsifier

Pre-stated numerically; every threshold resolves in the Decision record at
sign and does not move after results.

- **Margins do not separate (primary, censoring-aware).** The threshold
  derivation implies known margins are mostly right-censored within the
  coherent-output regime (fitted known median 229.7 dose_abs on qwen,
  far above the ~25 dose_abs collapse boundary), so a raw median ratio is
  not observable and must not be the criterion. Primary criterion, both
  legs required per family: (a) the median confab margin is at or below
  the family reference setpoint; (b) the median known row is right-censored
  above the highest pre-collapse rung (at least 50% of known rows neither
  tipped nor collapsed there), so the OBSERVABLE ratio lower bound (highest
  pre-collapse rung / median confab margin) meets the separation floor
  (TO-DECIDE 4; derived drafter proposal 2.5, from expected bound 3.4 with
  confab-median CI [6.86, 8.24] giving bound range 3.06-3.67 on qwen and
  headroom for collapse-location uncertainty). The FITTED median ratio
  (probit-in-log-dose primary, logistic sensitivity; derived expectation
  30.6 [5.39, 236] qwen, 39.2 [5.93, 322] mistral, lower-5% quantiles
  5.86 / 6.37) is reported descriptively with both parametric forms, never
  as the pass/fail surface. Failure of either leg falsifies framework
  Claim 1 at these operating points.
- **Setpoint placement fails.** The family reference setpoint does not lie
  between the two margin medians in either family. Then the mid-band regime
  account (framework Claim 2) is wrong even if margins separate.
- **Retrodiction fails.** Predicted arm rates from the margin CDFs miss the
  observed anchor rates by more than the tolerance (TO-DECIDE 5; derived
  drafter proposal 0.10 absolute: max per-anchor tolerance 0.063 assembled
  from observed-rate Wilson half-widths plus fit-propagated prediction
  half-widths, rounded up). Retrodiction targets are restricted to the
  PERMUTED-gate and baseline anchors (fired-conditional rates: qwen
  permuted confab 0.693 [0.664, 0.720] and known 0.065 [0.041, 0.100];
  mistral 0.692 [0.663, 0.720] and 0.051 [0.031, 0.082]); true-gate arms
  are excluded because their gate-selected fired sets are structurally
  unpredictable from a no-gate margin CDF, and the doubt-snap dose-8 known
  anchor is flagged in-sample (the fit trains on that ladder). Then margins
  exist but do not carry the dose-regime mechanism.
- **Construct integrity.** Pre-collapse non-monotone fraction above the
  ceiling (TO-DECIDE 6; derived drafter proposal 0.05 confab / 0.10 known,
  from observed 0.0102 (n=685) and 0.0203 (n=197) plus 3 SE rounded up;
  post-collapse reversals are collapse artifacts and are excluded by
  construction), OR the detector-vs-adjudication calibration gate fails.
  Then the margin construct or its readout is unsound and no framework
  claim is evaluated (instrument void, reported straight).

There is no rescoring lane; a failed criterion falsifies the corresponding
framework claim and the result stands.

## Gates

Wilson 95% CIs on every rate; bootstrap 95% CIs on every median and ratio.
Integrity gates inherited from the factorial: SC0 staging with committed
ID-manifests and RG0 byte-repro on every reused artifact; SC1 per-row
readback within relative 0.005 of the commanded ladder dose at every rung,
with the mandatory GPU preflight (rows per family at the rung extremes,
readback verified against setpoint) before the full run and live
first-batch assertions with hard abort (PI standing directive 2026-07-16);
SC2 hash-commit-before-unblind for the calibration adjudication slice, CG1
floors unchanged from the factorial; SC3 paired coverage, zero silent
drops, censored rows reported as censored per role.

Criterion gates: separation floor, setpoint placement, retrodiction
tolerance, non-monotone ceiling, calibration-slice agreement floor (all
TO-DECIDE values resolve at sign).

## Decision record (drafted as TO-DECIDE; RESOLVED at sign, 2026-07-17)

Resolution: the PI registered scoreboard predictions and directed launch
("get this running"); all seven knobs adopt the derived values where
DERIVED and the drafter proposals where JUDGMENT, lead-confirmed, recorded
below. The mistral top-rung preflight adjustment (item 1) is the single
authorized launch-time knob.

Knob values were re-derived pre-sign from existing artifacts where the data
allows (`analysis-committed/threshold_derivation/`; script and report
committed; inputs: factorial fired-conditional rates re-derived row-level,
doubt-snap hs20 permuted-gate row-level dose ladder 685 confab / 197 known
rows, pre-collapse rungs only). Each item below is labeled DERIVED (value
computed from data, assumption stated) or JUDGMENT (not resolvable from
existing artifacts). All resolve at sign with PI decisions.

1. Dose ladder rungs and span. PARTLY DERIVED: span revised to {0.0625,
   0.125, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4} x reference after the collapse
   finding (prior 4x-64x rungs sit past the observed dose_abs 25.2
   collapse on the identical qwen substrate/site); rung count and spacing
   within the span remain JUDGMENT. The per-family collapse location for
   M1's own run is preflight territory (GPU, rung extremes, before full
   run); mistral has no prior ladder so its preflight is decisive there.
2. Population subsample. DERIVED: n_confab = 400 (Wilson half-width 0.049
   at worst-case p=0.5, clearing the 0.05 bar that n=200 fails at 0.069) +
   full known pool per family (not a knob; whole population).
3. Primary readout (detector-v2 staircase + one blinded calibration shard
   per family with a 0.05 disagreement gate). JUDGMENT: instrument-design
   choice, not data-derivable.
4. Separation floor. DERIVED, reformulated censoring-aware: observable
   ratio bound floor 2.5 (expected bound 3.4, range 3.06-3.67 over the
   confab-median CI on qwen; the raw fitted ratio 30.6/39.2 with lower-5%
   quantiles 5.86/6.37 is reported descriptively only, since the known
   median is extrapolated far past the observed dose range and moves 2-3x
   between probit and logistic forms).
5. Retrodiction tolerance. DERIVED: 0.10 absolute (max per-anchor 0.063,
   rounded up), permuted + baseline anchors only; true-gate anchors
   excluded structurally; doubt-snap known anchor flagged in-sample.
6. Non-monotone ceiling. DERIVED: 0.05 confab / 0.10 known (observed
   0.0102 / 0.0203 plus 3 SE, pre-collapse regime only).
7. Right-censoring policy. JUDGMENT, with derived context: censored at top
   rung, never imputed, censored fraction reported per role. The
   derivation implies MOST known rows will right-censor within the
   coherent regime (fitted known median 229.7 dose_abs vs collapse ~25);
   that is the expected signature of Claim 1, not a defect, and the
   criterion (item 4) is built on the censoring-aware bound for exactly
   this reason.

## Predictions scoreboard

Registered at sign (2026-07-17), before any generation. No edits after
results. PI calls stated verbatim in conversation: slot 1 "Qwen pass mistral
fail same with 2", slot 3 "pass both", slot 4 "pass" (recorded as
axis-implied bands, no independent numeric band registered).

| Predictor | Separation (censoring-aware, per family) | Setpoint placement (per family) | Retrodiction within 0.10 | Bands |
|-----------|------|------|------|------|
| orchestrator | qwen PASS, mistral PASS (uncertain) | qwen PASS, mistral PASS | PASS both | observable bound qwen 3.0-3.7, mistral 2.5-4.5; fitted ratio qwen 15-60, mistral 8-80; known censored fraction at top coherent rung qwen 0.80-0.95, mistral 0.60-0.90 |
| PI | qwen PASS, mistral FAIL | qwen PASS, mistral FAIL | PASS both | axis-implied only: qwen observable bound >= 2.5, mistral < 2.5 |

The differentiating slots are the MISTRAL separation and placement legs: the
orchestrator predicts the censoring story holds on mistral (knowns survive
to the top coherent rung), the PI predicts mistral fails both (consistent
with reading mistral's S1 failure as generic boundary proximity: knowns tip
by 2-4x and the censoring signature does not hold there). A mistral FAIL
with qwen PASS would make boundary anisotropy (framework Claim 4) govern
the family scope of Claim 1. Whichever way mistral lands, exactly one
predictor's call survives; adjudicated in the Outcome, no edits after
results.

## Outcome

Resolved 2026-07-17, qwen35_4b only. Mistral7b_v03 is VOID_INSTRUMENT_LOSS:
its hs16 direction vector was destroyed in the 2026-07-17 worktree-sweep
incident, reconstruction failed the pre-registered byte-identity acceptance
rule (bf16 forward-pass non-determinism; forensics found no capture-
convention discrepancy), and the PI directed the qwen-only fallback before
any mistral staircase data existed. All mistral criterion and scoreboard
slots are unscored; the loss is incident-driven, not results-driven.

Criterion verdicts (qwen35_4b; full adjudication trail and red-team review
in NOTEBOOK 2026-07-17):

- **P1 separation (censoring-aware): FAIL.** Median confab margin 9.456
  dose_abs (bootstrap 95% CI [6.304, 9.456]) satisfies leg (a) against the
  setpoint 12.608, and 70.0% of known rows (Wilson CI [0.651, 0.745])
  neither tipped nor collapsed at the highest pre-collapse rung (1.5x,
  18.912 dose_abs; the 2.0x rung is 0.000 well-formed both roles),
  satisfying the 50% clause. The observable ratio lower bound fails:
  18.912 / 9.456 = 2.0 < floor 2.5 (bootstrap CI [2.0, 3.0]; the bound is
  rung-quantized, so 2.0 and 3.0 are the only achievable values near the
  floor). Framework Claim 1 is falsified at the qwen mid-band operating
  point as registered. Red-team note: the floor-derivation prose's
  "expected bound 3.4" contained a one-rung numerator error (it used the
  collapse-boundary dose 25.216 while naming the highest pre-collapse
  rung); under the correct numerator the derivation-time expectation was
  2.52 against the 2.5 floor, and the realized confab median landed one
  rung above the fitted expectation (9.456 vs 7.506). The criterion as
  written is unambiguous and the floor does not move.
- **P2 setpoint placement: PASS.** The setpoint 12.608 lies between the
  confab median (9.456) and the known censored region (above 18.912).
- **P3 retrodiction: PASS** under both parametric forms (tolerance 0.10
  absolute). Probit primary: permuted_confab predicted 0.618 vs observed
  0.693 (err 0.075); permuted_known 0.063 vs 0.065 (0.002);
  baseline_confab 0.000 vs 0.083 (0.083); baseline_known 0.000 vs 0.000
  (0.000). Logistic sensitivity agrees (max err 0.083). Doubt-snap dose-8
  known anchor excluded as in-sample per registration. Caveat recorded:
  permuted anchors are only weakly out-of-sample relative to M1's own
  ladder, and baseline anchors are predicted zero by construction, so P3
  is supportive rather than strongly independent.
- **C1 construct integrity: PASS.** CG1 attempt 1: clear-negative 52/52,
  clear-positive 51/52, detector-vs-adjudication disagreement 20/700 =
  0.029 vs ceiling 0.05. Non-monotone: confab 14/400 = 0.035 (ceiling
  0.05), known 4/360 = 0.011 (ceiling 0.10).

Margin distributions (qwen35_4b, dose_abs): confab median 9.456, IQR
1.576-18.912, tipping-censored 92/400 (0.230); known tipping-censored
322/360 (0.894), median above the coherent regime (recorded at the top
ladder rung 50.433 per Decision record item 7, lower-bound-only),
IQR 18.912-50.433; collapse-censored 0/760, with total well-formedness
collapse at the 2.0x rung (25.216) in both roles. Fitted median ratio,
descriptive only: probit 42.18 [9.02, 187.05], logistic 16.82 [4.46,
58.41]. Non-monotone fractions as under C1.

Predictions scoreboard adjudication (qwen slots; mistral slots void):
both predictors called qwen separation PASS and were WRONG. Both were
right on qwen placement, retrodiction, and the H4 qualitative slot
(setpoint below the known censored tail; total collapse regime at finite
ladder dose). Orchestrator bands: observable bound 3.0-3.7 MISS (realized
2.0), fitted ratio 15-60 HIT (probit 42.18), known censored fraction at
top coherent rung 0.80-0.95 MISS (0.700). PI axis-implied qwen bound
>= 2.5 MISS. Both predictors' band expectations inherited the derivation
numerator error. The differentiating mistral slots are void; no winner
is declared.

One-sentence summary (manifest `verdict:`): qwen mid-band margins are
mechanistically real and correctly placed (P2, P3, C1 pass; retrodiction
within 0.083) but the registered censoring-aware separation criterion
fails (observable bound 2.0 vs floor 2.5), falsifying framework Claim 1
as registered at this operating point; mistral is void by instrument
loss.
