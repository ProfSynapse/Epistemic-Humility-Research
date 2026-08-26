# Wide-instrument re-score of the gated-controller and layer-contrast controls (Qwen3-4B)

Status: resolved 2026-08-20. Verdict: prediction confirmed; all gates pass
(see Outcome).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 5 Appendix D records this gap explicitly: the random-direction and
permuted-gate controls behind Sections 4.5 (the raw-base gated-controller
headline, `experiments/doubt-gated-caution-tighten`) and 4.6 (the layer-site
contrast, `experiments/j-space-calibrated-layer-contrast-qwen3-4b`) were scored
under the narrow canonical detector only, and have never been re-scored under
the wide two-instrument stack (frozen widened pattern detector plus blinded
context-free LLM grading) that every Section 4.8 number rests on. The census
found qwen's wide-instrument placebo response suppressive rather than
confounding at a different operating point, which is reassuring but is not a
measurement at these operating points. Section 6.4 currently carries the gap as
a stated limitation.

Posture: exploratory control-validation cell. It produces no new headline
number; it tests whether two existing control conclusions survive an
instrument change. Resolved either way, its output is a sentence for Section
6.4 (gap closed, conclusions survive) or a substantive limitation upgrade
(conclusions do not survive the wide instrument).

Feasibility note recorded at registration: the original row-level generations
for both source cells are not on disk (gitignored `analysis/` directories, not
retained) and were never packaged to the HF exhaust datasets (verified against
`professorsynapse/eh-readout-rows` and
`professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`, 2026-08-18). The cell
therefore regenerates the arms from the committed pipelines before re-scoring,
with a parity gate (WG-G0) that stops the cell if regeneration is not faithful
to the committed summaries.

## Design

Substrate: `unsloth/Qwen3-4B` raw-base bf16, local 3090 lane, greedy decode,
exactly as pinned in the two source cells.

Stage 0 (regeneration + parity). Re-run the committed generation pipelines at
their pinned script shas, seeds, and committed direction artifacts
(`analysis-committed/u_d_L34.json`, `c_hat_L34.json`,
`random_direction_L34.json` in the 4.5 cell; the corresponding committed
artifacts in the 4.6 cell) for every arm the original summaries report:

- 4.5 cell: gated, random_direction, permuted_gate (seed 20260707), on the
  held-out pool (185 confabulation-prone / 258 known-correct rows).
- 4.6 cell: the hs23 and hs34 gated arms and their controls on the 443-row
  held-out pool.

Stage 0 output is scored with the ORIGINAL narrow canonical detector and
compared against the committed `analysis-committed/full_summary.json` of each
source cell (see WG-G0).

Stage 1 (wide re-score). All regenerated arms are scored under the wide
two-instrument stack exactly as pinned by
`experiments/abstention-wide-instrument-calibration`: detector_v2
(`detector_v2_patterns.yaml`, sha
36422e01ae03008c2f71f180158c63950e14f8dfc1279c4e654c89fb831841d9) and the
context-free LLM grading lane (`grader.py`, sha
bd5a974d7aa56cc28d8e6380e6176b81ea646fa276760feb31dc3d6bdc681218, rubric
rr2-verbatim), rows stripped of arm/dose/role labels and shuffled under a
fixed permutation, clear-positive and clear-negative decoys included, graded
manifest hashed and committed before unblinding. No instrument component is
refit or retuned for this cell.

Two harness-review notes, recorded before any run. First, Stage 0 captures
per-row generation text by tee-ing the source cells' own pinned functions via
import (the committed CLI entry points aggregate and discard row text); the
run therefore includes an internal-consistency check in addition to WG-G0:
the narrow summary recomputed from the teed rows must equal the run's own
aggregate exactly, else the capture is not trusted. Second, the
known-population coverage caveat documented in the wide-instrument
calibration cell (decoys carved from known-correct rows are excluded from
every scored rate) carries over here unchanged and is read the same way.

Estimated grading volume: on the order of 2,500-3,500 grader calls across both
source cells' arms (non-refused rows only reach the grading lane). GPU cost:
regeneration only, local 3090, no cloud spend.

