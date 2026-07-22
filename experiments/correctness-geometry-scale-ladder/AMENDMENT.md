# Correctness-geometry scale ladder (1.7B->8B->14B)

Status: draft (not signed; do not launch as confirmatory evidence). Real
per-row correctness labels have NOT been read by any script in this
experiment. This cell has gone through THREE successive pre-outcome
instrument iterations, all synthetic-only:

- **v1** (2026-07-20): G_val FAILED for all four estimators, all three
  scales (mean-shift generator; diagnosis 13.1/13.2). Lead adjudicated this
  as a pre-registration instrument-iteration loop, not a resolve-as-null,
  and authorized a v2 rebuild (design packet sections 13-21, lead
  adjudication section 21).
- **v2** (2026-07-20): the rebuilt generator (correlated-redundant
  flat-Rashomon) + a NEW hard-blocking pre-outcome gate,
  construction-validity, FAILED (criteria a and b; c passes) for a
  MATHEMATICAL reason -- criterion (a) (k=1 decodability-insufficiency) is
  unsatisfiable by any mean-shift-type construction (LDA argument). The
  lead and designer concurred this criterion tests the wrong axis against
  SO's real target and RETIRED it (design packet sections 22-23, teammate
  message 2026-07-20), authorizing a v3 rebuild rather than a
  mixture-construction redesign.
- **v3** (2026-07-20): retired criterion (a), replaced with (a-new) monotone
  E1 degradation across the r-ladder and (b-new) a derived index-resolution
  ceiling (sigma_c<=R_max); designated E1 PRIMARY (E2/E3_k1/E4 descriptive
  companions); fixed E1 itself (averaged over R_SH=15 split-half draws, not
  one noisy draw) and the diffuse-calibration search precision; wired
  full-n E1 primary into scale_ladder_real.py's real-mode draw loop.
  **RESULT: construction-validity v3 PASSES at all three scales** (a, c;
  b at the powered pair 8B/14B AND at 1.7B outright -- the full_pass
  branch, not merely the stated_limitation fallback) -- see Gates and
  NOTEBOOK.md 2026-07-20 v3 entry. G_val is now ACTIONABLE and E1 passes
  (primary). **G1 thresholds are now LOCKED** (2026-07-20, PI-approved
  sign-and-run instruction; lead independently re-verified the v3 numbers
  before locking) -- crystallization-index trend test on E1 full-n, bands
  frozen from the v3 official planted run, z=1.645 one-sided (see Gates).
  Sign confirmation and the first real-label run are still pending the
  lead's explicit go. Still no real per-row correctness label has been
  read.

Design source (authoritative, transcribed faithfully): the design packet
`scale_identifiability_design.md` (subspace-designer, 2026-07-20) sections
1-11, with LEAD ADJUDICATION (section 12) binding wherever it overrides the
packet. All experimental facts cited below were read from the governed docs
before use: `experiments/cross-model-size-sweep/AMENDMENT.md` Outcome,
`experiments/correctness-direction-rotation/AMENDMENT.md` Outcome,
`experiments/correctness-subspace-overlap/AMENDMENT.md` Outcome,
`library/concepts/mechanisms/l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace.md`.

## Motivation and posture

CD and SO (both Qwen3-4B, one training stage each) established a specific
fingerprint of the per-answer correctness signal: readable but weakly
identified (CD: best-layer OOF AUROC 0.809-0.860, but the within-stage
split-half normal-cosine floor is 0.174 -- stable AUROC, unstable
direction), and diffuse rather than compact (SO: only the single k=1 shared
axis is above the label-permutation null at 0.00896 vs 95th-pct 0.00472;
a random 8-dim slice of S's PCA-128 span reads T at 0.701 AUROC vs 0.742 for
S's top-8 discriminative directions, and at k=32 the discriminative
subspace falls below the random floor 0.771 vs 0.766).

The open, falsifiable hypothesis this cell targets: **diffuseness is a
small-model artifact** -- correctness may crystallize into a compact,
identifiable geometric object as scale grows. Amendment X already showed
the readout strength (AUROC) is size-robust but NON-MONOTONIC (dial/veto
peak at 8B, dip at 14B: X-G2 dial 0.8152/0.8621/0.8399 at 1.7B/8B/14B), so a
naive "monotonic sharpening with scale" story is already partly disfavored
and must be tested against X's own AUROC arc, not assumed.

