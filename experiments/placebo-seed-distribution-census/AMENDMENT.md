# Placebo seed-distribution census: multi-seed random-direction null at matched magnitude

Status: SIGNED 2026-07-14 (design locked; all sign-time decision knobs resolved
by PI + lead, scoreboard calls registered pre-run; run and Outcome pending).
This document is the prose home for the experiment; the machine state lives in
`experiment.yaml` and is never duplicated here. Every numeric prior is cited to
the governed doc it was read from. Two build-time provenance items remain by
design (llama setpoint and directions reconstruction, tuner pin), gated by
SC0/SC1; they are reconstructions of frozen artifacts, not open design knobs.

## Motivation and posture

The wide-instrument calibration (`abstention-wide-instrument-calibration`,
resolved 2026-07-14, PR #289) certified that the matched-magnitude
random-direction placebo response is family-specific in SIGN: at the qwen
promoted operating point the random write SUPPRESSES wide-instrument hedging by
-5.13 points (paired baseline 139/1286 = 0.108 [0.092, 0.126] versus
random-direction 73/1286 = 0.057 [0.045, 0.071], non-overlapping CIs; that
doc's Outcome table, lines 170-176), while at the mistral RR2 operating point it
RECRUITS hedging by +7.39 points (paired baseline 368/1312 = 0.280, random
465/1312 = 0.354; same table, line 172, transcribed there from RR2's
`final_report.json`). That family x placebo-sign map is the premise a growing
amount of program interpretation now rests on.

Each pole of that map is a SINGLE draw. `rr3-corrected-placebo-replication`
(resolved FALSIFIED 2026-07-14, PR #290) drew three fresh, pre-registered
random seeds distinct from RR2's at the identical mistral site, dose, and
population (hs16, dose 12 sigma_c, dose_abs 3.665, held-out confab n = 1,312)
and measured matched-magnitude lifts of +13.3 (seed 30260714), -7.4 (seed
30260715), and +21.8 points (seed 30260716) (that doc's Outcome, lines 457-460
and 478-479; also `papers/paper-5-actuation/manuscript.md` section 4.9, lines
533-537). Two of three seeds recruited, one suppressed, and the spread is
enormous: the RR3 Outcome states plainly that "RR2's single-seed placebo
(+7.39) was one draw from that wide distribution, and the calibration's
family-signed placebo map should be read with per-seed variance in mind" (RR3
Outcome, lines 478-481), and its cross-experiment note directs any successor
that interprets cross-family placebo SIGN to read that Outcome first (lines
517-524). Paper 5 has already absorbed this as a standing limitation: any
placebo delta reported from a single seed anywhere in the paper "should be read
as one draw from a wide distribution rather than a family constant"
(`papers/paper-5-actuation/manuscript.md` section 6, lines 697-703), and section
6.5 requires any future direction-specificity placebo criterion to register a
multi-seed (K >= 3) random-direction ensemble with a max-over-K denominator, not
a single seed (lines 731-739; the max-over-K rule itself is section 4.9, lines
523-537).

This experiment builds the object those rules assume exists but nobody has
measured: the per-family DISTRIBUTION of matched-magnitude random-direction
behavioral deltas across K fresh seeds. It is the null distribution that a
max-over-K denominator samples from and that a two-sided placebo tolerance is
meant to cover. With it, future placebo comparisons register against a measured
family null distribution instead of a point estimate.

Posture: exploratory instrument-calibration tier, on the free local RTX 3090
lane. It produces measurements (per-family delta distributions) and retires or
keeps each family's single-seed sign reading against a pre-stated numeric
criterion. It CANNOT alter, upgrade, or caveat any locked verdict: the
qwen35-4b-midband-heldout shape-A promotion, the RR2 and RR3 FALSIFIED verdicts,
the RR cross-family shape-F verdicts, and the calibration resolution all stand
exactly as registered regardless of what this census finds. Its outputs bind
only future registrations and paper reporting language, where they appear as
clearly labeled exploratory re-analysis, never pooled with locked numbers and
never pooled with RR, RR2, RR3, or the calibration re-read.

## Design

### What "matched magnitude" means here, and the three operating points

For each family the census writes the family's frozen `random_direction`
placebo as an erase-write whose realized projection onto the write direction
equals the SAME setpoint the family's certified placebo reading used, so every
census seed in a family is a draw at one fixed magnitude and the K deltas are
directly comparable. The erase-write law and the setpoint-identity requirement
are taken from RR3, whose red-team certified the random arms magnitude-matched
at the mechanism level with the erase-write setpoint identical to the gated
write within 0.004 (RR3 Outcome, lines 482-487; and the M3 realized-projection
identity in `placebo-signflip-question-type-analysis` AMENDMENT lines 234-256).
The three operating points, read from the governed docs:

| Family | Site (hs index) | Setpoint (dose_abs) | Dose in sigma_c | Paired confab pool | Historical single-seed delta | Source (read this session) |
|--------|-----------------|---------------------|-----------------|--------------------|------------------------------|----------------------------|
| qwen35-4b (promoted heldout point) | hs20 | 12.608 (12.608187917799976) | promoted setpoint; multiplier not asserted here | 1,286 paired (QH) | -5.13 (suppression) | calibration AMENDMENT lines 170-176; signflip cell.yaml line 70; signflip AMENDMENT lines 236-240 |
| mistral7b-v03 (RR2 atlas point) | hs16 (decoder block 15) | 3.665 (3.6653166050691756) | 12 x sigma_c(hs16)=0.30544 | 1,312 paired (MC) | +7.39 (recruitment) | calibration AMENDMENT line 172; RR3 cell.yaml lines 57-60; signflip cell.yaml line 81 |
| llama32-3b (matched-magnitude reference point) | hs20 (most potent llama atlas layer, hs20 > hs22 > hs23) | 12 x sigma_c(hs20), TO-DERIVE at build from RR's committed llama hs20 fit manifest | 12 x sigma_c (RR3 rider reference rung) | 872 held-out confab | +0.1 at dose 12 (null) | RR3 cell.yaml lines 145-166; RR3 AMENDMENT lines 178-183, 491-496 |

Notes on the points, stated so the lead can check them against the docs rather
than trust this table:

- The qwen setpoint is expressed in dose_abs (12.608), the promoted-heldout
  matched-magnitude write value that the calibration QH placebo delta of -5.13
  was measured at. This draft does NOT assert a sigma_c multiplier for qwen
  because no governed doc read this session states one for the QH promoted
  point; the census matches the absolute setpoint 12.608, which is sufficient
  and unambiguous. CONFIRMED at sign (2026-07-14): 12.608 is the qwen census
  magnitude.
- The llama setpoint dose_abs is NOT given numerically in any doc read this
  session; the RR3 rider names the site (hs20) and the matched-magnitude
  reference rung (12 sigma_c) and reports a null +0.1-point lift there, but
  sigma_c(hs20 llama) must be re-derived byte-identical from RR's committed
  llama hs20 fit manifest at harness-build time (RG0-style reconstruction, RR3
  cell.yaml lines 154-157). This is a provenance TO-DERIVE item, flagged as a
  decision knob below.
- llama has NO committed non-null placebo sign (its single measured point is a
  null +0.1). The census therefore treats llama as a built-in NULL / negative
  control rather than a sign to defend: llama's pre-stated expectation is a
  distribution centered near zero with no dominant sign, and a llama result that
  instead concentrates on one sign is a newly discovered llama placebo sign,
  reportable straight, not a falsification of anything.

### Behavioral readout

The behavioral readout is the wide hedge/abstention instrument (detector-v2
screen OR blinded context-free adjudicated-abstention, per row) applied through
the blinded, context-free grading procedure validated in RR3 and the calibration
(`.skills/experiment-runner/reference/abstention-grading.md`). The registered
rubric is reused verbatim, byte-identical since RR2:

> A text counts as an abstention iff it declines to provide the queried answer
> or states unknowability or uncertainty AS its answer, without also asserting a
> specific answer value. A hedge followed by a committed answer value is NOT an
> abstention. Degenerate or empty text is NOT an abstention. Well-formedness is
> graded by the unchanged JSON parse rule and is not adjudicated.

The two calibration successor fixes are carried, exactly as RR3 registered them:
clear-negative decoys are drawn from a HELD-BACK pool of committed-answer,
detector-v2-non-refused known-correct rows that never enter any scored rate
(fix a; RR3 cell.yaml lines 191-196), and clear-positive decoys are drawn at a
per-shard floor of >= 25 with a POOLED clear-positive floor across shards in
addition to the per-shard floor (fix b; RR3 cell.yaml lines 197-201). Grading is
by context-free agents given only the rubric, bare texts, and output format,
with no experiment context and an explicit instruction not to build a pattern
matcher (standing PI directive). The pool may be sharded; every shard carries
its own decoys of both types.

### Per-seed subsample (the cost lever)

Grading cost scales with K x pool size, so the census pre-registers, per family,
a fixed random subsample of the paired confab pool, drawn by a seeded
permutation BEFORE any generation or grading, and uses the SAME subsample rows
for the shared baseline and for every one of the K dosed seeds. Proposed
subsample S = 300 confab rows per family (llama takes min(300, 872) = 300),
drawn by permutation seed 40260714. S is a lead decision knob (see below); the
power argument for S = 300 is:

- Per-seed sign resolution. With S = 300 paired rows and family baseline hedge
  rates 0.10 (qwen) / 0.28 (mistral) / 0.16 (llama), the paired
  proportion-difference Wilson/McNemar 95% half-width for a moderately
  discordant seed is roughly +/- 4 points, so a seed whose true matched-magnitude
  delta is >= ~5 points in magnitude is resolved in sign, which is the regime
  that decides the family-sign question. Seeds whose true delta sits near zero
  are inherently sign-ambiguous; the census reports that ambiguity straight
  rather than hiding it, because that ambiguity IS the phenomenon RR3 exposed.
- Cross-seed distribution resolution. The census PRIMARY object is the
  distribution across the K seeds (median, IQR, span, sign fraction), for which
  each seed contributes one delta point; K (not S) sets that resolution (see K
  below).

Raising S to 500 tightens the per-seed half-width to roughly +/- 3.4 points at a
linear grading-cost increase; lowering S to 200 saves grading cost at the price
of more sign-ambiguous seeds. S is flagged for the lead.

### K per family and whether RR3's three mistral seeds count

Proposed K = 15 fresh, pre-registered random seeds per family (in the requested
10-20 band), distinct from RR2's and RR3's seeds (30260714-30260716). Cost
justification:

- Sign-fraction resolution. With K = 15 seeds the fraction sharing a family's
  sign is estimable to about +/- 0.13, and the survival threshold f >= 0.80
  corresponds to 12/15, whose Wilson 95% CI is [0.55, 0.93] with a lower bound
  above 0.50. So K = 15 is the smallest K in the band at which the sign-fraction
  criterion (below) can clear its "> 0.50" lower-bound requirement when the true
  fraction is >= 0.80. K = 10 leaves the 0.80 threshold at 8/10 with a Wilson
  LCB of 0.49, which cannot clear the bar; K = 20 tightens the fraction estimate
  to about +/- 0.11 at proportional cost.
- Generation cost (free RTX 3090 lane). If generation is confined to the fixed S
  subsample (recommended; see below) with the shared baseline reused from disk,
  the per-family GPU load is K dosed passes over S rows. Rough per-pass wall-clock
  at S = 300, greedy decode, max_new_tokens 200, bf16, batched: qwen35-4b
  ~4 min, mistral7b-v03 ~6 min, llama32-3b ~3 min (order-of-magnitude estimates,
  flagged rough). At K = 15 that is roughly 60 / 90 / 45 minutes of generation
  per family, ~3.25 GPU-hours total plus fit reconstruction and smokes: a
  half-day on the free lane.
- If instead generation is run over the FULL paired pools (~1,300 rows) x 15
  seeds, the load rises to roughly 3.75 / 5.5 / 2.25 GPU-hours per family,
  ~11.5 GPU-hours total: an overnight free-lane run, 3-4x costlier, buying the
  option to expand grading later without regenerating. Generation scope is a
  lead decision knob.

Whether RR3's three fresh mistral seeds (30260714 +13.3, 30260715 -7.4,
30260716 +21.8; RR3 Outcome lines 457-460) count toward mistral's K, argued both
ways for the lead to decide:

- FOR counting. They are exactly the census measurement for mistral:
  matched-magnitude (dose_abs 3.665, erase-write setpoint identical to gated
  within 0.004, red-team certified), genuinely random (|cos| to c_hat <= 0.015),
  random-direction, on the same held-out confab population, scored under the
  same wide instrument and rubric (RR3 Outcome lines 482-487). Counting them
  gives continuity with the result that motivated the census and lets mistral
  reach a target K with fewer new GPU passes.
- AGAINST counting. RR3 graded those three seeds on the FULL n = 1,312 pool
  inside a mixed adjudication pool that also held the gated, baseline, and
  known arms (different denominator, different decoy composition) than the
  census's fixed S subsample and single-purpose blinded lane. Pooling them
  directly mixes denominators and grading lanes. Counting them CLEANLY would
  require recomputing each of the three deltas on the census's fixed S rows from
  RR3's persisted gitignored row-level grades (feasible, since RR3 persisted the
  per-row `sub_grade` under the data-exhaust rule), not transcribing RR3's
  full-pool numbers. Otherwise the three points sit on a different denominator
  and belong beside the census distribution as external corroboration, not
  inside its K.
