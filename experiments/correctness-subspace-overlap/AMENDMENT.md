# Correctness discriminative-subspace overlap across training checkpoints

Status: null-result, resolved 2026-07-20 as instrument-limited (machine
state in `experiment.yaml`; see AMENDMENT.md "Outcome" and experiment.yaml
`verdict:`). This header was stale boilerplate reading "draft (not
signed)" until 2026-08-11; corrected to match the machine state, which was
already `null-result`. Design packet v2, lead-adjudicated 2026-07-20; PI
approved the design arc 2026-07-20 following lit-review due diligence.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

CD (`experiments/correctness-direction-rotation/AMENDMENT.md`, resolved
2026-07-20, null-result) asked whether the correctness (dial) direction rotates
across raw -> clean-SFT -> GRPO-v2 -> GRPO-par-true the way the answerability
direction does. It measured a single discriminative axis per stage (the
logistic-regression normal, unit-normed) and compared consecutive axes by
cosine. It found (AMENDMENT.md Outcome, lines 195-228; committed table lines
144-159):

- CD-G1 not met. L19-L24 mean cosines: raw->cleansft 0.192, cleansft->grpov2
  0.449, grpov2->partrue 0.330. The pre-registered "then stable" pattern
  (>= 0.85 on the later transitions) is absent.
- Falsifier did not fire (raw->cleansft 0.192 is far below the 0.80
  threshold).
- Every stage reads correctness well: best-layer OOF AUROC raw 0.860 (L24),
  cleansft 0.809 (L33), grpov2 0.811 (L21), partrue 0.817 (L24). None below
  the 0.60 sanity floor.
- Within-stage split-half control returned a floor of 0.174 (L19-L24 mean),
  computed as a single 50/50 stratified split at seed 20260719 on the grpov2
  stage.

CD's post-hoc reading (AMENDMENT.md lines 214-228, explicitly not a
pre-registered outcome): the correctness direction is only weakly IDENTIFIED.
AUROC is stable near 0.80 while the hyperplane normal is not reproducible, so
the cosine instrument cannot discriminate rotation from identifiability
noise. The mechanism behind the dial's 0.679 cold transfer stays open.

The 0.679 number (`experiments/correctness-readout-deployment-port/AMENDMENT.md`
lines 244-254): the S-fit Instruct-base correctness direction at L20, applied
cold to the deployed grpov2 checkpoint's post-gen vectors, reads AUROC 0.679,
versus grpov2's in-distribution same-layer AUROC 0.799. So the base direction
reads the deployed checkpoint well above chance but with a real 0.12 drop; the
deployment-port amendment calls the direction "partially shared, not fully."

The gap this cell targets. CD measured only rank-1 geometry (a single axis).
Two distinct mechanisms produce CD's exact signature (low cross-stage axis
cosine, stable AUROC, above-chance cold transfer):

- (a) The discriminative signal lives in a low-dimensional SUBSPACE that is
  stable across checkpoints, and the single logistic normal is an arbitrary,
  poorly reproducible vector within that flat subspace. This is precisely the
  Rashomon-set / predictive-multiplicity situation (Breiman 2001; Marx, Calmon
  and Ustun 2020): when many near-optimal separating hyperplanes fit the data
  almost equally well, the argmax hyperplane is underdetermined and its normal
  is unstable across resamples, even though the SET of good hyperplanes (their
  span) is well determined. Then axis cosine is low and unreliable while the
  subspace barely moves, and cold transfer stays high because the base axis
  still lands inside the shared subspace.
- (b) The discriminative subspace itself genuinely ROTATES across checkpoints.
  Then axis cosine is low because the geometry really moved, cold transfer is
  only partial because the base subspace only partly overlaps the target, and
  CD's "weakly identified" post-hoc reading would be wrong (the direction is
  identified, it just moves).