Why it matters either way: if correctness geometry sharpens with scale, the
"weakly-identified/diffuse" reading is a 4B-and-below artifact and the
cold-transfer/rotation questions (CD, SO) should be re-opened at larger
scale with better instruments. If it stays diffuse from 1.7B to 14B, that is
the informative negative: answerability is near-ceiling identifiable at
every scale (X gate AUROC 0.9958-0.9982) while correctness stays diffuse
across an order of magnitude -- strengthening the answerability-vs-
correctness contrast claim for Paper 4.

Posture: exploratory Tier-2 probe-fit/geometry-analysis cell; CPU-only;
never pooled with the locked PROTOCOL v0.3 headline matrix or the S/T
headline readings.

## Design

**Data (verified 2026-07-20, CPU-only, zero GPU, no regeneration).** Ladder
= three Amendment X raw-instruct-base extractions with an identical pool
(Stage2 dual-position, post-generation content token, all layers, fp32):

| Scale | n_layers | hidden_dim | correct/wrong | best-dial layer | fixed-depth layer |
|---|---|---|---|---|---|
| 1.7B | 28 | 2048 | 377/1476 | L21 | L17 |
| 8B | 36 | 4096 | 648/1205 | L20 | L22 |
| 14B | 40 | 5120 | 741/1112 | L28 | L24 |

Verified 2026-07-20 (`scale_ladder_real.py --mode g0`; rows.jsonl only, no
tensors read): all three counts match exactly; row_key pool intersection =
3000/3000 across all three scales (identical pool); matched-n floor
N*=377/377 achievable at every scale (1.7B correct=377 is the binding
minimum). See `cell.yaml` `data.g0_verified_2026-07-20`.

