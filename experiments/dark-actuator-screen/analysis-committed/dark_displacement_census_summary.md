# Dark displacement census - structure outside the named epistemic axes

Lab-notebook diagnostic (no gates, no claims). Branch
`lab-dark-displacement-census`. Script:
`experiments/dark-actuator-screen/dark_displacement_census.py`. Seed 20260706, CPU only.
Full machine-readable output (spectra, per-component stats, frozen candidate
direction JSONs) is UNTRACKED under
`experiment/phase1/probe/analysis/dark_displacement_census/census_report.json`.

## Question

Item-20 found ~99% of generation-time displacement outside the
doubt/caution_perp plane, but on n=41 all-confabulation rows at one checkpoint
(`diag_item20_gentime_decomposition.py`, staging `diag-item20-gentime-r2`; see
TODO row 20). The session-0035 MI fleet found the prime writes 92-99% off every
readable axis, and caution survives 40 direction removals. This census re-runs
that measurement on a 33x larger surface with a refuse-arm contrast, and then
asks whether the dark remainder is isotropic noise or structured latent
directions worth freezing as steering candidates.

## Surface

Amendment AK Stage 1 per-position captures (staging
`professorsynapse/eh-al-prep-staging`, tags `ak-stage1-raw-base-r1` and
`ak-stage1-grpo-v2-r1`; each `tensors/ak_stage1_tensors.tar.gz` + `data/rows.jsonl`).
1,338 rows per arm, dim 2560, float32. The pool is unanswerable-only
(`label == unknown`), so the ONE outcome axis available is confab-vs-refuse
(309 confab / 1,029 refuse). Captured layers L16 L20 L24 L28 L34; captured
positions anchor, first_visible(==answer_k0), answer_k0..answer_kN (stride 4),
answer_end. Tensor keys `"<layer>@<pos>"`.

Two displacement families per row per layer:
`succ` = successive per-position delta `h_{t+1} - h_t` over the answer window;
`arel` = anchor-relative `h_t - h_anchor`.

## Named-axes span projected out

Per layer, an orthonormal basis (QR of the block, not sequential rank-1s) of:
`refuse` (pool mean(refuse) - mean(confab) anchor direction, per layer),
`propensity` (pool confab-vs-refuse logistic direction in raw space, per layer),
and `doubt` (the frozen AH answerability probe raw direction, available only at
L20/L24/L28). The steering gate/dial directions and the L35 `caution_perp`
artifact are on a different model/layer and were NOT applied here - documented
negative. Because `refuse` and `propensity` are fit on the SAME pool, removing
them is the strongest reasonable definition of "named" structure, so the dark
fraction reported below is a conservative (upper-bounded) estimate, not inflated.

## Result 1 - the displacement is overwhelmingly dark, and it replicates item-20

Fraction of per-position displacement variance OUTSIDE the named-axes span,
across all 20 (arm x layer x family) surfaces:
**0.964 - 0.999, median 0.994.** The named epistemic axes account for a median
of 0.6% (worst case 3.6%, at grpo-v2 L24/L28 anchor-relative) of where the
residual stream actually moves during generation. This holds on BOTH the raw
base and the deployed grpo-v2 checkpoint, and on both the successive-step and
anchor-relative families, so the item-20 ~99% finding survives the refuse-arm
contrast it flagged as missing (item-20 was 41 all-confab rows at grpo-v2 only;
this is 1,338 rows x confab+refuse x two checkpoints).

## Result 2 - the dark remainder is STRUCTURED, not isotropic noise

PCA of the residual (span-projected) deltas, pooled per surface:
participation-ratio effective rank **4.4 - 12.7, median 8.6** out of 2560; top-1
residual PC share **0.098 - 0.438** (median 0.160), top-5 **0.36 - 0.69**
(median 0.50), top-20 **0.58 - 0.96** (median 0.73). Isotropic noise in 2560
dimensions would have an effective rank of order 2560 and per-PC shares of order
1/2560. The dark subspace is instead a low-rank object: a handful of directions
carry most of the off-axis motion. 378 of 400 inspected components (94%) are
cross-row consistent (top-k half-fit |cosine| >= 0.6 between disjoint row
halves). So the remainder is real, low-dimensional, reproducible structure, not
sampling dust.

## Result 3 - but the structure is only WEAKLY tied to the confab-vs-refuse outcome

