# Wide-instrument re-score of the gated-controller and layer-contrast controls (Qwen3-4B)

Status: draft (not signed; do not launch as confirmatory evidence).

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

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
