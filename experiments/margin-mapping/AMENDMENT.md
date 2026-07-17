# Margin mapping: per-row tipping dose along the known-unknown direction

Status: draft (not signed; do not launch as confirmatory evidence). All
sign-time knobs are marked TO-DECIDE and resolve at sign with PI decisions
recorded in the Decision record; no threshold moves after any result is
known.

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

Dose ladder (TO-DECIDE 1): a geometric ladder in setpoint units spanning
well below the confab regime to above the known-collapse regime. Drafter
proposal: 10 rungs per family at {0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64}
x the family reference dose_abs. The top rungs deliberately enter the
overdrive regime so the known-margin tail and the collapse boundary are
observed, retrodicting the H4 anchor qualitatively.

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

- **Margins do not separate (primary).** Median known margin / median
  confab margin below the separation floor (TO-DECIDE 4; drafter proposal
  2.0), OR the bootstrap 95% CI on the median ratio includes 1.0. Then
  epistemic state is not usefully encoded as distance-to-boundary along
  c_hat and framework Claim 1 is falsified at these operating points.
- **Setpoint placement fails.** The family reference setpoint does not lie
  between the two margin medians in either family. Then the mid-band regime
  account (framework Claim 2) is wrong even if margins separate.
- **Retrodiction fails.** Predicted arm rates from the margin CDFs miss the
  observed factorial or doubt-snap anchor rates by more than the tolerance
  (TO-DECIDE 5; drafter proposal 0.10 absolute per retrodicted rate). Then
  margins exist but do not carry the dose-regime mechanism.
- **Construct integrity.** Non-monotone fraction above the ceiling
  (TO-DECIDE 6; drafter proposal 0.15) in either family's confab
  population, OR the detector-vs-adjudication calibration gate fails. Then
  the margin construct or its readout is unsound and no framework claim is
  evaluated (instrument void, reported straight).

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

## Decision record (TO-DECIDE; resolves at sign)

1. Dose ladder rungs and span (drafter: 10 geometric rungs, 0.125x to 64x
   family reference dose_abs).
2. Population subsample (drafter: 400 confab by registered seed + full
   known pool, per family).
3. Primary readout (drafter: detector-v2 staircase + one blinded
   calibration shard per family with a 0.05 disagreement gate).
4. Separation floor on the median margin ratio (drafter: 2.0).
5. Retrodiction tolerance (drafter: 0.10 absolute per anchor rate).
6. Non-monotone ceiling (drafter: 0.15).
7. Right-censoring policy confirmation (drafter: censored at top rung,
   never imputed, censored fraction reported per role).

## Predictions scoreboard

Registered at sign, before any generation. No edits after results.

| Predictor | Margins separate (ratio at or above floor) | Setpoint placement | Retrodiction within tolerance | Band for median margin ratio (qwen / mistral) |
|-----------|------|------|------|------|
| orchestrator | | | | |
| user | | | | |

## Outcome

Filled at resolve. Record the verdict, the gate results, per-family margin
distributions (medians, IQRs, censored fractions, non-monotone fractions),
the retrodiction table (predicted vs observed per anchor), and the
one-sentence summary that also goes into `verdict:` in the manifest.