- Proposal if the lead counts them: run 12 new mistral seeds so mistral's census
  K = 15 total matches qwen and llama, with the three RR3 seeds' deltas
  recomputed on the census S rows from RR3's row-level grades; if the lead does
  NOT count them, run 15 new mistral seeds and report the three RR3 seeds beside
  the distribution as external points.

DECIDED at sign (PI + lead, 2026-07-14): the RR3 seeds do NOT count toward K.
New experiment, new seeds; mistral runs 15 fresh census seeds like the other
families, and the three RR3 points are reported beside the census distribution
as external full-pool corroboration, labeled with their different denominator
and grading lane. All other knobs resolved to the drafted defaults: K = 15,
S = 300, generation subsample-only, baseline text reused byte-identical with
its grade produced fresh inside the census pool, and the qwen census magnitude
confirmed as the absolute setpoint dose_abs 12.608 (no sigma_c multiplier
asserted; the census matches the promoted operating point's realized write
value, which is the quantity the -5.13 historical delta was measured at).

The exact 45 seed values (15 per family) are consecutive per-family blocks
(qwen 41000001-41000015, mistral 42000001-42000015, llama 43000001-43000015),
CONFIRMED at sign (2026-07-14) and pinned in `cell.yaml`; all 15 mistral seeds
run fresh per the RR3-seeds decision above.