**Off-ladder 4B point: EXCLUDED** (lead adjudication 1). Different pool and
extraction pipeline (S/W lineage, not Amendment X's shared pool); cited only
as a prose footnote from CD's already-committed numbers, never as a ladder
fit point.

**No-HF-revision-pin caveat (carried, not fixed):** no HF revision hash is
pinned for the three unsloth repos (repo name only, loaded 2026-06-30, per
each scale's `manifest.json`). The cell reads tensors already on disk and
never reloads a model, so this does not block it; carried identically to
Amendment X's own caveat.

**Method.** PCA-128 fit per scale, per draw, on the matched-n subsample's
post-gen activations (label-agnostic). Matched-n control: balanced
N*=377/377 correct/wrong at every scale, R=30 stratified draws, all
estimators computed per draw, across-draw median+IQR reported. Planted
baseline control: per-scale planted-signal simulation at that scale's
matched n/D/balance, calibrated to that scale's own observed full-PCA
AUROC. Layer policy: REQUIRE-BOTH (lead adjudication 2) -- best-dial layer
AND fixed fractional depth (~0.6*n_layers); a sharpening verdict must hold
under both. E1/E2 additionally scan a +/-3-layer window around best-dial as
robustness (not part of the G1 conjunction). Label-leak discipline: every
discriminative direction/subspace is fit on train folds only, every AUROC
scored out-of-fold (the SO trap).

**Estimators** (full spec, known limitations, and the v3 disposition: see
`cell.yaml` `estimators` and `planted_signal_generator`). Dispositions below
are v3 (section 22.4/22.5, teammate message item 2); v1/v2 kinds are
retained in `cell.yaml` history where load-bearing:
- **E1** split-half k=1 direction reliability -- **PRIMARY** (v3;
  designated primary in the official v3 run). CD's instrument, now averaged
  over R_SH=15 independent split-half draws (v3 fix (i)).
- **E2** top-1-vs-full concentration ratio -- **DESCRIPTIVE COMPANION** (v3;
  all-three-scales rule not relaxed; never primary-eligible).
- **E3_k1** within-stage random-slice recovery margin, k=1 -- **DESCRIPTIVE
  COMPANION** (v3, section 22.5): a support-breadth context read, explicitly
  NOT a check on E1's identifiability headline; **E3_k8** same at k=8
  (SECONDARY, descriptive only, adjudication 6).
- **E4** participation ratio of the discriminability spectrum --
  **DESCRIPTIVE COMPANION** (never primary-eligible regardless of
  pass/fail, lead ruling 21.5).
- **FORBIDDEN:** k>1 bootstrap-SVD subspace-reliability estimator, excluded
  by construction per SO's finding (best planted reliability 0.104 vs a
  0.70 gate) and the mechanism note.

**Filled gaps, v1 (superseded by the v2 rebuild below; retained for provenance):**
1. E1's split-half fit shared the draw's single per-draw PCA-128 basis
   across both halves -- SUPERSEDED in v2 by per-half PCA refit (SO's
   convention), per lead ruling 21.2's diagnosis that this was an optimism
   leak.
2. E4's held-out convention: a single stratified 50% split (paired with
   E1's split), not repeated/averaged -- CARRIES FORWARD unchanged in v2;
   only the participation-ratio formula itself changed (null-subtraction).
3. The G_val prediction-band anchor rank is DIFFUSE -- CARRIES FORWARD
   unchanged in v2 (now one of TWO anchors, compact + diffuse, section 17).
4. The v1 planted-signal generator's rank construction was AXIS-ALIGNED,
   not randomly-rotated (necessary for E4, provably immaterial for E1/E3) --
   axis-alignment CARRIES FORWARD into v2's generator for the same reason;
   the mean-shift CONSTRUCTION ITSELF was replaced (see v2 Design below).

**v3 rebuild (design packet sections 22-23, teammate message, 2026-07-20;
built after the v2 G_construction stop).** v2's own construction-validity
criterion (a) -- "k=1 must be genuinely insufficient to decode a planted
rank r>1 signal" -- FAILED at all 9 (scale, r) cells for a MATHEMATICAL
reason: any two-class Gaussian mean-shift model, correlated or not, has a
Bayes-optimal decision boundary that is a SINGLE linear direction (LDA
argument, w proportional to Sigma^-1*mu). The lead and the designer both
independently concurred this criterion tests the WRONG axis (decodability
rank) against SO's real committed target, which is itself nearly
k=1-decodable (random 8-dim slice 0.70 vs top-8 0.74) while directionally
UNSTABLE -- a synthetic construction that required k>1 decoding would
validate the estimators against a signal class the real target explicitly
is not. v3 RETIRES criterion (a) (not a mixture-construction redesign,
which the designer argued against directly as a validity error, not a fix)
and replaces it with (a-new) monotone E1 full-n degradation across the
r-ladder {compact,r2,r4,r8} and (b-new) a derived index-resolution ceiling
`sigma_c(s) = (diffuse_hw_s/1.645)/gap_s <= R_max`, `R_max =
Delta_min/(z*sqrt(2))` with `Delta_min=0.5, z=1.5` (both the design
packet's own recommended values, locked before the run). Criterion (c) is
unchanged but now specifically tests separation on the PRIMARY estimator
(E1). v3 also designates **E1 PRIMARY** (E2/E3_k1/E4 demoted to descriptive
companions, all-three-scales rule NOT relaxed for them), fixes E1 itself
(averaged over R_SH=15 independent split-half draws, replacing v2's single
noisy draw -- section 22.6.4), raises the diffuse-calibration search's own
precision (fix (ii), targeting the calibration-procedure drift v2 showed at
14B), and wires full-n E1 PRIMARY into `scale_ladder_real.py`'s real-mode
draw loop (closing the gap v2's build flagged). The crystallization-index
machinery (section 17) is revised per section 22.6: `c` is explicitly NOT
clipped to [0,1] (out-of-range values are informative), per-scale-anchor
normalization is affirmed as the cross-scale comparability mechanism, and a
pre-registered trend test (monotonicity of `c` + endpoint contrast
`Delta_c` against propagated `sigma_c`, z locked at sign) is implemented
but not evaluated (no real observed value exists pre-sign).

**v3 filled gaps (flagged for the lead, not silently resolved):**
1. `CV_B_DELTA_MIN=0.5` and `CV_B_Z=1.5` (hence `R_max~=0.2357`) are the
   design packet's own RECOMMENDED values (section 22.3), adopted here as
   "LOCKED as adopted" per the teammate message; not independently derived
   by this build.
2. The diffuse-calibration search's quick_reps (2->5) and quick_calib_iters
   (25->35) increases, and the new quick_r_sh=3 (a cheaper r_sh than the
   official R_SH=15) for E1 calls WITHIN the search only, are this build's
   own choice of how to satisfy "re-run the diffuse calibration selection
   with enough reps... to fix the procedure" -- verified empirically to
   narrow (not fully eliminate) the calibration-procedure drift: v2's worst
   case (14B, search-vs-official diff 0.101) narrowed to v3's worst case
   (14B, diff 0.036). The residual drift is reported, not further chased.
3. R_SH=15 (within the lead-authorized [10,20] range) was picked from a
   direct microbenchmark and a smoke-scale timing extrapolation (projected
   the official R_SIM=30 run at ~20-25 min at workers=8; actual wall was
   1612.9s / 26.9 min) -- a cost-driven pick, not tuned against any gate
   result.
4. Item 6 of the teammate message's pre-stated 1.7B disposition (branch:
   full_pass vs stated_limitation) turned out MOOT this run -- 1.7B passed
   (b-new) outright (full_pass branch) -- but the branching logic itself is
   implemented in `check_construction_validity`/`g_val_v2` and will fire
   correctly if a future rebuild's 1.7B numbers land differently.

**v2 rebuild (design packet sections 13-21, lead adjudication section 21;
built 2026-07-20 after the v1 G_val stop).** v1's diagnosis (section 13):
its mean-shift generator made EVERY nominal "rank" the same Bayes-optimal-
rank-1 signal (13.1), and v1's E2 (top-1-vs-full ratio using the fitted
joint normal as "top-1") was mathematically tautological for any linear
signal (13.2). v2 replaces the generator with a CORRELATED-REDUNDANT
flat-Rashomon construction (section 14): an r-axis block whose within-block
covariance is equicorrelated ((1-rho)*I_r + rho*11^T), not identity, giving
r correlated/redundant readouts of the label rather than r independent
slivers of one vector -- the mechanism SO's own Motivation (lines 50-58)
attributes CD/SO's diffuseness to (many near-tied linear combinations,
unstable argmax, stable AUROC). v2 also rebuilds E1 (per-half PCA refit,
full-n primary -- lead ruling 21.2), E2 (nested best-single-axis, not the
joint normal), and E4 (null-subtracted participation ratio via label
permutation), and adds a NEW hard-blocking pre-outcome
**construction-validity gate** (section 14 criteria a-c, lead ruling 21.4)
that must pass before any G_val criterion may be read.