The interesting negative. Once a component is required to be non-nuisance
(|correlation| with answer length, absolute token position, and normalized step
all < 0.15) AND cross-row consistent (>= 0.6), its pooled confab-vs-refuse
separation collapses to **AUROC 0.58 - 0.72**. The components with the highest
raw outcome separation are the ones most correlated with answer length and token
position (correlations up to +0.5 to +0.7): confab rows generate longer answers,
so anchor-relative displacement magnitude tracks the outcome as bookkeeping, not
cognition. A row-level aggregated AUROC (mean component score per row) returns
implausible 0.97-0.99 values precisely because row-mean aggregation re-injects
that length signal; it is reported in the JSON but explicitly NOT used to gate,
and flagged in the script docstring as length-confounded. The honest instrument
is the pooled per-vector AUROC under the strict nuisance filter, and by that
instrument the dark structure does not encode the one outcome this pool exposes.

## Result 4 - the dark subspace does not transfer well across checkpoints

Mean best |cosine| of each raw-base top-component matched against the grpo-v2
top-components: **0.25 - 0.31** across every surface (individual frozen
candidates 0.15 - 0.52). The dark subspace is reproducible WITHIN a checkpoint
(half-fit consistency ~0.9-1.0) but largely re-oriented BETWEEN raw-base and
grpo-v2. Combined with Result 3, this means post-training rotates the dark
directions rather than sharpening a shared off-axis outcome code.

## Ranked knob candidates

12 raw-base components clear all gates (consistency >= 0.6, pooled AUROC >= 0.60,
all three nuisance correlations < 0.15); ZERO grpo-v2 components clear them.
Frozen as direction JSONs in the frozen-direction schema the AN section-6 knob
screen consumes, under the untracked analysis dir
(`dark_cand_raw-base_<layer>_<family>_pc<idx>.json`). They are genuine, stable,
non-bookkeeping off-axis directions, but their outcome AUROC (0.60-0.72 pooled)
is modest and they do not transfer to the deployed checkpoint, so they are
weak-prior steering candidates only - worth a dose screen, not a claim. The
strongest by within-checkpoint consistency is `L34 succ pc0`
(consistency 1.000, transfer 0.475, rising trajectory); by transfer,
`L20 succ pc5` and `L28 arel pc11` (both ~0.515).

## Screens against the dark-displacement literature map

Before treating any of the 12 candidates as undiscovered epistemic structure,
each is walked through the three decision signatures the companion
[dark-displacement literature map](../../../../docs/research/dark-displacement-literature-map.md)
names as the cheapest nuisance identities to rule out. The screens run PER
CANDIDATE DIRECTION, so the candidate set is exactly the 12 above; the screens
judge them, they do not redefine them.

- **Input linear-predictability** (SAE dark matter, litmap row 4). Out-of-fold
  R^2 of a ridge map from the row anchor (the last prompt-token hidden state at
  the same layer) to the candidate's per-position activation, on a fold-local
  label-agnostic input PCA. A direction whose activation is a linear image of the
  input is bookkeeping, not a knob. Ceiling: R^2 < 0.50. The anchor is constant
  within a row (these captures hold no per-position pre-layer input), so this
  screen targets row-level input-linear bookkeeping; position-varying bookkeeping
  is the positional screen's job.
- **Positional carrier** (position/context bookkeeping, litmap row 2). Out-of-fold
  R^2 of a low-frequency Fourier basis of the absolute token index. A direction
  tracking position is a spiral carrier, not epistemic content. Ceiling: R^2 < 0.30.
- **Rogue load** (massive activations / rogue dimensions, litmap row 1). Fraction
  of the direction's L2 energy sitting on the layer's rogue coordinates (max over
  positions >= 100x the median coordinate mean-magnitude, or extreme kurtosis),
  plus the overlap of its top-20 loadings with that rogue set. A direction that is
  mostly a few massive coordinates is a nuisance. Ceilings: energy fraction < 0.50,
  top-20 overlap < 10.

**Result: all 12 raw-base candidates survive all three screens.** Input
linear-predictability R^2 lands in [-0.011, +0.027], positional R^2 in
[0.006, 0.099], and rogue-energy fraction in [0.000, 0.040] (top-20 overlap at
most 2 of 20). Every candidate clears every ceiling by a wide margin, so none is
input-linear bookkeeping, a positional carrier, or rogue-loaded. Seed 20260706;
per-candidate numbers are in `census_report.json` (`candidate_screen_summary`)
and in each frozen candidate JSON's provenance.