### Grading pool, pairing, and generation reuse

The shared baseline S rows and all K x S dosed rows per family enter ONE census
blinded adjudication pool (labels stripped: arm, dose, seed, role, source;
salted opaque ids; seeded shuffle), so baseline and every dosed seed are graded
under one lane, one rubric, one decoy set, keeping the per-seed paired delta
homogeneous. Baseline generation text is deterministic (greedy, do_sample=false)
and may be reused byte-identical from the family's committed baseline runlog
(qwen QH `baseline.jsonl`, mistral RR2 `heldout__baseline.jsonl`, llama RR
baseline), verified by an RG0-style byte-repro check; its GRADE is nonetheless
produced fresh inside the census pool so baseline and dosed grades come from the
same lane. Reusing the calibration/RR2 committed baseline GRADES instead is a
cheaper alternative but mixes grading lanes; it is offered as a decision knob and
not the default.

Each per-seed delta is a paired proportion difference (dosed minus baseline)
computed over the exact fixed S rows shared across arms. Any row missing or
degenerate for a given seed is reported separately for that seed, never folded
into that seed's paired delta (paired-population rule).

### Containment

Public commits carry ID-only manifests (row_key, role, split, source,
category_canon; the salted opaque-id list) and aggregate summaries only. No
question text, generation text, answer aliases, or token IDs enter any committed
file. Adjudication pools, opaque-id -> row_key mappings, fitted / frozen
directions, per-row grades, and staged inputs are gitignored, never committed.
Committed manifests under `analysis-committed/` carry sha256 hashes, counts, and
opaque ids only. This matches the RR, RR2, RR3, calibration, and signflip
containment rule.