Exhaust retention (lesson from this cell's own scoping): at resolve, the
regenerated rows and their wide-instrument grades are packaged as HF data
exhaust through the data-exhaust skill (license gate permitting), so the rows
this cell regenerates outlive its gitignored analysis directory and no future
cell has to regenerate them again.

## Prediction

Under the wide instrument, both narrow-detector control conclusions survive at
both operating points: the gated arm's confabulation-abstention lift is at
least 3x the random-direction arm's lift (effect-ratio criterion, RR3 form),
and the permuted gate still degrades the controller (cost side and selectivity
gap) with a bootstrap CI excluding zero.

## Falsifier

Any control conclusion reverses under the wide instrument: WG-G1's effect
ratio lands below 3.0 at the 4.5 operating point (specificity of the Section
4.5 result does not survive the instrument change), WG-G2's permuted-gate
cost-excess CI includes zero (the gate's contribution is a narrow-detector
artifact), or WG-G3's layer-site advantage loses its sign or its CI includes
zero (the 4.6 conclusion is instrument-dependent). Any firing upgrades the
Section 6.4 gap to a substantive limitation and blocks promotion of the
affected result.

## Gates

- WG-G0 (parity precondition, pre-outcome stop): for every regenerated arm,
  the narrow-detector rate must match the committed
  `full_summary.json` rate within +/- 2.0 percentage points (anchors for the
  4.5 cell: gated 73.5% / 3.1%; random_direction 7.0% / 2.3%; permuted_gate
  40.0% / 22.9%; 4.6 anchors per that cell's committed summary). Any arm
  outside tolerance stops the cell at a negative-feasibility record
  (regeneration-invalid); Stage 1 does not run and no wide numbers are
  reported.
- WG-G1 (random-direction specificity, per operating point): wide-instrument
  effect ratio = (gated lift over undosed baseline) / (random-direction lift
  over undosed baseline), computed as in RR3. PASS at >= 3.0. The
  random-direction lift is also reported signed, against the census
  expectation that qwen's placebo response is suppressive.
- WG-G2 (permuted-gate contribution): the gated quantity is the wide-instrument
  known-correct cost excess, permuted-gate cost minus true-gate cost, on rows
  paired by row key (decoy carving is per-arm, so pairing is by explicit key
  intersection with drop counts reported). PASS if the cost excess is positive
  with paired bootstrap 95% CI excluding zero (anchor: narrow-detector cost
  excess 22.9% - 3.1% = 19.8 points). The confabulation-tightening difference
  between the arms is reported descriptively and is not gated.
- WG-G3 (layer-site conclusion, added at harness review 2026-08-18, before
  any regeneration or scoring): the Section 4.6 cell has no placebo arms, so
  WG-G1/WG-G2 literally cover only the 4.5 cell; this gate covers 4.6. PASS if
  the wide-instrument hs23-vs-hs34 clean-tightening advantage retains its
  positive sign with paired bootstrap 95% CI excluding zero (anchor:
  narrow-detector +22.7 points). WG-G0 parity for this cell spans all four
  regenerated layers (hs23/26/29/34; the committed pipeline regenerates all
  four with no subset flag), while Stage 1 wide scoring remains hs23/hs34 per
  the confirmed scope.
- Indeterminate: if the wide-instrument grading lane fails its own decoy
  calibration, the cell records instrument-invalid, reports nothing, and may
  be re-run after the lane is fixed; this is not a gate outcome.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | WG-G0 passes (parity holds); WG-G1 holds (ratio >= 3.0); WG-G2 survives (CI excludes zero); WG-G3 holds (advantage keeps sign, CI excludes zero) |
| user | WG-G0 "it works"; WG-G1 holds; WG-G2 survives; WG-G3 holds (call recorded 2026-08-18, before sign) |

Calls recorded 2026-08-18, before any regeneration or scoring. The two
predictors converged independently; both flagged WG-G0 as the leg carrying the
real uncertainty (months-later regeneration on a possibly drifted CUDA stack).

## Scope confirmation (2026-08-18, PI)

Option A confirmed: the 4.5 cell (`doubt-gated-caution-tighten`) plus the
primary 4.6 contrast (`j-space-calibrated-layer-contrast-qwen3-4b`) only. The
two 4.6 same-model replications are out of scope for this cell and may be
covered by a follow-up if this cell's result warrants it.

## Outcome

Resolved 2026-08-20. Verdict: prediction CONFIRMED — both narrow-detector
control conclusions survive the wide two-instrument re-score at both
operating points; no falsifier fires; the Section 6.4 gap closes.

Gate results (machine reports promoted to `analysis-committed/results/`;
rates below are quoted from `wide_gates_report.json` and
`wg_g3_paired_bootstrap.json`):

- WG-G0 (parity): PASS, `verdict: parity_holds`, `stage_1_authorized: true`.
  Every regenerated arm in both cells matched its committed narrow-detector
  rate to 0.0pp (13/13 rate pairs byte-exact), under the per-cell historical
  tuner pins of NOTEBOOK launch-correction 6. `results/parity_report.json`.
- CG1 (grading-lane calibration): PASS on all four shards at attempt 1 —
  clear-negative and clear-positive decoy agreement both 1.0 on every
  shard, no voided cells, 2,677 core rows applied.
- WG-G1 (random-direction specificity): PASS. Wide gated confab tightening
  74.05% (137/185, Wilson 95% [67.3, 79.8]) vs undosed baseline 11.35%
  (21/185): gated lift +62.7pp. Random-direction 7.03% (13/185): lift
  -4.3pp, suppressive, matching the census expectation quoted in the gate
  text. Effect ratio 14.5 against the 3.0 threshold.
- WG-G2 (permuted-gate contribution): PASS. Paired known-correct cost
  excess (permuted minus gated) +20.6pp, paired bootstrap 95% CI
  [+14.8, +26.3], n=209 paired rows (23 dropped from each side by the
  per-arm decoy carve, reported not hidden), seed 20260818; narrow anchor
  +19.8pp. Descriptively (not gated): the permuted gate also drops confab
  tightening to 40.0% vs the true gate's 74.05% (paired n=185, zero
  drops). The harness build's two flagged ambiguities stand as flagged:
  the selectivity-gap formula is unregistered, so its point estimate
  (+54.6pp) is reported without a verdict and without a joint CI.
- WG-G3 (layer-site conclusion): PASS. Wide clean tightening hs23 89.19%
  (165/185) vs hs34 66.49% (123/185); paired advantage +22.70pp — equal
  to the narrow anchor — with paired bootstrap 95% CI [+16.2, +29.7],
  n=185, zero pairing drops. Computed by the lead with the cell-pinned
  machinery (score_wide `_wide_rate_flags`/`paired_flag_lists`,
  stats_lib `bootstrap_paired_diff_ci`, seed 20260818, 10,000 resamples),
  since the harness scorer reports the 4.6 contrast informationally only;
  `results/wg_g3_paired_bootstrap.json` records the computation.

Instrument-change magnitude: across all 2,677 core rows, exactly 5 gained
adjudicated-abstention beyond detector_v2 (the grading agents' remaining 15
positive labels were the 15 clear-positive decoys, all caught). At these
operating points the wide instrument barely moves qwen raw-base rates,
consistent with the wide-instrument calibration cell's family-specificity
reading.

Scoreboard: both predictors (orchestrator and user) called all four gates
correctly; the shared flag on WG-G0 as the risk-bearing leg was borne out
in process (six pre-GPU launch corrections) but not in outcome (parity
byte-exact).

Process record: the six launch corrections (artifact restores, import-path
extensions, config shim, mining rerun and its ordering fix, per-cell tuner
pins) are documented in NOTEBOOK.md and RUNBOOK.md; none edited a pinned
script or moved a goalpost. The registered unblinding order held: pool
manifest committed (PR #526) before any grading; graded-file sha256s
committed (PR #527) before any id map was read; four context-free grading
agents (rubric rr2-verbatim, no pattern matching, counts-only reporting)
each passed an independent lead recount before hash commit.

Exhaust retention: the packaging of regenerated rows and wide grades via
the data-exhaust skill, registered above, is owed at this resolve and
remains open pending the license gate and user approval of the dry-run
card; tracked as this cell's follow-up, not dropped.

One-sentence summary (also in `verdict:`): Both control conclusions survive
the wide two-instrument re-score — WG-G1 effect ratio 14.5, WG-G2 cost
excess +20.6pp with CI excluding zero, WG-G3 layer advantage +22.7pp with
CI excluding zero — closing the paper 5 Section 6.4 instrument gap.
