# M4c: evidence-derived doubt direction constructive search

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The margin cascade tests whether a probe direction earns the mentalistic name
"doubt" via a four-rung ladder: it must (a) track actual ignorance, (b) drive
abstention when amplified, (c) do so direction-specifically, and (d) respond to
evidence the way doubt should (supplying the true answer in-context collapses
the projection and lengthens the margin). Every prior cell auditioned a pre-fit
direction against rung (d). M4c inverts the audition: it fits a direction on
the rung-(d) contrast itself and then asks whether that constructed direction
independently satisfies the other rungs, most importantly rung (a).

M4-WK (`experiments/margin-evidence-responsiveness-worldknown/`, resolved
null-result, PR #306) is the existence proof that motivates this. On the
world-known PopQA population, at hs20, the KUQ-fit `c_hat` (transfer) did not
fire at all on the confident-wrong error class (baseline confab-vs-correct
AUROC 0.3018, void per its BLOCKER B1, population reversal). The natively refit
`c_hat_worldknown` did fire (baseline AUROC 0.86275, CI [0.8359, 0.8876]) but
its rung-(d) result was split: the projection-collapse leg-1 failed its frozen
floor (median true-answer shift 0.5921 vs `collapse_floor_z` 0.8209), while the
leg-2 specificity test passed (paired true-minus-false shift 0.10215, bootstrap
95% CI [0.0527, 0.1524], true larger). Channel 2 (margin lengthening) was
instrument-void (S1 baseline survival 0.2549 > 0.05 ceiling; only 51/400 confab
rows tip within the coherence-valid dose band; paired survival diff 0.0).

The leg-2 pass is the key fact: an evidence-specific signal exists in the
anchor hidden states, it is just small when read along the native direction.
M4-WK read that as fragmentation (the evidence leg and the ignorance leg do not
co-locate on the native axis). M4c asks the constructive question that
fragmentation cannot answer from a single pre-fit direction: is there a
direction, built to maximize the true-vs-false evidence contrast, that ALSO
separates confab from correct at baseline? If yes, the evidence and ignorance
signals live on one recoverable axis and the fragmentation reading is upgraded
to a single evidence/doubt axis. If no, the evidence signal is an in-context
answer-integration artifact with no prospective content and the fragmentation
reading stands, now on firmer ground.

Posture: exploratory instrument/mechanism tier, `qwen35_4b` only, reported
separately, never pooled with the locked Phase 1 headline matrix. M4c
adjudicates a naming-criterion mechanism; it cannot move a locked verdict.
Mistral is out of scope (it fails criterion (c); mentalistic naming already
retired there).

## Rulings record (pre-sign)

The five open questions from the design derivation are resolved as follows.

1. PI ruling (2026-07-18): rung (b), the GPU steering ladder, is CONDITIONAL.
   It is pre-registered here but funded only if rung (a) passes its 0.70 floor.
   If rung (a) fails, the cell resolves on the CPU rungs alone and rung (b) is
   recorded NOT RUN (condition unmet), which is not a void and not a gate
   failure. A rung-(a) pass does not itself authorize the launch: the standing
   rule that every paid GPU launch needs fresh explicit PI approval still
   applies at that point (the local 3090 carries standing approval).
2. PI ruling (2026-07-18): sequencing. M4c runs next, before the family memo.
3. Lead technical ruling: the rung-(b) reference dose for the freshly fit
   `d_ev` adopts the M4-WK analogy recipe, 8x `sigma_c` of the baseline-arm
   projection distribution (`mu_c`/`sigma_c` standardization). This fork was
   flagged in M4-WK as not spelled out in a governed doc; adopting the same
   convention keeps the two cells comparable. Numeric frozen at repin from
   realized `sigma_c` before any survival contrast.
4. Lead technical ruling: fit/held-out split is 50/50 (200 fit / 200 held-out)
   within the 400 test confab rows, seed 48260728, id-only permutation.
5. Lead technical ruling: the native-comparator STRONG bar is a paired
   AUROC-difference (`d_ev` minus native) lower 95% CI bound >= -0.05.
6. Lead technical ruling: the single pre-registered secondary estimator is the
   top principal component of the centered paired-difference matrix, reported
   as a robustness reading only; it never rounds into the primary verdict. A
   logistic probe is explicitly not funded.

## The construct: `d_ev`

`d_ev` is the mean paired difference, over fit-split confab rows only, between
the `true_answer` and `false_answer_placebo` anchor hidden states at hs20:

```
d_ev_raw = mean_{i in FIT confab} ( h_true(i) - h_false(i) )   # h in R^2560, hs20 anchor
d_ev     = d_ev_raw / ||d_ev_raw||                             # unit vector
```

Both arms place an answer-shaped string in context before the question (M4-WK's
before-question injection keeps the len-1 anchor on the question's last token
in all arms). The difference `h_true - h_false` cancels the components common
to "an answer is present in context" and isolates the components that separate
a TRUE answer from a category-matched FALSE placebo. Specificity against mere
answer-presence is therefore built into the estimator by construction, the same
anti-tautology logic M4-WK used for leg-2, here promoted from a readout to the
fit objective.

Because `d_ev` is optimized for the true-vs-false contrast, it must never be
scored on that contrast. Its only earned readouts are at the
`no_answer_baseline` arm (rung a), under steering (rung b), and relative to
control directions (rung c). None of these is the fit objective, and the first
is measured in an arm that contains neither the true nor the false string.

## Design

Substrate, capture convention, and detector stack are carried from the
M1/M2/M4/M4-WK lineage byte-identically. Substrate is `Qwen/Qwen3.5-4B` rev
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, bf16, `enable_thinking=False`,
under the frozen `BASELINE_SYSTEM_PROMPT` + chat template. Layer hs20
(layer_index 19), the anchor is the question's last token, one vector per row
per arm.

All hidden states for the CPU rungs already exist on disk; M4c reuses M4-WK's
channel-1 captures verbatim and generates no new forward passes for rungs (a),
(c), or the KUQ transfer readout. Verified inventory (physical location: the
retained M4-WK worktree, `/home/profsynapse/code/ehr-worktrees/m4-worldknown/`,
gitignored path `experiments/margin-evidence-responsiveness-worldknown/analysis/channel1_capture/`;
SC0 stages and hash-pins these into this cell before any fit):

- three arms `no_answer_baseline/`, `true_answer/`, `false_answer_placebo/`,
  each `capture/tensors/*.safetensors`, 1001 rows per arm (3003 files total);
- role composition per arm (from `capture/capture.jsonl`): 400 confab, 360
  correct_on_answerable, 241 refused_on_answerable, the M4-WK test population
  (`analysis-committed/selection/test_population.json`), drawn by seed
  48260727, disjoint from M4-WK's native-fit split;
- each tensor holds a single key `anchor__L20` of shape `[2560]`.

The `true_answer` and `false_answer_placebo` arms were captured only for the
test population. The M4-WK native-fit-split rows have no true/false-arm
captures. Therefore `d_ev` can only be fit from the 400 test confab rows'
true/false arms, and the fit/held-out split must be taken within those 400
rows. This is a hard constraint, not a choice (see circularity item iii).

### Fit / held-out split

- Permute the 400 confab row-keys by seed 48260728 (next free value in the
  4826072x series; 48260724-48260727 are M4-WK's). Split 50/50: 200 fit / 200
  held-out. The split is computed from opaque row-keys only, never from any
  projection, before `d_ev` is computed. Committed as
  `analysis-committed/selection/fit_heldout_split.json` (opaque ids) before any
  fit.
- Rationale for 50/50: the mean paired-difference estimator is stable at n=200
  (each coordinate is an average of 200 differences); 200 held-out confab
  against 360 correct-control gives an AUROC standard error near 0.02-0.025,
  ample power for the 0.70 floor and the native comparator.
- The 360 correct-control rows are NOT in the fit (`d_ev` is a confab-only
  paired-arm difference). They are unseen by construction, so all 360 serve as
  the negative class at rung (a). The 241 refused rows are reported as an
  auxiliary readout, not gated.
- Hard invariant: the fit never sees held-out rows; rung-(a) baseline AUROC and
  every gated quantity score on held-out confab + correct-control only.

### Direction estimator

- PRIMARY: mean paired difference (the `d_ev` formula above). Chosen for
  simplicity, pre-registrability, and because the mean difference is exactly
  the linear direction that maximizes the paired true-minus-false shift
  M4-WK's leg-2 measured, the constructive analogue of the passing test.
- SECONDARY (pre-registered, one only): top principal component of the
  centered paired-difference matrix `{h_true(i) - h_false(i)}` over fit confab
  rows. Reported as a robustness reading; if it materially outperforms the
  mean it flags anisotropy in the evidence contrast, but it never rounds into
  the primary verdict.

Sign is pinned in code by construction (the M2 trap): `d_ev` points false ->
true (more grounding = positive). The registered confab-positive score is the
negated projection `-(h_baseline . d_ev)`, mirroring M4-WK's negative-z
convention (confab expected to project low on a grounding axis). AUROC is
computed with confab as the positive class, orientation fixed at sign; if the
empirical orientation is opposite, the AUROC falls below 0.5 and rung (a)
fails, reported straight. Orientation is never chosen on the held-out data.

### The four readouts

**Rung (a), prospective ignorance tracking (PRIMARY, CPU).** Project the
`no_answer_baseline` anchors of the held-out 200 confab + 360 correct-control
onto `d_ev`; compute confab-vs-correct AUROC with bootstrap 95% CI (seed
48260724, 10000 resamples, carried). This is the key test: `d_ev` was fit
where the answer is IN context; rung (a) reads it where NO answer is in
context. An evidence-integration/answer-copying direction has nothing to
detect at baseline and separates near chance. Separation at baseline is
positive evidence that `d_ev` encodes the model's own prospective ignorance,
not answer-copying.

**Rung (b), steering to abstention (CONDITIONAL SECONDARY, GPU,
coherence-guarded; funded only on a rung-(a) pass, per PI ruling).** One dose
ladder along `d_ev`, reference dose 8x `sigma_c` per the rulings record. Run
only within the coherence-valid band: M4-WK ruled rungs >= 3.0x
instrument-invalid (total generation collapse; 3.0x confab well_formed 0.007)
and kept <= 2.0x valid (2.0x confab well_formed 0.733). Ladder fractions
`{0.5, 1.0, 1.5, 2.0}` x reference, with per-rung generation-health indicators
(well-formed rate, degeneration flag) reported for every rung; any degenerate
rung is reported, never scored. Test: abstention-rate increase vs a matched
control direction at each valid rung, paired bootstrap CI. Given M4-WK's
channel-2 instrument-void ceiling, rung (b) is expected to be weak or
instrument-limited; it is framed as a guarded secondary that can only earn if
a valid-band dose produces a coherent, CI-clearing abstention effect.

**Rung (c), specificity vs matched controls (PRIMARY companion, CPU).**
Compare `d_ev`'s held-out baseline AUROC against:

- a random-direction null: K = 1000 unit directions drawn from the empirical
  covariance of the baseline confab+correct anchors (covariance-shaped, not
  isotropic, so the null respects the activation geometry), seed 48260729.
  `d_ev` must exceed the 95th percentile of this null (p < 0.05). This kills
  the "any direction separates" tautology. Disclosed (pre-sign red-team m-1):
  the pooled covariance carries between-class structure, which makes this
  null CONSERVATIVE (random draws partially align with the class axis, so the
  bar is harder, not easier); an isotropic-null percentile is reported
  alongside as an ungated companion reading.
- the native `c_hat_worldknown` (sha256 `432c9f1f...`) as the upper comparator.
  Its 0.86275 baseline AUROC is the full-test-population reference anchor
  only; for the gated comparison the native AUROC is RECOMPUTED on the
  identical held-out rows, and the paired bootstrap of the AUROC difference
  (`d_ev` minus native) runs on those rows (pre-sign red-team m-4); the
  "matches native" STRONG bar is a lower 95% CI bound >= -0.05.
- the KUQ `c_hat` (sha256 `937d1bff...`) as the negative comparator (its
  baseline AUROC 0.3018 on this population; it does not fire).

**KUQ transfer readout (exploratory, CPU, ungated).** Does `d_ev`, fit on
PopQA world-known evidence contrast, separate confab-vs-correct on the KUQ
population? Use the doubt-snap per-row anchor states at
`experiments/qwen35-4b-midband-doubt-snap/analysis/anchor_extract.safetensors`
(hs20; roles in `fit_rows_for_anchor.jsonl`; both verified present on disk).
Report AUROC only, as the mirror of M4-WK's transfer logic run in reverse. Not
gated; a positive result is a bonus cross-population transfer, a null is
expected given the population shift.

### CPU vs GPU

- CPU only (dot products / small linear algebra on existing tensors): the
  `d_ev` fit, rung (a), rung (c) null and comparators, all baseline/arm
  projections, and the KUQ transfer readout. These reuse M4-WK's frozen
  captures, whose single-regime attestation carries (the three channel-1 arms
  captured under identical per-row batch grouping, row_order_sha256 identical
  across arms, batch_size 8).
- GPU only: rung (b)'s dose ladder (activation-addition forward passes and
  abstention grading), if funded. It needs its own pinned batch composition per
  M4-WK channel-2 conventions
  (`analysis-committed/channel2_survival/native_batch_composition.json` as the
  template) and its own GPU preflight + throughput probe (SC1).

## Circularity audit

- (i) Anti-copying control (the design's point). `d_ev` is fit where evidence
  is IN context (`true_answer` / `false_answer_placebo` arms) and tested at
  baseline where it is NOT (`no_answer_baseline` arm, containing neither
  string). A pure answer-integration/copying direction is silent at baseline
  and rung (a) lands near chance. The fit-arm / test-arm asymmetry is exactly
  what makes a rung-(a) pass informative rather than tautological. Control:
  rung (a) is scored only on the baseline arm.
- (ii) Fit / held-out leakage. The 200 fit and 200 held-out confab rows are
  disjoint by a seeded (48260728) id-only permutation; `d_ev` is a function of
  the fit rows' raw anchors only; correct-control never enters the fit. SC3
  asserts disjointness against the committed id-lists at analysis time.
- (iii) Reuse of the M4-WK 400 test rows for a NEW direction's held-out test.
  Legitimate, argued in three parts. First, the 400 confab rows were selected
  by seed 48260727 before any direction existed, via census
  correctness/abstention labeling, disjoint from M4-WK's native-fit split;
  there is no selection-on-outcome in the row set itself. Second, the one real
  residual risk is that M4-WK published per-row projections
  (`analysis-committed/channel1/per_row_projections.jsonl`, per-row
  transfer/native z in all three arms); selecting the fit/held-out split or
  tuning `d_ev` using those numbers would be selection-on-outcome. This is
  neutralized by construction: the split is an id-only seeded permutation
  computed without opening that file, and `d_ev` is the mean of RAW
  `anchor__L20` differences, never a function of any published z. The analyst
  does not inspect held-out baseline projections before freezing the split
  (self-blinding, SC0). This is machine-enforced, not promised (pre-sign
  red-team M-B): the permutation routine is pinned byte-exactly in cell.yaml,
  and the analysis re-derives both the split (from routine + seed) and `d_ev`
  itself (from staged raw tensors + the committed fit id-list) and
  hard-asserts equality with the committed artifacts; an assertion failure is
  an SC0 provenance void. Third, using a within-400 split is not a free choice
  but the only feasible one: the true/false arms exist only for these 400
  rows, so there is no alternative disjoint pool with the required captures.
- (iv) Category-matched distractor confound. M4-WK's `false_answer` donors are
  category-matched within PopQA `prop` by seeded permutation (opaque-id
  mapping, hash-pinned). A residual worry is that `h_true - h_false` encodes
  surface features of the specific donor string (length, shared tokens) rather
  than truth. This cannot drive the gated readout: rung (a) is measured in the
  `no_answer_baseline` arm, which contains neither the true nor the false
  string, so any donor-string surface artifact is absent from the scored
  quantity. The rung-(c) covariance-shaped null further absorbs generic
  surface directions. The distractor mapping is inherited byte-identically and
  reported, not re-drawn.

## Decision record

Each knob is DERIVED (from committed data), CONVENTION (carried from a
resolved cell), or JUDGMENT (a choice with rationale).

1. Population: M4-WK test captures, reused verbatim (DERIVED). The only rows
   with true/false-arm captures. 400 confab / 360 correct / 241 refused, hs20
   anchors on disk.
2. `d_ev` = mean paired true-minus-false difference over fit confab (JUDGMENT,
   primary estimator). Top-PC as the single pre-registered secondary (rulings
   record item 6).
3. Fit/held-out split = 50/50 within the 400 confab, seed 48260728, id-only
   (JUDGMENT; rulings record item 4). Correct-control never in fit; all 360
   are held-out negatives.
4. Rung (a) is the primary test (JUDGMENT). Baseline confab-vs-correct AUROC
   on held-out. Rung (c) is its companion; rung (b) a conditional guarded
   secondary; KUQ transfer ungated.
5. Rung-(a) firing floor: AUROC >= 0.70 (CONVENTION, carried from M4-WK's
   transfer firing floor). Chance is 0.5; the native comparator is 0.86275. A
   direction built purely from an in-context evidence contrast that
   nonetheless clears 0.70 at baseline on held-out rows is a real prospective
   signal. Unlike M4-WK, a below-floor result here is a substantive NULL
   (falsifier confirmed), not a void/lift; the whole point of the constructive
   search is that failing rung (a) is scientifically informative.
6. Comparator bar (STRONG pass): `d_ev` matches native (DERIVED; rulings
   record item 5). Paired bootstrap AUROC difference on identical held-out
   rows, lower 95% CI bound >= -0.05. Distinguishes "fires (>= 0.70)" from
   "fires as well as the ignorance-fit direction."
7. Rung (c) null: covariance-shaped random directions, K=1000, p<0.05
   (JUDGMENT). Plus native (upper) and KUQ (lower) comparators.
8. Rung (b): coherence-valid band only, `{0.5,1.0,1.5,2.0}` x reference,
   per-rung health (DERIVED from M4-WK's rung-validity ruling: >= 3.0x
   instrument-invalid). Conditional on rung-(a) pass (rulings record item 1).
9. Reference dose for `d_ev`: `mu_c`/`sigma_c` standardization, 8x `sigma_c`
   (CONVENTION by lead ruling, rulings record item 3). The convention is
   empirically traceable, not merely asserted: M4-WK's realized native
   multiplier-1.0 reference dose (8.469 absolute) equals 8x its realized
   `sigma_c`, so this cell carries the same realized recipe (pre-sign
   red-team m-3).
10. Seeds (CONVENTION, extending the 4826072x series): fit/held-out split
    48260728; all bootstraps reuse 48260724; random-null draw 48260729.
11. Self-blinding (CONVENTION from M2/M4-WK): the fit/held-out split, `d_ev`,
    and the rung-(b) reference dose are frozen (committed + hashed) before any
    held-out AUROC, comparator difference, or survival contrast is computed.

## Reusable-artifact manifest

1. `d_ev` direction: `analysis-committed/directions/hs20/d_ev.json`,
   `mechinterp-direction/v1`, sha-pinned, with `mu`/`sigma`/`mu_c`/`sigma_c`,
   reference dose, sign convention, and a provenance block recording the
   fit-split id-list hash. A first-class reusable direction (consumers: M3
   anisotropy, any downstream evidence-axis work).
2. Fit/held-out split id-lists: `analysis-committed/selection/fit_heldout_split.json`
   (opaque ids, seed, counts). Committed before the fit.
3. Per-row held-out projections: `{row_key, role, baseline__d_ev_z}` for the
   held-out confab + correct-control (and refused readout). No text.
4. Rung/readout aggregates: AUROCs + CIs (rung a), null percentiles + p-value
   and comparator AUROC-differences (rung c), per-rung survival +
   generation-health (rung b, if funded), KUQ transfer AUROC.
5. Input hash manifest: sha256 of the three reused capture arms (directory
   manifest hash), `c_hat_worldknown.json` (`432c9f1f...`), KUQ `c_hat.json`
   (`937d1bff...`), the KUQ `anchor_extract.safetensors` +
   `fit_rows_for_anchor.jsonl`, `test_population.json`, and the detector
   stack, mirroring M4-WK's `staging_manifest.json`.

Containment: the committed record carries only aggregates, the direction
vector, id-lists, and hashes. NEVER generation, question, or answer text. This
holds regardless of PopQA being public; any text export is the separate
`data-exhaust` license-gated path.

## Prediction

`d_ev`, fit purely on the in-context true-vs-false evidence contrast over the
200 fit confab rows, separates the 200 held-out confab rows from the 360
correct-control rows at the `no_answer_baseline` arm with AUROC >= 0.70
(rung a), exceeds the covariance-shaped random-direction null at p < 0.05
(rung c), and does so at a level statistically indistinguishable from or
better than the native ignorance-fit direction (paired AUROC-difference lower
CI >= -0.05). Interpreted: the small-but-real evidence-specific signal M4-WK
found along the native direction (leg-2 pass) is recoverable as a standalone
direction that also carries prospective ignorance information, one
evidence/doubt axis, upgrading the fragmentation reading.

## Falsifier

With the fit/held-out split valid and all provenance gates green, `d_ev`'s
held-out baseline confab-vs-correct AUROC is < 0.70. Then the constructive
search fails. Two below-floor branches are distinguished IN ADVANCE (pre-sign
red-team M-A; M4-WK's population reversal proves the second branch is live):

- (a1) The bootstrap 95% CI covers 0.5 (no baseline content). The direction
  that maximally captures the true-vs-false evidence contrast carries no
  prospective (baseline) ignorance content; it is an in-context
  answer-integration/copying direction only. M4-WK's fragmentation reading
  STANDS and is strengthened: the evidence leg (d) and the ignorance leg (a)
  live on genuinely different axes, and leg-2's evidence signal does not
  double as an ignorance detector.
- (a2) The AUROC is materially BELOW 0.5 (CI excludes 0.5 from below). `d_ev`
  DOES carry baseline content but with reversed orientation relative to the
  registered sign convention: a distinct finding, never to be equated with
  the copying/no-content reading. Reported straight and lifted to PI for
  interpretation; rung (a) still fails (the floor is on the registered
  orientation) and the fragmentation reading still stands, but the reversal
  itself is recorded as a substantive observation.

Distinct from M4-WK, a below-floor rung (a) is a substantive NULL, not a
void/lift: this cell is designed so that failing to find the axis is an
informative result about fragmentation, not an instrument failure. A void/lift
is reserved only for a broken provenance gate (a mixed-regime capture, a
failed hash pin, or a leakage-check failure). A rung-(a) pass with a rung-(c)
failure (`d_ev` no better than random) is reported as "separation is generic
geometry, not a specific evidence axis," never rounded to a win.

## Gates

Pinned in `gates.yaml` at sign; summary below.

**Integrity (S-gates).**

- SC0 provenance/staging. The three reused capture arms, `c_hat_worldknown`
  (`432c9f1f...`), KUQ `c_hat` (`937d1bff...`), the KUQ `anchor_extract` +
  `fit_rows_for_anchor`, `test_population.json`, and the detector stack are
  staged with sha256 and verified byte-identical against pins. M4-WK's
  single-regime attestation carries for the CPU rungs. The fit/held-out split
  id-list is committed BEFORE `d_ev` is computed; `d_ev` and its reference
  dose are committed + hashed BEFORE any held-out AUROC or survival contrast.
- SC1 dose & preflight (rung b only, GPU, if funded). Per-row readback within
  relative 0.005 or absolute 0.005 x reference_dose (M1's amended rule);
  mandatory GPU preflight (8-row capture + 8-row generation smoke) and
  throughput probe before the ladder; live per-rung completion assertions with
  hard abort.
- SC2 grading integrity (rung b only, if funded). Abstention calibration slice
  with the commit-before-grade / commit-before-unblind ceremony, CG1 floors,
  and the 0.05 detector-vs-adjudication disagreement gate, ensuring
  valid-band-tipped rows are represented (M4-WK channel-2 convention). Rungs
  (a), (c), and the KUQ transfer readout need no grading.
- SC3 coverage. Zero silent drops; every held-out row appears in every
  applicable readout or is reported missing with reason. Fit/held-out
  disjointness re-asserted against the committed id-lists at analysis time;
  survival never imputed for a missing generation.

**Criterion (D-gates), per rung.**

- D_a (rung a, PRIMARY). Held-out confab-vs-correct AUROC on the
  `no_answer_baseline` arm >= 0.70 (fixed floor, carried numeric; AUROC has a
  natural chance anchor). The POINT ESTIMATE gates; the bootstrap 95% CI is
  reported-only and never reinterprets the gate (pre-sign red-team m-2).
  Below floor, the (a1)/(a2) branch split in the Falsifier section applies.
  STRONG pass additionally requires the D_c native-comparator bar.
- D_b (rung b, CONDITIONAL guarded SECONDARY). Within the coherence-valid band
  only, the abstention-rate increase vs a matched control at a valid rung has
  a paired bootstrap CI excluding zero; the reference dose (numeric-at-repin,
  frozen from `d_ev`'s baseline `sigma_c` before any survival contrast) and
  per-rung generation-health indicators are reported. A degenerate rung is
  reported, never scored.
- D_c (rung c, PRIMARY companion). `d_ev` baseline AUROC exceeds the 95th
  percentile of the covariance-shaped random-direction null (formula-at-sign;
  numeric percentile frozen from the K=1000 draws at repin), i.e. p < 0.05;
  the native comparator AUROC-difference (lower CI >= -0.05 for the STRONG
  bar) and the KUQ comparator are reported alongside.

**Construct & coherence.** The rung-(b) coherence/degeneration guard inherits
M4-WK's rung-validity ruling (>= 3.0x instrument-invalid; valid band tops at
2.0x); doses reported with per-rung generation-health. The correct-control and
refused readouts are reported as construct context (no silent pass); the
covariance-shaped null (D_c) is the specificity guard for rung (a).

**Floor mechanism.** Rung (a)'s 0.70 is a fixed carried numeric
(chance-anchored). Rung (c)'s null percentile and rung (b)'s reference dose
follow the M4-WK formula-at-sign / numeric-at-repin discipline: the formula is
locked at sign, the numeric is frozen at the moment the realized quantity
(null draws; `d_ev` baseline sigma) is measured, before any contrast is
computed.

## Relation to prior cells

- M4-WK leg-2 (the existence proof). M4-WK's native leg-2 passed (paired
  true-minus-false shift 0.10215, CI [0.0527, 0.1524]): an evidence-specific
  signal is present in the anchor states, small along the native axis. M4c
  fits a direction to that contrast and asks whether it also fires at
  baseline. M4-WK leg-1 failed (0.5921 < 0.8209) and channel-2 was
  instrument-void, which is the fragmentation this cell either overturns or
  upgrades.
- M4-WK transfer void (the negative comparator). The KUQ `c_hat` did not fire
  on this population (AUROC 0.3018). M4c's rung (c) uses it as the lower
  comparator and its KUQ transfer readout runs the mirror direction.
- Fragmentation hypothesis. A rung-(a) pass overturns fragmentation (evidence
  and ignorance co-locate on `d_ev`); a rung-(a) fail upgrades fragmentation
  from "small along the native axis" to "the evidence contrast has no
  prospective content at all," a cleaner and stronger negative.

## What each outcome means

| Outcome | Reading |
|---------|---------|
| Pass a + b + c | `d_ev` is a genuine evidence-derived doubt axis: it tracks prospective ignorance (a), drives abstention in the valid band (b), specifically (c). Strongest result; constructive search succeeds, fragmentation overturned, M4-WK leg-2 upgraded to a named direction. |
| Pass a + c, fail b | `d_ev` tracks ignorance at baseline, specifically, but does not causally drive abstention within the coherence-valid band. Read/write dissociation, most likely instrument-bound (consistent with M4-WK's channel-2 ceiling), not a substantive failure. Report as dissociation. |
| Pass a only, fail c | `d_ev` separates at baseline but no better than random directions from the same covariance: the separation is generic activation geometry, not a specific evidence axis. Weak / uninterpretable; not a win. |
| Fail a, CI covers 0.5 (a1) | Falsifier confirmed. `d_ev` is an in-context answer-integration/copying direction with no baseline content. Fragmentation STANDS and is strengthened. Clean, informative negative. Rung (b) not run (condition unmet). |
| Fail a, AUROC materially < 0.5 (a2) | `d_ev` carries baseline content with REVERSED orientation. Not copying/no-content; a distinct substantive observation. Report straight, lift to PI. Rung (a) still fails on the registered orientation; rung (b) not run. |
| Fail a but KUQ-transfer positive | Anomaly (no PopQA-baseline content, but separates on KUQ). Report straight, lift to PI; do not round. |
| Any provenance/leakage gate fails | Instrument void / lift to PI (not a substantive result). Reserved only for broken SC0/SC3, mixed regime, or hash-pin failure. |

## Predictions scoreboard

| Predictor | Slot 1: does `d_ev` fire at baseline on held-out (rung a AUROC >= 0.70)? | Slot 2: does `d_ev` match the native direction (AUROC-diff lower CI >= -0.05)? |
|-----------|--------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| orchestrator | [fill at sign] | [fill at sign] |
| user (PI) | [fill at sign] | [fill at sign] |

Slot 1 is the falsifier axis (fires vs fragmentation-stands). Slot 2 is the
differentiating value (a genuine single axis vs a weak-but-real evidence axis
that underperforms the ignorance-fit direction).

## Outcome

Filled at resolve. Record the verdict, per-rung gate results (rung a + c
primary; rung b conditional guarded secondary; KUQ transfer ungated), and the
one-sentence summary that also goes into `verdict:` in the manifest.