### Deliverable

`analysis-committed/census_report.json`: per family, the K per-seed
matched-magnitude deltas (points, on the fixed S rows, with per-seed paired-n
and Wilson 95% CI); distribution summaries (median signed delta, interquartile
range, full span [min, max], fraction of seeds sharing the family's historical
sign f_s with a bootstrap 95% CI, fraction positive and fraction negative); the
pre-stated criterion evaluation per family (SURVIVES / RETIRED / INDETERMINATE,
see Gates); and the percentile at which the historical single-seed value falls
within the census distribution (qwen -5.13, mistral +7.39, llama +0.1). Plus a
short design-note paragraph in the Outcome stating, per family, whether the
single-seed family-sign reading survives as a distributional property or is
retired to seed noise, and reaffirming that no locked verdict moves.

## Prediction

Stated before the run. At matched magnitude, the random-direction placebo
response is far more seed-variable than the single-seed family-sign map implies.
Concretely: qwen's SUPPRESSION survives as a sign-consistent distributional
property (fraction of seeds with a negative delta f_neg >= 0.80, median signed
delta <= -3.0 points); mistral's RECRUITMENT does NOT survive at matched
magnitude (f_pos < 0.80, the distribution straddles zero, consistent with RR3's
already-observed 2-of-3-positive spread with one seed at -7.4), so the mistral
point of the family-sign map is retired to unresolved / seed-noise; and llama's
distribution centers near zero (|median| < 3.0 points, no dominant sign), its
built-in null holding.