**v2 filled gaps (flagged for the lead, not silently resolved):**
1. Full-n and matched-n synthetic datasets are generated by SUBSAMPLING a
   matched-n balanced set from the SAME full-n draw (one calibration
   bisection per rep, not two independent ones) -- a legitimate reading of
   "the same underlying population, different sample sizes," cheaper than a
   second full calibration, not specified either way by the packet.
2. The generator's calibration bisection ceiling (hi) is expanded
   geometrically before bisecting whenever the base ceiling cannot reach
   the target AUROC -- found necessary during build: at high (r, rho) the
   equicorrelated block's Mahalanobis distance for a fixed raw shift
   magnitude shrinks (mu^T*Sigma^-1*mu = strength^2*r/(1+(r-1)*rho) -> a
   constant as rho->1), so a fixed strength ceiling adequate for low rho
   silently undershot the target AUROC for high (r, rho) before this fix.
   This is an implementation-robustness fix (the calibration's own stated
   contract, "match target_auroc," was not being met), not a tuning pass.
3. RHO_LADDER=0.7 ("fixed moderate rho" for the r-ladder, section 14) and
   the construction-validity operational thresholds (material-rise > 0.02,
   plateau-gap < 0.01, compact-E1-floor >= 0.70) were chosen and locked
   BEFORE the official R_SIM=30 run, informed by exploratory correctness-
   testing of the estimator code (analogous to v1's axis-alignment fix) that
   also surfaced the mathematical tension documented in the Outcome section
   below; none were retuned after reading the official run's numbers.
4. The diffuse (r, rho) calibration grid (DIFFUSE_R_GRID x
   DIFFUSE_RHO_GRID, 25 points) and its quick-search reps/precision are a
   filled gap (the packet does not specify a grid); the FINAL locked-in
   (r, rho) is always re-run at full R_SIM=30/R_RAND=20/calib_iters=40
   official precision, identically to every other condition -- only the
   SEARCH itself uses a coarser, cheaper pass.

**Instrument config files:** `cell.yaml`, `gates.yaml`, `scale_ladder_lib.py`
(shared primitives; imports CD/SO helpers by reference, never reimplements;
v3 adds `e1_split_half_reliability_avg`, the R_SH-averaged E1 wrapper, on
top of the v2 generator + estimator rebuild), `scale_ladder_planted_sim.py`
(G_val v2-band-based criteria + v3 construction-validity gate + prediction
bands + trend test, synthetic only -- the module authorized to run before
sign), `scale_ladder_real.py` (G0 check + real-label ladder driver; v3
CLOSES the gap v2's build flagged -- `fit_one_draw` now fits a SEPARATE
full-rank PCA-128 on each layer's FULL real population and reports
`e1_full_n` there as PRIMARY, matching the planted sim's convention; the
matched-n reading is retained as `e1_matched_n`, a reported secondary per
ruling 21.2; regression-checked 2026-07-20 against the v3-rebuilt lib.py
(`--mode g0` PASS; `--mode real --synthetic-smoke --smoke` completes
cleanly, 30.9s, `e1_full_n`/`e1_matched_n` both populated with sane values).
The real-fit path still refuses to run without `--synthetic-smoke`, which
substitutes shape-matched synthetic data and can never read a real label).

## Prediction

**SCOPE NARROWED (v3, design packet section 22.2, teammate message item 4;
FINALIZED -- lead-confirmed 2026-07-20, PI-approved sign-and-run
instruction, teammate message item 3).** With v2's criterion (a) retired
and E1 designated PRIMARY (E2/E4 demoted to descriptive companions), the
cell's live claim narrows from "correctness geometry *crystallizes*
(compact AND identifiable)" to **"correctness-direction IDENTIFIABILITY
sharpens with scale."** This is the well-posed, instrument-backed version --
exactly the axis CD surfaced (stable AUROC 0.80, split-half 0.174) -- and
it is the axis E1/the crystallization index actually measure.
"Concentration/effective-dimensionality" language (E2/E4) is demoted to
descriptive companion, not part of the headline claim. "Diffuse" is defined
as **"correctness-direction identifiability as unidentifiable as the real
4B correctness direction (split-half ~= 0.174)"** -- exactly what the
diffuse anchor is calibrated to.

**Orchestrator bet: DIFFUSE-STABLE** (the informative negative), restated in
identifiability terms. Across the ladder, E1 (full-n primary) does not rise
beyond its per-scale planted bands from 1.7B->14B; the crystallization
index `c` stays near 0 (as unidentifiable as the real 4B direction) at
every scale, not trending toward 1. E2/E3_k1/E4 are reported as descriptive
context, not part of the bet. Honest prior: two consecutive optimistic
orchestrator calls in this research arc (CD Reading, SO Reading A) were
recorded WRONG, and X's own readout is non-monotonic (peak 8B) -- the base
rate favors "diffuse-and-stays-diffuse" or "non-monotonic," not clean
sharpening.

## Falsifier

**SCOPE NARROWED (v3; FINALIZED -- lead-confirmed 2026-07-20, teammate
message item 3).** The cell's hypothesis (diffuseness is a small-model
artifact; correctness-direction identifiability sharpens with scale) is
FALSIFIED if, across 1.7B->8B->14B, E1 (full-n, PRIMARY) does not show a
monotone increase exceeding the per-scale planted-band half-width under
both layer choices -- i.e. 14B's identifiability is within the planted
bands of 1.7B's. E1-ALONE: v2's falsifier required E1 AND E2 jointly; with
E2 now descriptive-only per the v3 scope narrowing, the falsifier is
carried by E1 alone, and the lead has confirmed this single-estimator
framing as final (the v2 E2-joint requirement is struck, not merely
demoted). **STATUS: G1 is now LOCKED** (see Gates/`gates.yaml` `G1` for the
full criterion -- frozen bands, z=1.645 one-sided, unclipped
crystallization index). Still NOT YET TESTED on real data: no real per-row
correctness label has been read; testing happens only after the lead's
explicit sign confirmation and the first real-label run.

