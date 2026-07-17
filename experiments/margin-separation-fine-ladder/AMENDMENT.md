# Margin separation at fine ladder resolution (M1b)

Status: draft (not signed; do not launch as confirmatory evidence).

## Motivation and posture

M1 (experiments/margin-mapping, RESOLVED FALSIFIED 2026-07-17) measured
per-row commitment margins on a coarse ladder and failed the registered
censoring-aware separation criterion: observable bound 2.0 against the 2.5
floor. But M1's ladder quantized the achievable bounds to {2.0, 3.0}, with
nothing between: the criterion could not have returned any value in the
interval containing the floor. The confab median landed on the 0.75x rung
(9.456) with a bootstrap CI spanning down to the 0.5x rung (6.304), and the
critical bracket (0.5x, 0.75x] holds 53 of the 400 confab rows, including the
median row itself.

M1b asks the one question M1 could not answer: does the merged confab median,
measured at fine resolution inside that bracket, fall at or below the dose
where the bound reaches 2.5? The floor is UNCHANGED at 2.5; the instrument
gains the resolution to reach it exactly (the 0.6x rung is 18.912/2.5 to the
digit). If the criterion fails again at fine resolution, M1's falsification is
confirmed as real rather than a quantization artifact. If it passes, Claim 1's
registered separation holds at this operating point and the M1 result is
reinterpreted as resolution-limited, without reopening M1's own resolved
verdict.

Posture: exploratory instrument/mechanism tier, qwen35_4b only (mistral is
void by instrument loss per M1; the model-family decision is deferred to the
post-M4 memo). Reported separately, never pooled with the locked Phase 1
headline matrix. M1 stays resolved regardless of outcome.

## Design