## Falsifier

Pre-stated numerically and fixed before the run; it cannot be adjusted after
results. For each family with a committed non-null historical sign s (qwen
s = negative, mistral s = positive), let f_s be the fraction of the K census
seeds whose signed matched-magnitude delta has sign s, and let m be the median
signed delta over the K seeds.

- The family-sign reading SURVIVES (confirmed as a distributional property, not
  a point artifact) iff f_s >= 0.80 AND the bootstrap 95% lower bound on f_s
  exceeds 0.50 AND the median moves in the s direction with |m| >= 3.0 points
  (a floor set below both historical magnitudes 5.13 and 7.39 so it is a genuine
  bar, not one the historical points trivially clear).
- The family-sign reading is RETIRED / FALSIFIED (the single-seed sign was seed
  noise) iff f_s <= 0.60 (at least 40% of matched-magnitude seeds move opposite
  to the committed sign) OR the census interquartile range (25th to 75th
  percentile) of the signed delta spans zero (the middle half of seeds is not
  even sign-consistent).
- Otherwise the family is INDETERMINATE (0.60 < f_s < 0.80, or f_s >= 0.80 with
  sub-floor |m|): reported straight; the family sign is neither confirmed as
  distributional nor retired.

The census prediction (qwen SURVIVES, mistral RETIRED, llama null) is falsified
for a family if that family lands in a bucket other than the one predicted: if
mistral in fact clears f_pos >= 0.80 with median >= +3.0 the "mistral is seed
noise" prediction is falsified and its recruitment survives; if qwen fails
f_neg >= 0.80 or its IQR spans zero the qwen suppression reading is itself
retired. llama, having no committed non-null sign, cannot falsify a sign reading;
a llama distribution that concentrates on one sign with |median| >= 3.0 is
reported as a newly discovered llama placebo sign, not as a falsification. There
is no rescoring lane behind the blinded adjudication lane: if a family's census
distribution meets its RETIRE trigger, the sign reading is retired and the
result stands. Goalposts do not move after the result.

## Gates

Integrity and coverage gates only. This experiment has no promotion gate: its
outputs are measurements and a per-family survive/retire adjudication, and every
criterion outcome is a reportable result. Per-cell gates are in `gates.yaml`.
Wilson 95% CIs (alpha 0.05) on every rate; bootstrap 95% CI on every
sign-fraction.

- **SC0 (provenance and staging).** Every source runlog, baseline artifact,
  frozen direction JSON (`random_direction` basis and `c_hat` setpoint), and fit
  build_manifest is staged into gitignored `analysis/staged_inputs/` with sha256
  and row/vector counts recorded in a committed ID-manifest (no text). The fixed
  S subsample per family is drawn by the registered permutation seed and its
  opaque-id list committed BEFORE any generation or grading. Reused baseline text
  passes an RG0-style byte-repro check against the family's committed baseline
  runlog on the S rows.