## Gates

See `gates.yaml` for the full transcription. Summary:
- **G0** (data adequacy): **PASS**, re-verified 2026-07-20 (unaffected by
  the v2/v3 rebuilds).
- **G_construction** (construction validity, pre-outcome, HARD BLOCKING
  STOP): v2 **FAILED** (criteria a and b; c passed) for a mathematical
  reason (LDA argument) -- criterion (a) was RETIRED, not patched (design
  packet sections 22-23, teammate message). v3 (rebuilt criteria a-new/
  b-new, unchanged c): **PASSES at all three scales**, R_SIM=30 synthetic
  replicates, 2026-07-20 -- a=true, b_pass_powered=true, b_1p7b_pass=true
  (branch=full_pass), c=true. Full numbers in
  `analysis-committed/planted_sim_g_val.{json,md}` and NOTEBOOK.md v3 entry.
- **G_val** (estimator validation): **E1 (PRIMARY) PASSES** at all three
  scales (both the powered-pair 8B/14B carve-out and outright at 1.7B).
  E2/E3_k1 (descriptive companions) FAIL overall (all-three-scales rule not
  relaxed); E4 (descriptive companion, never primary-eligible) also passes
  all three scales this run. G_val is now **ACTIONABLE** (G_construction v3
  passes).
- **G1** (sharpening/identifiability, PRIMARY): thresholds **LOCKED
  2026-07-20** (PI-approved sign-and-run instruction; lead independently
  re-derived the sigma_c and separation numbers before locking). Primary
  criterion: crystallization-index trend test on E1 full-n, bands frozen
  from the v3 official planted run, z=1.645 one-sided, c unclipped -- see
  `gates.yaml` `G1` for the full spec. NOT YET EVALUATED: no real E1
  full-n value exists yet (no real label read); evaluation happens on the
  first real-label run, gated on the lead's explicit sign confirmation.