CD's rank-1 instrument cannot separate (a) from (b). This cell measures the
top-k discriminative SUBSPACE and its principal-angle overlap across
checkpoints, with a full-sample disjoint-split reliability reference (fixing
CD's half-sample floor), a label-permutation null that respects activation
anisotropy, and a floor-and-ceiling recovery curve that converts the geometry
into a quantitative account of the 0.679 transfer. It is the CPU-only
successor CD's own caveats point to.

Posture: exploratory Tier-2 probe-fit cell. Never pooled with the locked
Phase 1 matrix or the S/T headline readings. Single model (Qwen3-4B), one
primary seed plus a pinned robustness seed on the headline. Promotion to any
claim would need a confirmatory replication (fresh seeds, larger model, or
held-out) registered before running.

### Related work and novelty

The prior that a concept is represented as a linear subspace or cone rather
than a single direction is established: Marks and Tegmark (arXiv:2310.06824)
find a roughly two-dimensional truth subspace, and From Directions to Cones
(arXiv:2505.21800) generalizes single directions to cones. Our contribution
is not "concepts are subspaces"; it is the within-model identifiability
CONTRAST (correctness is subspace-identifiable where its single axis is not,
whereas the answerability axis in `diag-item9` was already single-axis
stable) tied to a specific measured cross-checkpoint transfer gap (0.679
versus 0.799). This is Gap 4 in the program KG; the nearest external prior
(arXiv:2511.12991) does not connect subspace geometry to a measured
cross-checkpoint readout-transfer number. The recovery-curve construction
(restricting a target checkpoint's probe to a source checkpoint's
discriminative subspace) is a restricted-rank probe, the constructive
complement of amnesic / concept-erasure probing (amnesic probing
arXiv:2006.00995; LEACE arXiv:2306.03819; RLACE arXiv:2201.12091), which
remove a subspace and measure the damage; we retain a subspace and measure
the recovery. The activation-anisotropy concern behind the null design is
Timkey and van Schijndel (arXiv:2109.04404). The overlap metric's provenance
is Krzanowski (1979). Two further anchors (both ingested in the program KG):
Subspace Chronicles (arXiv:2310.16484) is the precedent for principal-angle
subspace tracking across LM training states, and independently replicates
the stable-readout-versus-unstable-direction dissociation at pretraining
scale (cross-seed subspace angles above 80 degrees at matched checkpoints
despite near-identical probe F1); the Reliability of CKA analysis
(arXiv:2210.16156) documents the similarity-inflation regime in
high-dimension low-sample settings that motivates this cell's disjoint-split
reliability and label-permutation null.

## Design

### Core question and secondary question

Primary: does correctness classification transfer across checkpoints because
a top-k discriminative subspace is preserved rather than a single axis, and
does that subspace overlap quantitatively account for the 0.679 S->T cold
transfer?

Secondary: recast the CD four-stage timeline in subspace terms: does the
discriminative subspace rotate at SFT and then stabilize (mirroring the
answerability direction in `diag-item9-caution-assembly-timeline`), even
though the single axis within it is unidentifiable? The answerability
reference from that committed table: raw->cleansft axis cosine drops to
0.05-0.27 at mid/late layers (L18 0.0505, L22 0.0857), then cleansft->grpov2
>= 0.96 and grpov2->partrue 0.69-0.94, with AUROC flat near 0.95 throughout.

### Data (verified on disk; CPU-only, zero GPU, no regeneration)

All five stage tensor sets and their prebuilt caches already exist. This cell
reads them; it never regenerates. Verified 2026-07-20 from the canonical
checkout:

| stage | tensor dir | rows (correct/wrong) | source |
|---|---|---|---|
| raw | `/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/gen_raw` | 500 / 1323 | CD |
| cleansft | `.../gen_cleansft` | 750 / 500 | CD |
| partrue | `.../gen_partrue` | 500 / 717 | CD |
| grpov2 (T) | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2` | 988 / 500 | Amendment T reuse |
| S (Instruct base) | `archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2` | 500 / 1336 | Amendment S reuse |

Counts confirmed against the CD committed table (`cd_rotation_timeline.md`
lines 12-16) and the S/T manifests. Prebuilt caches on disk (built by CD's
`build_stage_cache`):
`/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/cache/cache_{raw,cleansft,grpov2,partrue,s}.npz`
(five files, approximately 2.8 GB total). These stack `arr[layer, row, 2560]`,
`y[row]`, `keys[row]`; reusing them makes the whole cell CPU-minutes-to-hours
(see Lane and cost).

Row schema (verified, containment-clean): each rows.jsonl row is
`{row_key, dataset, answered, refused, correct, label, prompt_len,
answer_tok_len, config_sha}`. No question text, answer text, aliases, or
token ids. `row_key` is `dataset::id`.

S/T population overlap (verified, drives the confound bound below): the S
and T labeled sets share 334 row_keys. Within that intersection the joint
(S,T) label counts are correct/correct 208, wrong/wrong 67, correct/wrong 37,
wrong/correct 22. So a matched-population S->T fit has T 230 correct / 104
wrong and S 245 correct / 89 wrong, all above the MIN_CLASS floor. The
matched-population confound bound is therefore feasible for the S->T
bracket.

Disjoint half-split feasibility (verified, drives the reliability grid): at
the tightest fit-size m=n/8 every stage keeps at least 62 rows in its
smaller class (raw 62, cleansft 63, grpov2 63, partrue 62, S 62, T 63), well
above MIN_CLASS=30 and above the maximum gated k=8. The {n/8, n/4, n/2}
reliability grid is therefore feasible for all stages.

The 0.679 transfer was measured at L20. This cell centers the transfer
accounting at L20 and reports the L19-L24 window CD used, for direct
comparability.

Optional extension (out of scope, not assumed): other model families depend
on a separate tensor inventory now in progress. If that inventory later
surfaces a second family's four-stage post-gen tensors with per-row
correctness labels, the identical subspace pipeline can be rerun per family
and the principal-angle overlaps compared across families. That is a
separate signed extension, not part of this packet, and no result here is
conditioned on it.

### Method

CPU-only throughout. The estimator is deterministic given the pinned seeds
(fixed bootstrap RNG, fixed permutation RNG, fixed PCA `random_state`, fixed
fold RNG). It reuses CD's `cd_rotation_analysis.py` primitives verbatim where
possible (`load_jsonl`, `safe_key_for`, `build_stage_cache`, `load_layer`,
`cv_auroc`, `full_direction`, `cos`) and adds the subspace machinery.

**Discriminative subspace estimator (bootstrap logistic-normal span, balanced
bootstrap).** For a stage at a layer: work in that stage's own per-layer
PCA-128 (see Basis hygiene below). Draw B = 200 balanced bootstrap resamples
(balanced bootstrap: each row appears the same total number of times across
the B resamples, which reduces Monte-Carlo variance of the estimator at no
bias cost versus ordinary bootstrap; resamples stay stratified on label and
seeded). Fit `LogisticRegression(saga, tol=1e-3)` on each resample (CD's
`full_direction` machinery, StandardScaler then unit-norm), giving a B x 128
matrix of separating normals in PCA space. The rank-k discriminative subspace
is the top-k right singular vectors of that matrix (SVD). Map each basis
vector back to the 2560-dim residual space through the PCA components and
QR-orthonormalize, giving an orthonormal 2560 x k basis U_stage,k.

Why this estimator: it answers the exact (a)-vs-(b) question directly. It
spans the directions the data actually support for the classifier (the
Rashomon set of good hyperplanes), and its top-k PCs describe the region
within which a single logistic normal is free to wander. If CD's axis was
unstable because the discriminative region is a flat k>1 subspace, this
estimator recovers that subspace.

Rejected alternatives: LDA (class-whitened between-class covariance) yields
exactly one discriminant direction for a two-class problem (between-class
scatter has rank C-1 = 1), so it cannot produce a k>1 subspace for binary
correct/wrong and is rejected as primary. Deflation (fit direction 1, project
out, refit) is deterministic and gives an ordered k-set, but each successive
direction is defined on the residual of the previous fit and its span is
sensitive to deflation order, with no natural reliability reference; it is
retained as a secondary robustness estimator (report k=8 overlap under
deflation alongside the bootstrap primary), and a large disagreement between
the two is flagged.

No .632-style correction is applied: moving reliability to disjoint
half-splits (below) removes the shared-data tightening that motivated any
such correction. The balanced bootstrap is adopted only to lower the
estimator's Monte-Carlo noise, not as an error-rate correction.

**Subspace overlap metric (Grassmann projection metric).** For two
orthonormal 2560 x k bases U, V, compute the k principal angles from the SVD
of U^T V; the singular values are cos theta_1 >= ... >= cos theta_k. Primary
scalar metric: mean squared cosine, `overlap(U,V) = (1/k) * sum_i cos^2
theta_i = (1/k) ||U^T V||_F^2`, bounded in [0,1]. This is the Grassmann
projection metric, equivalently the mean squared canonical correlation
between the two subspaces (Krzanowski 1979, between-groups comparison of
principal components). It reads as the average fraction of one subspace's
variance captured by the other. Also report the full principal-angle
spectrum (all k cosines) per compared pair, so the reader sees whether
overlap is carried by one strong shared direction or spread. k=1 reduces
exactly to a squared axis cosine, giving continuity with CD (a sanity check:
the k=1 balanced-bootstrap-mean overlap should track CD's single-fit cosines
of 0.192 / 0.449 / 0.330).

**k grid (pre-registered).** k in {1, 2, 4, 8, 16, 32}. k=1 nests CD's
single-axis measurement (continuity and sanity). The discriminative signal
reaches AUROC ~0.80 inside PCA-128, so the useful directions are a small
fraction of 128; the powers-of-two ladder from 1 to 32 spans "single axis" to
"a quarter of the retained basis." Cap at 32: as k approaches 128 the
subspace fills the retained PCA span and overlap inflates by pigeonhole. 32
keeps the label-permutation null modest while covering the plausible
discriminative dimensionality. Every overlap is reported against the
permutation null at the same k, so overlap is read against an honest chance
level, never against zero.

**Within-stage subspace reliability (disjoint half-splits plus
extrapolation to n).** CD's split-half floor (0.174) was a single 50/50
split at half sample size, understating full-sample reliability and
carrying no interval; the CD AMENDMENT itself flags (lines 236-240) that the
near-equality of raw->cleansft 0.192 with the floor 0.174 "carries no
interpretive weight" because it compares differently-powered fits. An
in-bootstrap pairwise overlap has the opposite bias (two bootstrap resamples
share about 63 percent of rows, tightening the estimate upward). This cell
uses an unbiased-by-construction disjoint estimator, per stage per layer per
k, restricted to the gate window L19-L24 (where SO-G1 reads):

- Disjoint half-split reliability. For each fit-size m in {n/8, n/4, n/2},
  draw R = 15 random stratified partitions into two disjoint sets of size m
  each (disjoint pairs only exist for m <= n/2). Fit the subspace estimator
  independently on each set (a reduced B_rel = 30 balanced-bootstrap normals
  per set, chosen so the reliability estimate is conservative: fewer normals
  scatter the SVD subspace slightly, which can only lower measured overlap,
  biasing the reliability against passing the gate). Compute principal-angle
  overlap per disjoint pair; take the median over the R pairs. This yields
  overlap as a function of fit-size m, and each point is the expected
  overlap between two independent subspace estimates, which is exactly a
  reliability.
- Extrapolation to full n (pinned). Model subspace mismatch as first-order
  in inverse sample size: `(1 - overlap)(m) = a + b*(1/m)`, fit by ordinary
  least squares over the three m points, evaluated at m=n to give the
  extrapolated full-n reliability `1 - (a + b/n)`. The 1/m form is the
  leading term of the asymptotic variance of a subspace estimator (the
  sin-theta perturbation of an estimated subspace has squared error of order
  1/m under standard M-estimator asymptotics), so a linear-in-(1/m) fit is a
  first-order Richardson extrapolation. Report the fit R^2 as a diagnostic
  and report the intercept a (the estimated irreducible, sample-size-
  independent mismatch).
- Conservative floor and fallback. Reliability increases with m, so the
  m=n/2 disjoint median is a conservative lower bound on the full-n
  reliability and is always reported. If the linear extrapolation R^2 is
  poor (pre-set threshold R^2 < 0.90), the gate uses the m=n/2 median floor
  instead of the extrapolated value (stricter, conservative), rather than
  trusting a bad fit.

A cross-stage overlap counts as reduced (relative to identifiability noise)
only if it falls below the lower of the two stages' full-n reliabilities.

**Null (label-permutation null primary; isotropic random-subspace
secondary).** An isotropic random-subspace null (draw random k-subspaces
within PCA-128) is too easy under activation anisotropy: a few high-variance
rogue dimensions (Timkey and van Schijndel, arXiv:2109.04404) are shared
across checkpoints, so two real subspaces can overlap simply because both
load on the same dominant variance directions, independent of any label
information. The primary null instead preserves the activation covariance
and breaks only the label association:

- Label-permutation null (primary). Shuffle the correctness labels within a
  stage (stratified count preserved) and refit the entire bootstrap-SVD
  subspace estimator on the shuffled labels. Do this for P = 100 permutations
  (pinned, seed 20260720), for each stage, at the gate layers L19-L24, at
  every k in the grid (k only re-truncates the same permuted SVD, so the k
  grid is nearly free). For each stage-pair of interest (raw->cleansft,
  cleansft->grpov2, grpov2->partrue, and S->T) compute the cross-stage
  overlap of the two permuted subspaces; the P values form the null
  distribution. Report its mean and 95th percentile. Any residual overlap in
  this null is exactly the anisotropy-driven, label-free chance overlap.
  Because P=100, the null 95th percentile is resolved to about the
  1-percent granularity, which is stated with the result. Gate margins read
  against this null.
- Isotropic random-subspace draw (secondary, reported). Keep the isotropic
  draw (random k-subspaces within each stage's PCA-128 span, N=200) as a
  reported sanity baseline. The expected gap between the isotropic baseline
  and the permutation null quantifies how much of the chance overlap is
  anisotropy rather than dimension-counting; report both.
- Raw-span overlap (recommended, added). In the retained-variance block
  report the principal angles and Grassmann projection metric between the
  two stages' label-agnostic PCA-128 spans directly. This makes the
  shared-activation-geometry overlap visible as a single number per
  stage-pair, complementing the permutation null.

Because the honest permutation null is expected to be higher than the
isotropic one, the predicted bands and the gate margin are set against the
permutation null and the empirical null is reported so every margin is
auditable.

**Transfer accounting (recovery curve with floor and ceiling; explanation of
0.679).** This converts subspace overlap into an account of the cold
transfer. At L20 (where 0.679 was measured) and across L19-L24:

1. S-subspace-restricted T probe (recovery curve, bracketed by floor and
   ceiling). Fit S's top-k discriminative subspace U_S,k. Project grpov2 (T)
   post-gen activations onto U_S,k, then fit a fresh 5-fold logistic probe on
   T within that restricted k-dim subspace and report OOF AUROC, call it
   AUROC(T | S-subspace, k). At every k also report:
   - Chance floor: AUROC(T | random k-subspace of S's PCA span), averaged
     over the isotropic random-subspace draws above. This is what T recovers
     when restricted to an arbitrary k-subspace of S, isolating the value
     added by S's discriminative subspace over a generic one.
   - Ceiling: AUROC(T | T's own top-k subspace), the best T can do
     restricted to k of its own directions.
   Interpretation: the single-axis cold transfer 0.679 is the k=1,
   frozen-coefficient special case (S's exact axis, no refit), and the k=1
   recovery point should land near 0.679 as a pipeline sanity check against
   the deployment-port measurement. Under mechanism (a) the recovery curve
   rises to near the ceiling at small k while the floor stays low; under
   mechanism (b) the recovery curve tracks the floor (S's discriminative
   subspace adds nothing over a random subspace of S) and never approaches
   the ceiling.
2. Direct S->T subspace overlap. Principal-angle overlap between U_S,k and
   U_T,k (each in its own symmetric basis, see Basis hygiene), reported with
   the permutation null and both stages' full-n reliability. High overlap
   should coincide with a recovery curve reaching near the ceiling; overlap
   near the permutation null with a recovery curve pinned to the floor.

The predicted-versus-observed accounting is stated as: observed single-axis
cold transfer 0.679 (frozen, k=1) versus T in-distribution 0.799 (full
PCA-128), with the floor-to-ceiling recovery curve telling us how much of
that gap S's shared geometry supports and at what k.

**Basis hygiene.** CD fit PCA-128 on the raw stage only and reused it for
every stage, and fit the S->T bracket in S's own basis with T projected into
it; the CD AMENDMENT flags both threats (raw-basis truncation unquantified,
lines 241-245; bracket "fit in S's own PCA basis and not magnitude-
comparable," lines 224-228). This cell treats stages symmetrically:

- Primary basis treatment: fit PCA-128 separately on each stage's own
  post-gen activations, estimate that stage's discriminative subspace inside
  its own PCA-128, map the subspace to the ambient 2560-dim residual space,
  and compute principal angles in 2560-dim. Principal angles in the common
  ambient space are basis-independent, so no stage is privileged and there
  is no asymmetric projection of one stage into another's basis. This
  applies identically to the four-stage timeline and the S->T bracket
  (fixing the CD bracket asymmetry directly).
- Retained-variance reporting (quantifies the truncation CD left
  unrecorded): for each stage and layer, report the fraction of total
  activation variance retained by its PCA-128, and (spot layer) the
  discriminative signal retained (full-PCA AUROC versus full-dim AUROC). Add
  the cross-stage raw-span overlap described above.
- Secondary robustness: a shared symmetric basis (PCA-128 on the
  per-stage-balanced pooled union of stages, equal n per stage) with the
  timeline overlaps recomputed; agreement with the per-stage-symmetric
  primary is reported, a large disagreement flagged.

**Population/label confound bound.** CD accepted the per-stage
population/label shift as an unbounded interpretive limit (AMENDMENT.md
lines 63-66, 231-234). This cell bounds it where the data allow:

- Matched-population S->T bracket (primary bound, feasible: 334 shared
  row_keys, T 230/104, S 245/89 per class, all above MIN_CLASS). Recompute
  the S->T subspace overlap and the recovery curve restricted to the shared
  row_keys. If overlap and the recovery curve are stable versus the
  full-population version, the population shift is not driving the S->T
  geometry; report the delta as the confound sensitivity. The reduced sample
  (334 rows) is read against the disjoint-split reliability curve so the
  power drop is not misread as rotation.
- Matched-class-balance (secondary, four-stage timeline). Subsample each
  stage to a common correct/wrong count and recompute the consecutive-stage
  overlaps, removing the class-balance contribution to any
  covariance/basis difference; report the delta versus the full-population
  overlaps.
- Honest residual. The full four-stage timeline's population confound is
  only partially bounded because the four-way shared intersection is too
  small for a matched-population four-stage fit; this is carried as a
  caveat, but it is strictly better than CD's fully-unbounded acceptance
  because the decision-relevant S->T pair is bounded.

## Prediction

Orchestrator call (recorded pre-run): the discriminative subspace overlaps
across checkpoints far more than CD's single axis did, the subspace is
reliably identified (unlike the axis), and S's subspace substantially
recovers T's in-distribution AUROC. Bands are stated against the
label-permutation null, which is expected to be higher than an isotropic
null. Concretely, at k=8 over L19-L24, all three readings are pre-stated so
no result falls off the table:

- Reading A, SUBSPACE-OVERLAP (the informative positive): S->T subspace
  overlap exceeds the permutation-null 95th percentile AND overlap minus
  permutation-null mean >= 0.15; within-stage full-n reliability at k=8
  >= 0.70 for both S and T (the subspace IS identified, in contrast to CD's
  single-axis split-half 0.174); and the recovery curve closes at least
  three-quarters of the floor-to-ceiling gap at k=8. Reading: the
  correctness readout transfers across checkpoints on a shared
  low-dimensional subspace, the single axis is arbitrary within it
  (explaining CD's low, unreliable cosines as Rashomon-set
  underdetermination), and this quantitatively accounts for the 0.679 cold
  transfer as a frozen-axis lower bound on a larger shared-subspace
  capacity.
- Reading B, GENUINE ROTATION (the informative negative): S->T subspace
  overlap is indistinguishable from the permutation null (inside its 95th
  percentile and within 0.10 of its mean) at every pre-registered k up to
  32, WHILE within-stage full-n reliability is high (>= 0.70), AND the
  recovery curve tracks the floor (never closes more than one-quarter of
  the floor-to-ceiling gap) at any k. Reading: the discriminative subspace
  genuinely rotates across checkpoints; the 0.679 partial transfer reflects
  real geometric drift, not axis-identifiability noise; CD's "weakly
  identified" post-hoc reading is superseded (the geometry is identified,
  it moves).
- Middle ground (pre-stated, neither reading adopted): subspace overlap
  above the permutation null but within-stage full-n reliability itself low
  (< 0.70) at the same k. Then the subspace instrument is also
  resolution-limited at these sample sizes, echoing CD but now with the
  disjoint-split reliability curve quantifying the limit; report "subspace
  overlap not resolvable at this sample size," neither A nor B adopted.

Orchestrator's own bet: Reading A. Prediction: k=8 S->T overlap in the
0.45-0.70 band against a permutation null with mean ~0.20-0.35 and 95th
percentile ~0.30-0.45 (higher than an isotropic null would give), so a
comfortably positive margin; within-stage full-n reliability 0.75-0.90;
recovery curve reaching 0.78-0.80 (near the T ceiling) by k=8 while the
random-subspace-of-S floor stays near 0.60-0.68. Rationale: CD found stable
AUROC (~0.80) with an unreliable axis (split-half 0.174) and an
above-chance cold transfer (0.679) coexisting with a low single-axis cosine
(bracket 0.170); that specific combination is the fingerprint of a flat
discriminative (Rashomon) subspace, mechanism (a).

## Falsifier

The cell's headline hypothesis (correctness transfer rides on a shared
discriminative SUBSPACE that accounts for the 0.679 cold transfer) is
FALSIFIED if, at every pre-registered k up to 32 over L19-L24, S->T subspace
overlap is statistically indistinguishable from the label-permutation null
(inside its 95th percentile and within 0.10 of its mean) WHILE within-stage
full-n reliability is high (>= 0.70), AND the recovery curve never closes
more than one-quarter of the floor-to-ceiling gap at any k. That is Reading
B: no shared subspace beyond the anisotropic chance level, transfer does
not ride on subspace overlap, genuine rotation adopted. Reported straight.
(If overlap is at the null but reliability is also low, that is the
middle-ground instrument-limited null, not the falsifier.)

## Gates

Per-cell gates in `gates.yaml`: SO-G0 (data adequacy, pre-outcome stop,
reuse-verification, no generation), SO-G1 (primary, subspace-overlap-
confirmed, a conjunction of overlap-versus-null margin, within-stage
reliability, and recovery fraction at k=8 over L19-L24), and SO-G2 (readout
sanity, reported). A two-seed robustness rerun of the headline k=8 S->T
overlap (seed 20260721) is also required before the SO-G1(i) call stands;
a seed disagreement is reported as a stability caveat, not resolved by
picking a seed.

## What is NOT claimed

Exploratory Tier-2, single model, one primary seed plus one robustness seed
on the headline. Never pooled with the locked Phase 1 headline matrix or
the S/T headline readings. No causal claim about training; subspace
overlap is a geometric description of already-collected activations, not
an intervention. The population/label confound is bounded for the S->T
pair only; the four-stage timeline's confound is partially bounded
(matched-class-balance) and the caveat is carried. A positive Reading A
would be a candidate mechanism for the 0.679 transfer, not a confirmed one;
promotion needs a registered confirmatory replication (fresh seeds, larger
model, or held-out).

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Reading A. k=8 S->T overlap 0.45-0.70 against a permutation null mean ~0.20-0.35 (95th pct ~0.30-0.45); within-stage full-n reliability 0.75-0.90; recovery closing ~0.80+ of the floor-to-ceiling gap by k=8 (curve reaching ~0.78-0.80 near the ceiling, floor ~0.60-0.68); the 0.679 transfer is a frozen-axis lower bound on a shared-subspace capacity near 0.80. (recorded pre-run) |
| user | Approved the design arc 2026-07-20 following lit-review due diligence; no separate quantitative call recorded. |

## Lane and cost

Lane: CPU-only, zero GPU, no launch approval needed. No generation, no
extraction; all five caches are on disk. The cost is dominated by the
label-permutation null (P full-pipeline refits). Counting logistic fits
(each PCA-128 saga fit on approximately 1500 rows, empirically about
0.1-0.15 s warm):

| component | fit count | derivation |
|---|---|---|
| core subspaces | 37,000 | 5 stages x 37 layers x B=200 |
| disjoint-split reliability | 81,000 | 5 stages x 6 gate layers x R=15 x 3 m x 2 halves x B_rel=30 |
| label-permutation null | 120,000 | P=100 x 5 stages x 6 gate layers x B_null=40 |
| 2-seed headline rerun | ~4,800 | 2 stages (S,T) x 6 layers x B=200 x 1 extra seed |
| recovery/floor/ceiling + deflation | ~2,000 | k-grid x layers x folds, negligible |
| total | ~245,000 | |

At 0.1 s/fit that is about 6.8 CPU-hours; at 0.15 s/fit about 10.2
CPU-hours, under the ~12 CPU-hour budget. P=100 is chosen to hold the null
term (the dominant one) inside budget while still resolving the null 95th
percentile to about 1-percent granularity; B_null=40 and the L19-L24
gate-layer scoping of both the null and the reliability keep those terms
bounded (the full 37-layer timeline uses only the core subspaces, which are
cheap). The job is embarrassingly parallel across layers and permutations,
so wall-clock on the multi-core box stays well under an hour. Peak memory
is one stage cache at a time (approximately 0.7 GB). Any change of lane
(for the deferred cross-family extension, if it ever needs regeneration)
would need fresh approval.

## Outcome

Resolved 2026-07-20 as a null-result (instrument-limited), adjudicated by
the lead against the signed gates after an adversarial red-team review
(six findings, sign-off conditional on wording; every wording constraint
is applied below). All gate numbers were independently re-derived by the
lead from `analysis-committed/subspace_overlap_timeline.json` and match
the module's own gate summary exactly. Run provenance: detached CPU run,
76.4 min wall at 8 workers, module sha unchanged
(de6c16fb3c266b2d6393ba6700f83b8531108865cf96f82f10079618e330fd71).

Gate results as signed:

- SO-G0 PASS. All five caches matched the CD committed table exactly
  (raw 1823 = 500/1323, cleansft 1250 = 750/500, grpov2 1488 = 988/500,
  partrue 1217 = 500/717, S 1836 = 500/1336); matched-population subset
  counts verified (T 230/104, S 245/89); the m=n/8 half-split grid held
  at least 62 rows per class everywhere.
- SO-G1 FAIL on all three limbs (L19-L24 means at k=8):
  (i) S->T overlap 0.01157 vs permutation-null mean 0.01085 and 95th
  percentile 0.01419: margin +0.00072 vs the required +0.15, and inside
  the null band. (ii) Within-stage full-n reliability S 0.0185 and
  T 0.0293 vs the required 0.70; the 1/m extrapolation R^2 was
  0.007-0.226 at every gate layer, so the pre-registered m=n/2
  conservative fallback was used at all 12 stage-layer cells.
  (iii) Recovery closed fraction 0.1750 vs the required 0.75.
- SO-G2: per-stage best-layer full-PCA OOF AUROC inherited PASS
  (0.809-0.860). The k=1 recovery point at L20 is 0.7009, within 0.10 of
  the documented 0.679 cold transfer; a fresh-refit 1-D probe can only
  meet or exceed the frozen-coefficient 0.679, so this is a sanity check,
  not an exact reproduction. Criterion (iii) is met only literally: the
  k=32 restricted AUROC exceeds full-PCA via the ceiling's label leakage
  (see caveats), so it is NOT evidence that the subspace estimator
  captures the discriminative signal.
- Falsifier (Reading B) NOT fired: its precondition of within-stage
  reliability >= 0.70 is unmet, and the k=1 and k=2 overlaps are above
  their nulls, so the "indistinguishable at every k" clause also fails.
  Per the signed falsifier text, overlap at the null with low reliability
  is the middle-ground instrument-limited null.
- Two-seed robustness: both pinned seeds agree so_g1_i_pass = False at
  every gate layer; the headline call is seed-stable.

Adopted reading: the pre-stated middle ground. Neither Reading A (shared
flat subspace) nor Reading B (genuine rotation) is adopted. The cell
could not adjudicate mechanism (a) vs (b): its primary discrimination
instrument saturated below the gate threshold.

Red-team finding on the nature of the limit (post-hoc diagnosis, labeled
as such; no gate, threshold, or reading retuned): a planted-signal
simulation using the module's own estimator at matched n, dimensionality,
and class balance showed that k=8 within-stage reliability >= 0.70 is
unreachable for ANY signal, including a perfectly separable redundant
flat 8-dim subspace, the exact mechanism-(a) case the gate was built to
detect (best planted case reliability 0.104; the observed real-data
values 0.0185-0.0293 are indistinguishable from a genuine moderate 8-dim
signal at 0.018-0.073). The cause is estimator-structural, not
sample-size: L2-regularized logistic regression collapses a redundant
discriminative subspace onto one stable weighted normal, so
bootstrap-normal SVD directions beyond the first are noise regardless of
the true dimensionality. The pre-stated middle-ground phrase "not
resolvable at this sample size" is therefore superseded on mechanism:
more data would not lift this limb. Because both Reading A and the
falsifier required that limb, both were unreachable before any data were
seen, and the falsifier's non-firing carries no evidential weight.

What the run does establish (label-clean numbers):

- The k=1 S->T overlap is above its permutation null (0.00896 vs 95th
  percentile 0.00472, 6.7x the null mean), k=2 marginally so, and k=4
  through k=32 are inside the null. One weak shared direction, the axis
  underlying the documented 0.679 transfer, is real; no reproducible
  shared structure beyond it was detectable by this instrument.
- S's discriminative 8-subspace reads T only about 0.04 AUROC above a
  RANDOM 8-dim slice of S's PCA-128 span (recovery 0.742 vs floor 0.701
  at L20; at k=32 recovery 0.766 is below the floor 0.771). The
  transferable signal is diffuse in S's span rather than concentrated in
  S's top discriminative directions.

Caveats (carried):

- The recovery ceiling is label-leaky: T's top-k basis is fit on the full
  T labels before CV scoring, inflating it above this run's own full-PCA
  OOF AUROC (0.885 at k=1 decreasing to 0.864 at k=32, vs full-PCA
  0.814). The bias depresses closed_fraction, so limb (iii)'s FAIL is
  conservative (an honest ceiling near 0.78 still yields about 0.52,
  below 0.75), but all closed_fraction values are ceiling-dependent.
- The two pre-registered subspace estimators (bootstrap-SVD primary vs
  deflation) agree only 0.17-0.23 at k=8 across stages: independent
  corroboration that the k=8 subspace is not well determined.
- The pooled shared-basis secondary runs +0.06 to +0.27 above the
  per-stage-symmetric primary on the four-stage timeline (the predicted
  shared-basis inflation); it is not computed for the S->T bracket, so
  the headline is unaffected.
- Population/label confound: the matched-population S->T bracket (334
  shared row keys) gives k=8 overlap 0.0087 vs 0.0128 full-population;
  the near-null result is not a population artifact.
- External dependency: re-running requires the five cache_*.npz
  activation caches (durable exhaust store) and CD's
  cd_rotation_analysis.py helpers.
- Exhaust wording gap: cell.yaml's exhaust_staging sentence names derived
  arrays (bootstrap bases, permutation draws) for the durable store; as
  designed in the signed packet those are consumed in memory and only
  summary statistics persist. Provenance artifacts (run log, start stamp,
  pid file) were staged; no per-draw arrays exist to stage.

Predictions scoreboard adjudication: the orchestrator's Reading A call
was WRONG on every quantitative band (overlap level, null level,
reliability, recovery fraction). Recorded straight.

One-sentence verdict (mirrors `experiment.yaml`): S->T correctness-
subspace overlap at k>=4 sits inside its permutation null and the
reliability limb was shown estimator-structurally unreachable for any
signal, so the flat-subspace vs rotation question stays open; only the
single k=1 shared direction underlying the 0.679 transfer is above null,
and S's discriminative subspace reads T only about 0.04 AUROC above a
random slice of S's span.