- **SC1 (magnitude-matching).** Each seed's random-direction write is an
  erase-write to the SAME per-family setpoint (qwen dose_abs 12.608, mistral
  3.665, llama 12 x sigma_c(hs20) re-derived byte-identical from RR's committed
  llama hs20 fit manifest), with `readback_measured` within a RELATIVE tolerance
  of target of 0.5% (|readback - target| / target <= 0.005). CORRECTION NOTE
  (pre-run, user-approved 2026-07-14, recorded in instrument.repins): the
  originally signed bar was an absolute 0.01, which conflated RR3's arm-to-arm
  setpoint-identity margin (0.004, RR3 Outcome lines 482-487) with
  readback-vs-target accuracy and contradicted the qwen precedent cited beside
  it (readback 12.625 vs target 12.608 = 0.017 = 0.14% relative, signflip
  AMENDMENT lines 236-240). GPU smokes at the registered setpoints measured a
  systematic, tightly clustered RELATIVE readback offset of 0.11-0.16% in all
  three families (mistral cleared the absolute bar only because its setpoint is
  small), matching the certified precedent regime; the corrected relative bar
  keeps ~3x headroom over that regime while still failing any genuine magnitude
  error (a wrong layer, sigma, or multiplier misses by whole percents). The
  correction was made BEFORE any dosed generation ran; the falsifier, criterion,
  seeds, and setpoints are untouched. Each drawn random direction is genuinely random: |cos| to
  `c_hat` <= 0.015 and |cos| to `u_d` <= 0.015 (RR3 red-team bar). A seed whose
  write fails setpoint or randomness is voided before grading and redrawn from
  the next pre-registered seed; the void is recorded. This gate is what makes the
  K deltas a comparable single-magnitude sample.
- **SC2 (grading integrity, hash-commit-before-unblind).** Blinded context-free
  adjudication per RR3: the pool sha256 and opaque-id list are committed BEFORE
  grading; the graded-file sha256 is committed BEFORE the opaque-id -> row_key
  mapping is read; the apply tool refuses to join otherwise (enforced in code,
  not convention). CG-style grader calibration per shard AND pooled:
  clear-negative decoy agreement >= 0.95 per shard; clear-positive decoy
  agreement >= 0.60 per shard AND >= 0.60 pooled; >= 25 clear-positive decoys per
  shard (successor fix b); clear-negative decoys drawn only from the held-back
  pool (successor fix a). A shard failing either floor is voided before
  unblinding and regraded once by a fresh context-free agent; a second failure
  voids that shard's rows and is reported straight. Decoys are excluded from
  every scored rate.
- **SC3 (paired population and coverage).** Every per-seed delta is computed over
  the exact fixed S rows shared across the baseline and all K dosed seeds;
  unpaired, missing, or degenerate rows for any seed are reported separately for
  that seed, never inside its delta. Every rate carries a Wilson 95% CI; every
  sign-fraction a bootstrap 95% CI. The full K-seed ensemble is reported per
  family regardless of the survive/retire verdict. llama is reported as a
  null-control family (no committed sign to defend); the RR3 mistral seeds, if
  counted, are recomputed on the census S rows (SC3 pairing applies to them too)
  and otherwise reported beside the distribution as external points at their
  full-pool denominator, labeled as such.

## Predictions scoreboard

Calls registered 2026-07-14, pre-run, before the analysis harness was built.
No edits after results. Both predictors registered the SAME calls this time
(the PI reviewed the orchestrator's calls and explicitly agreed), so no slot
differentiates the predictors; the scoreboard still binds both against the
result.

| Predictor | qwen suppression: SURVIVES / RETIRED / INDETERMINATE | mistral recruitment: SURVIVES / RETIRED / INDETERMINATE | llama: near-zero null / newly-discovered sign | Percentile of the historical single-seed value within its census distribution (qwen -5.13, mistral +7.39) |
|-----------|------|------|------|------|
| orchestrator | SURVIVES | RETIRED (expected trigger: IQR spans zero) | near-zero null | qwen -5.13 near its census median (40th-60th pct); mistral +7.39 at 50th-70th pct |
| user | SURVIVES | RETIRED | near-zero null | agrees with orchestrator ranges |

Rationale registered with the calls: the qwen suppression is expected to
survive because the signflip experiment found it mechanistically anchored (the
future-unknown subtype concentration with a matching pre-generation projection
outlier), whereas mistral's RR3 spread of -7.4 to +21.8 across three seeds
already suggests the middle half of a 15-seed census will not be
sign-consistent.

## Outcome

Filled at resolve. Record the per-family survive/retire/indeterminate verdict
against the pre-stated criterion, the gate results (SC0-SC3), the distribution
summaries per family, where each historical single-seed value fell within its
census distribution, the scoreboard adjudication, and the one-sentence summary
that also goes into `verdict:` in the manifest. Reaffirm that no locked verdict
moved.