- **G2** (readout sanity): not yet applicable (no REAL-label fit has run;
  `--mode real` without `--synthetic-smoke` remains unauthorized pre-sign).
- Two-seed robustness: not yet run (moot pending lead G1 lock and sign
  authorization).

## Middle grounds

M1 (non-monotonic), M3 (layer-selection artifact): not yet testable on real
data, same reason as the falsifier. **M2 (estimator disagreement): observed
at the SYNTHETIC-VALIDATION level in both v2 and v3** -- v3: E2 passes at
1.7B/14B but not 8B; E4 passes all three; E3_k1 fails everywhere; E1
(primary) passes all three -- an estimator-disagreement pattern among the
descriptive companions, not affecting the E1 headline. **M4 (v1,
instrument-resolution-limited): superseded**, retained for provenance.
**M4-prime (total-instrument-failure, section 18): NOT APPLICABLE to the v3
run** -- `primary_designation.m4_prime = false` (E1 passes G_val), so the
cell has NOT resolved as an instrument-limited null. (v2's near-miss,
`m4_prime = true`, was moot anyway because G_construction failed one level
upstream first; retained for provenance in `gates.yaml`
`middle_grounds.M4_prime`.)

## Predictions scoreboard

Both calls recorded verbatim (teammate message item 2, 2026-07-20). Three-way split
(DIFFUSE-STABLE vs PARTIAL/NON-MONOTONE vs a clean SHARPENING that neither predictor called);
each call is scored against the realized pattern once G1 is evaluated on the real fit -- not
yet adjudicable, no real label has been read.

| Predictor | Call |
|-----------|------|
| orchestrator | "DIFFUSE-STABLE: c stays near 0 at every scale, no trend toward 1; reasoning: the Rashomon flat set arises from many features correlating with correctness, which scale plausibly increases, and the ladder's raw correctness AUROC is already non-monotone (0.815/0.862/0.840)" |
| user | "PARTIAL / NON-MONOTONE (recorded 2026-07-20 EDT): a rise that stalls or reverses, e.g. tracking the non-monotone AUROC; distinct from both diffuse-stable and clean sharpening" |

## Outcome

RESOLVED 2026-07-20: G1 lands on the pre-stated middle ground M3 -- see
"G1 resolution on the real run" at the end of this section. The build
history immediately below is retained verbatim as written pre-run; its "no
real label read" statements were true at their writing and are superseded
by the resolution block.

v1's build stopped at G_val
(pre-outcome MUST-pass stop, 2026-07-20); the lead adjudicated that as a
pre-registration instrument-iteration loop and authorized a v2 rebuild.
v2's build stopped at a NEW, one-level-upstream gate, construction-validity
(2026-07-20), whose own criterion (a) turned out to be mathematically
unsatisfiable by any mean-shift-type construction (LDA argument) -- the
lead and designer concurred it tested the wrong axis and RETIRED it (design
packet sections 22-23), authorizing a v3 rebuild. **v3's build PASSES
construction-validity at all three scales and G_val designates E1
primary** -- see full numbers below. Still no real per-row correctness
label has been read by any script in this experiment.

**v3 construction-validity result, in full (see `gates.yaml`
`G_construction` and NOTEBOOK.md 2026-07-20 v3 entry for the complete
numbers):**
- (a-new) monotone E1 full-n degradation across the r-ladder
  {compact,r2,r4,r8} at fixed rho=0.7 **PASSES at all three scales**: 1.7B
  0.590->0.451->0.301->0.185 (tol 0.056); 8B 0.686->0.557->0.394->0.258
  (tol 0.048); 14B 0.678->0.553->0.392->0.232 (tol 0.041) -- clean, no
  reversals anywhere.