Substrate, direction, dose law, decoding, detector stack, and criterion
conventions are all carried from M1 byte-identically (pins in `cell.yaml`).
Three design choices are new, each derived pre-sign from M1's committed
artifacts (derivation report committed at
`analysis-committed/design_derivation/m1b_design_report.json`; the derivation
first reproduced M1's committed median, CI, and censoring counts exactly):

1. **Fine ladder (Candidate C)**: multipliers {0.5, 0.55, 0.6, 0.65, 0.7,
   0.75, 1.5, 2.0} x reference_dose_abs. Only four rungs are newly generated
   (0.55x to 0.7x); the rest reuse M1 runlogs under RG0. Achievable bounds
   become {2.0, 2.1429, 2.3077, 2.5, 2.7273, 3.0}: the floor is exactly
   achievable and the bound is no longer forced to jump over it.

2. **Conditional population with a registered merge rule**: only the 53 confab
   rows whose M1 tipping fell in (0.5x, 0.75x] receive new generations (212
   total, 2.8% of M1's budget). For every other row the fine window cannot
   change the answer: rows with margin <= 0.5x are below every fine point,
   rows with margin > 0.75x are above every fine point, so their M1 values
   are carried unchanged. This conditioning is bias-free for the median
   question; the residual cost is CI coverage only, and only in the widening
   direction (bias note in `cell.yaml`).

3. **Known rows**: leg (b) depends only on the 1.5x/2.0x rungs, and 322/360
   known rows are right-censored above the top pre-collapse rung, so a fine
   ladder for knowns buys nothing (derivation, known_row_analysis). The
   Decision record leaves reuse-vs-regenerate as the one open PI choice.

Instrument configs pinned at sign: `cell.yaml`, `gates.yaml`.

## Decision record

Every knob is labeled DERIVED (from committed data), CONVENTION (carried from
a resolved experiment's registered convention), JUDGMENT (a choice with
rationale), or TO-DECIDE (open for the PI at sign).

1. **Rung set** (DERIVED): Candidate C from the design derivation. Beats
   Candidate A (quarter-x grid) on generation cost at equal floor
   resolvability (212 vs 468 generations) and beats Candidate B (log-spaced,
   14 rungs) which cannot achieve the floor exactly and triples the cost. The
   0.6x rung is included by construction so that bound = 2.5 is exactly
   achievable.
2. **Conditional population + merge rule** (DERIVED): bracket distribution
   from the pinned margin dataset: 181 rows at idx <= 4, 53 at idx 5, 166 at
   idx >= 6 or censored. Merge rule as in `cell.yaml`; SC3 asserts the
   181/166/53 partition at analysis time.
3. **Known-row evidence** (TO-DECIDE): Option 1 (recommended) reuses M1's
   1.5x and 2.0x runlogs byte-identically under RG0 (zero new generations;
   leg (b) and the collapse-cliff evidence carry over; pins already in
   cell.yaml). Option 2 regenerates both rungs fresh (720 generations) as an
   M1b-native replicate that hedges against artifact staleness. The
   orchestrator recommends Option 1: the RG0 rule is the same one M1 itself
   used for the dose-0 baseline, the artifacts are pinned by sha256, and the
   rg0_drift_check (item 7) independently verifies that the substrate still
   reproduces M1 outputs byte-identically before the full run.
4. **Floor and pass/fail convention** (CONVENTION): observable bound floor
   2.5, point estimate as the pass/fail surface, CI descriptive. Carried
   verbatim from M1's registered criterion and its resolved adjudication
   convention. Registering a fresh experiment against the same floor is the
   sanctioned path; the floor itself never moved.
5. **Numerator = 18.912281876699964, the 1.5x rung** (DERIVED): M1's Outcome
   records total well-formedness collapse at the 2.0x rung in both roles, so
   the highest pre-collapse rung on the M1b ladder is 1.5x. The four new
   rungs all sit at or below 0.7x and cannot create a new collapse cliff
   above 1.5x. Equivalent criterion form: PASS iff merged confab median
   <= 7.564912750679985.
6. **Detector validity** (CONVENTION + JUDGMENT): detector_v2 byte-identical
   from the M1 stack (CONVENTION). M1's CG1 PASS covered this operating point
   on a 700-row slice stratified across rungs including both endpoints of the
   fine window; the new rungs are interior interpolations. JUDGMENT: a fresh
   100-row blinded calibration slice (25 per new rung, seed 48260720, same
   CG1 floors and 0.05 disagreement gate, hash-commit-before-unblind) is run
   on the new generations as a drift check; exceedance voids the refined
   margin values for criterion use.
7. **Drift guards** (JUDGMENT): mandatory GPU preflight at the 0.55x and 0.7x
   rungs (standing directive), M1's amended dose-readback rule carried
   verbatim, and a NEW rg0_drift_check: 8 of the 53 refined rows regenerated
   at 0.75x and byte-compared to M1's pinned runlog before the full run; any
   mismatch halts. Rationale: the merge rule leans on M1 endpoint values
   being reproducible on today's environment; this check converts that
   assumption into evidence for 8 generations of cost.
8. **Seeds** (CONVENTION): bootstrap 48260719, calibration slice 48260720,
   continuing the registered lineage increment (M1: 48260714-16, M2:
   48260717-18).
9. **Design-info disclosure** (CONVENTION): the derivation's outcome
   estimates, P(bound >= 2.5) = 0.6727 under the empirical interval model and
   0.5311 under M1's committed probit fit, are disclosed to both predictors
   before calls are registered, mirroring M1's threshold-derivation
   transparency. Self-blinding holds structurally: the headline quantity
   depends on generations that do not exist yet, and no merged median or
   bound has been computed pre-sign.

## Prediction

At fine ladder resolution the merged confab median margin falls at or below
the 0.6x rung (7.564912750679985), so the censoring-aware observable bound
reaches the registered 2.5 floor with both legs passing: Claim 1's separation
holds as registered at the qwen mid-band operating point, and M1's criterion
failure is attributed to ladder quantization.

## Falsifier

With all gates valid, the merged confab median lands above the 0.6x rung
(point-estimate bound in {2.0, 2.1429, 2.3077}), failing the 2.5 floor at
fine resolution: the separation failure is real, not a quantization artifact,
and Claim 1 remains falsified at this operating point with the resolution
excuse removed.

## Gates

See `gates.yaml` (pinned at sign). Integrity: SC0 provenance/staging with the
pre-committed 53-row id list and the rg0_drift_check; SC1 dose readback (M1's
amended OR-rule) plus mandatory GPU preflight at the new-rung extremes; SC2
blinded calibration with CG1 floors and the 0.05 disagreement gate; SC3
coverage plus the 181/166/53 merge-provenance audit. Criterion: P1 both legs
plus bound >= 2.5 (point estimate). Construct: C1 non-monotone ceiling 0.05
on the refined subset's merged fine sequence; on_failure instrument void,
reported straight.

## Predictions scoreboard

Registered at sign, after design-info disclosure (Decision record item 9).

| Predictor | Slot 1: P1 separation at fine resolution | Slot 2: merged-median landing rung |
|-----------|------------------------------------------|-------------------------------------|
| orchestrator | | |
| user | | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