A divergence from the literature worth recording: the SAE dark-matter family
predicts the out-of-span residual is roughly half to mostly recoverable by a
linear map from the input (R^2 about 0.7 to 0.95 at mid layers). On this surface
it is not. Family-level input R^2 of the whole span-residual is about -0.01 for
the successive family and +0.02 to +0.12 for the anchor-relative family; the
family positional variance explained is 0.03 to 0.18; and each layer carries only
2 to 5 rogue coordinates, which the candidates do not load on. The dark remainder
here is genuinely not a linear image of the input, so the row-4 identity does not
apply to this span-projected per-position generation displacement on
unanswerable prompts.

Surviving the three screens rules out the cheap nuisance identities; it does NOT
promote a candidate to a knob. The positive row-6 signature (a curved,
irreducible low-dimensional feature manifold confirmed by separability and
geodesic tests, then a causal subspace intervention) was not established here and
is the AN section-6 screen's job. Survivors keep the committed weak-prior
profile: modest pooled confab-vs-refuse AUROC (0.60 to 0.72), within-checkpoint
half-fit consistency 0.83 to 1.00, and poor cross-checkpoint transfer (0.15 to
0.52). grpo-v2 clears zero candidates through the original gate, so its screen
set is empty.

| candidate (raw-base) | pooled AUROC | input R^2 | position R^2 | rogue energy (top20 overlap) | trajectory | transfer | verdict |
|---|---|---|---|---|---|---|---|
| L16 arel pc7 | 0.64 | +0.000 | 0.057 | 0.011 (0/20) | flat | 0.272 | survives |
| L20 arel pc5 | 0.63 | +0.006 | 0.031 | 0.005 (0/20) | rise | 0.309 | survives |
| L20 arel pc8 | 0.63 | +0.027 | 0.043 | 0.014 (1/20) | rise | 0.331 | survives |
| L20 succ pc5 | 0.62 | -0.008 | 0.095 | 0.005 (0/20) | decay | 0.515 | survives |
| L24 arel pc5 | 0.63 | +0.016 | 0.023 | 0.016 (1/20) | flat | 0.270 | survives |
| L24 arel pc7 | 0.72 | +0.003 | 0.090 | 0.000 (0/20) | flat | 0.147 | survives |
| L24 succ pc4 | 0.63 | -0.008 | 0.068 | 0.011 (1/20) | flat | 0.493 | survives |
| L28 arel pc11 | 0.61 | +0.000 | 0.046 | 0.001 (0/20) | decay | 0.515 | survives |
| L28 succ pc0 | 0.60 | -0.010 | 0.028 | 0.030 (2/20) | rise | 0.250 | survives |
| L28 succ pc3 | 0.62 | -0.011 | 0.030 | 0.002 (0/20) | decay | 0.165 | survives |
| L28 succ pc4 | 0.63 | -0.006 | 0.099 | 0.040 (2/20) | flat | 0.359 | survives |
| L34 succ pc0 | 0.61 | -0.011 | 0.006 | 0.003 (0/20) | rise | 0.475 | survives |

## What could not be done with these captures

- **No correct/wrong or answered-on-answerable axis.** The AK pool is
 unanswerable-only, so confab-vs-refuse is the sole outcome. Component
 separation against correctness or answered-vs-refused-on-answerable could not
 be computed. A census with an answerable-inclusive per-position capture would
 test whether the dark structure encodes correctness rather than the
 (length-confounded) confab signal.
- **Steering artifacts (gate/dial) and caution_perp were not projected out**,
 because their frozen artifacts are at a different model/layer than these
 captures. The span therefore covers doubt + pool-fit refuse/propensity only;
 the true "named" span is at most slightly larger, which would only INCREASE
 the dark fraction, not decrease it.
- **Doubt was in the span only at L20/L24/L28** (frozen AH probe layers). L16
 and L34 spans are refuse+propensity only; the L16/L34 dark fractions are thus
 very mild upper bounds.
- **No causal test.** This is a read-side census. Whether steering along the
 frozen candidates moves confabulation is the AN section-6 screen's job, not
 this diagnostic's.

## Provenance

Every number above comes from
`census_report.json` (seed 20260706), produced by
`experiments/dark-actuator-screen/dark_displacement_census.py` reading the two staging
tarballs listed under Surface. Frozen doubt trunk: AH probes
`experiment/phase1/probe/analysis/ah_stage0/probes/probe_L{20,24,28}.joblib`.
CPU probe discipline: randomized PCA, `LogisticRegression(solver="saga",
tol=1e-3)`; no full-dim lbfgs.