- (b-new) derived index-resolution ceiling `sigma_c(s) <= R_max~=0.2357`
  (Delta_min=0.5, z=1.5, locked before the run) **PASSES at ALL THREE
  scales, including 1.7B outright** (branch=full_pass, not merely the
  weaker stated_limitation fallback the design packet's own pre-run
  analysis predicted as the likely outcome): sigma_c 1.7B=0.111, 8B=0.133,
  14B=0.108 -- all comfortably under R_max. This is attributed to v3 fix
  (i) (E1 averaged over R_SH=15 split-half draws), which tightened
  `diffuse_hw` exactly as section 22.7 predicted it most likely would.
- (c) compact-vs-diffuse separation on the primary estimator (E1)
  **PASSES at all three scales** (diff 0.41-0.51 vs half-width 0.05-0.07).
  E2 also separates at 1.7B/14B (not 8B); E3_k1 never separates anywhere
  (consistent with its support-breadth framing, section 22.5).

**G_val v2-band-based numbers (NOW ACTIONABLE):** E1 (PRIMARY) PASSES at
all three scales -- separated + monotone + reachable (the same (b-new)
band-based sigma_c<=R_max test, replacing v2's hand-picked absolute-0.70
floor) everywhere, both via the powered-pair (8B/14B) carve-out and
outright at 1.7B. E2 (descriptive companion) fails overall (passes
1.7B/14B individually, not 8B). E3_k1 (descriptive companion, a
support-breadth context read per section 22.5) fails separation everywhere
as before. E4 (descriptive companion, never primary-eligible per ruling
21.5) passes at all three scales this run (an improvement on v2's 2-of-3
partial pass). Per section 21.5's UNCHANGED fallback order (E3_k1 -> E1 ->
E2, E4 never primary), **E1 is designated primary** -- E3_k1 still fails
separation, so the pre-registered mechanism resolves to E1 mechanically,
matching the lead's ruling as a predicted result rather than a hand-picked
override (`primary_designation.m4_prime = false`).

**Diffuse-calibration drift (v3 fix (ii), partially resolved):** the
calibration-search's quick estimate vs the eventual official R_SIM=30 mean
still drifts, most at 14B (search 0.165 vs official-achieved 0.201, diff
0.036) -- narrowed substantially from v2's worst case (0.165 vs 0.266, diff
0.101) but not eliminated. Carried as a residual calibration-procedure
imprecision; not retuned further post-hoc (the ruling's own "fix the
procedure, do not hand-pick the point" was satisfied by the reps/precision
increase, not by chasing this specific number down to zero).

Lead adjudication, resolved 2026-07-20 (PI-approved sign-and-run
instruction): (a) **G1 thresholds LOCKED** from the committed planted bands
(`analysis-committed/planted_sim_g_val.json` `prediction_bands`,
`e1_full_n`), z=1.645 one-sided for the "materially sharpening" read (see
Gates / `gates.yaml` `G1`); (b) the v3 prediction/falsifier scope-narrowing
wording (identifiability-only, E1-alone falsifier) is **FINALIZED** as
drafted, no further revision; (c) the residual 14B calibration-drift
(0.036) is **ACCEPTED** as reported, not chased further. **Item (d),
closed 2026-07-20:** the PI approved sign-and-run (NOTEBOOK.md 2026-07-20),
`bin/exp sign` ran, and the real-label run executed the same day; the
original "still pending" wording is retained above only inside this
historical adjudication record.

### G1 resolution on the real run (lead adjudication, 2026-07-20)

**Run provenance.** First launch of the signed real driver was VOID: the
pinned build had the synthetic data path hardwired (an `if True` stub;
`real_layer_cache` never called). Root cause, quarantine
(`.CONTAMINATED-synthetic-20260720` runlog files), minimal repin
(`scale_ladder_real.py` -> sha 24c5da15, data routing only, gates and
thresholds untouched), and the pre-relaunch real-path probe are recorded in
NOTEBOOK.md. The resolving run: exit 0, 699.3s, 780 records,
`config.synthetic_smoke=false`; the red-team's independent contamination
check (explained_variance_128 = 0.87/0.87/0.80, decreasing with hidden
dim -- the real high-dimensional signature, impossible for the 128-dim
synthetic generator) confirms real-label execution.

**Gate arithmetic (lead-re-derived; red-teamed).** Crystallization index
c(s), unclipped, against the frozen bands:

| layer choice | c(1.7B) | c(8B) | c(14B) | monotone | Delta_c | vs 1.645*sigma_Delta |
|---|---|---|---|---|---|---|
| best_dial | -0.0620 | +0.0856 | +0.2402 | yes | 0.3022 | clears 0.2542 (frozen-only) AND 0.2880 (frozen + real draw spread) |
| fixed_depth | +0.0331 | +0.1290 | +0.0754 | no (dips at 14B) | 0.0423 | fails both |

The gate text's sigma_Delta wording ("frozen band half-widths AND the
real-side E1 draw spread") admits two readings because the pinned
`trend_test` only implements the frozen-only sigma; both readings were
computed and best_dial clears both, so the ambiguity is immaterial to this
resolution and is recorded rather than resolved.

**Adjudication.** (iii) PASS is NOT awarded: the two registered layer
choices disagree, and the middle-ground taxonomy's own M3 ("trend present
at best-dial but absent at fixed-depth") demonstrates the design treated a
best-dial-only trend as a middle ground, not a PASS. (iv) FALSIFIED is NOT
triggered: it requires no-rise under BOTH layer choices, and best_dial's
raw E1 rise (0.1566) exceeds every defensible half-width reading
(0.0739/0.0793/0.0846). (v) therefore fires: **G1 resolves as middle
ground M3.** M3 is chosen over M1 (peak-at-8B) deliberately: M1's
non-monotone shape describes only the fixed_depth arm (0.033 -> 0.129 ->
0.075, which does track Amendment X's non-monotone AUROC arc and is noted
as an M1-shaped feature of the label-free arm), while best_dial is cleanly
monotone; M3 is the only single label that captures the cross-layer-choice
disagreement that actually drove the non-PASS.

**Selection-provenance disclosure (red-team finding 2).** The best_dial
layers {1.7B: L21, 8B: L20, 14B: L28} are Amendment X's correct-vs-wrong
best layers, selected on the SAME pool and the SAME correctness labels E1
consumes -- a real selection exposure, checked and found NOT to bite: at
1.7B and 8B best_dial sits among the LOWEST-E1 layers of its own +/-3
window, so selecting for correctness AUROC did not cherry-pick for
direction reliability. The monotone best_dial trend is not
selection-inflated.

**Context that the pre-stated M3 label under-describes (red-team finding
3; descriptive, from the robustness-only window scan, NOT a gate surface,
NOT an upgrade).** The cross-scale sharpening is layer-robust: per-layer c
medians run about -0.04 (1.7B) -> +0.13 (8B) -> +0.24 (14B), and every
8B-window layer's c exceeds every 1.7B-window layer's c. The require-both
conjunction fails because fixed_depth at 14B (L24) lands on the single
anomalously low-E1 layer in its window while fixed_depth at 1.7B (L17)
lands at the high end of its window. The literal M3 gloss
("layer-selection artifact") is therefore recorded WITH this
qualification: the committed window data show a layer-robust trend whose
require-both failure is driven by one unlucky label-free layer pair. The
gate verdict stays M3; the window scan cannot and does not upgrade it.

**Reported-tier gates.** G2 (readout sanity): this run computes no new
AUROC; the criterion's own cited committed X/CD values (0.815/0.862/0.840,
all >= 0.60) stand as the reported read. two_seed_robustness: the run's
second-seed (20260721) best-dial draws reproduce the first-seed means
within 0.008 at every scale (0.1621/0.2283/0.3155 vs
0.1594/0.2205/0.3159) -- the monotone rise is seed-stable. Descriptive
companions: E2, E3_k1, E3_k8, E4 and matched-n E1 are committed in
`real_ladder.json`; none gate G1.

**Prediction scoreboard adjudication (proposed; PI adjudicates).** The
realized pattern is a partial: monotone, threshold-clearing sharpening
under the scale-adaptive layer choice; a rise that stalls and reverses at
fixed relative depth. The user's recorded PARTIAL / NON-MONOTONE call ("a
rise that stalls or reverses, e.g. tracking the non-monotone AUROC")
describes the fixed_depth arm almost verbatim and correctly rejected both
alternatives. The orchestrator's DIFFUSE-STABLE call ("c stays near 0 at
every scale, no trend toward 1") is refuted by best_dial's c=0.24 clearing
the trend threshold under both sigma readings and by the layer-robust
window trend. Proposed score: **user WIN / orchestrator LOSS**.

**Verdict (one line, mirrored in `experiment.yaml`):** G1 resolves as
pre-stated middle ground M3: correctness-direction identifiability rises
monotonically with scale at the scale-adaptive best-dial layers (c -0.06
-> +0.09 -> +0.24, Delta_c 0.302 clearing both sigma readings) but not at
fixed relative depth (c dips at 14B), so sharpening is confirmed only
conditional on layer choice; falsifier not triggered.
