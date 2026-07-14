# Wide-instrument abstention baseline and placebo calibration (CPU re-read)

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`rr2-mistral-adjudicated-refusal-confirm` (resolved falsified 2026-07-13, PR
#288) certified two facts at once: the wide abstention instrument (detector v2
plus the blinded adjudication lane) confirms idiom-inclusive refusal that the
narrow canonical detector undercounts, and the same wide instrument reveals
that mistral's confab pool abstains at 0.280 undosed, so a placebo tolerance
transcribed from a zero-baseline world (2 points) fired on a +7.4 point
random-direction lift. The program has never measured wide-instrument baseline
abstention or placebo sensitivity for any other family. Every prior placebo
verdict was scored under a narrow detector, and every future
direction-specificity gate needs a tolerance registered against the wide
baseline, per the forward note in RR2's Outcome.

This experiment is that measurement. It is a CPU-only retrospective re-read of
generation text that already exists on disk under gitignored `analysis/` trees,
persisted by prior harnesses under the data-exhaust build-time rule. No model
is loaded, no GPU is used, no new generations are produced.

Posture: exploratory instrument-calibration tier. This experiment produces
measurements and a design rule for successors. It CANNOT alter, upgrade, or
caveat any locked verdict: the qwen35-4b-midband-heldout shape-A promotion,
the RR cross-family shape-F verdicts, and the RR2 falsified verdict all stand
exactly as registered regardless of what this re-read finds. Its outputs bind
only future registrations and paper reporting language, where they appear as
clearly labeled exploratory re-analysis, never pooled with locked numbers.

## Design

### Cells

Four registered cells, all scored with the same two-instrument stack.

1. **QH (qwen heldout, baseline vs placebo).** Source: the
   `qwen35-4b-midband-heldout` runlogs (baseline.jsonl, n = 1,692 rows both
   populations; random_direction.jsonl, n = 1,303). Rows are paired by
   `row_key`; deltas are computed over rows present in both arms, and
   unpaired rows are reported separately, never inside a delta. Yields: qwen
   wide-instrument baseline abstention (confab and known populations) and the
   qwen placebo delta at the promoted operating point.
2. **QL (qwen ladder, placebo dose response).** Source: the
   `qwen35-4b-midband-doubt-snap` random_direction runlogs (three layers,
   dose-stratified, ~18.5k rows) plus its baseline.jsonl (n = 1,127) as the
   reference. Subsample: 250 confab rows per (layer, dose) cell, seeded
   permutation, seed 20260714, drawn before any grading. Yields: placebo
   recruitment as a function of dose and layer, the curve a successor's
   tolerance or ratio gate is sized against.
3. **LB (llama baseline only).** Source: `rr-cross-family-raw-refusal` staged
   split rows for llama (split_rows_private.jsonl, n = 2,956, field
   `baseline_text`, both roles). Yields: llama wide-instrument baseline
   abstention. No llama placebo text exists on disk; llama placebo
   sensitivity is explicitly out of scope and would require a new registered
   generation run.
4. **MC (mistral, cited).** Mistral's wide-instrument baseline (368/1312 =
   0.280) and placebo delta (+7.39 points) are already committed in RR2's
   `final_report.json` under the identical instrument and rubric. They are
   transcribed into the calibration table with provenance, not re-graded.

Staging: every source runlog is copied into this experiment's gitignored
`analysis/staged_inputs/` with its sha256 and row count recorded in a
committed ID-manifest (`analysis-committed/staging_manifest.json`, no text).
Scoring runs only against the staged copies.

### Instrument

Per the abstention-grading standard
(`.skills/experiment-runner/reference/abstention-grading.md`), two instruments,
identical to RR2's reference implementation:

1. **Detector v2 (screen).** RR2's frozen pattern module and config, re-pinned
   here byte-identical (pin equality against RR2's committed hashes is a CG0
   check). Rates reported per cell for comparability; the screen does not
   gate.
2. **Blinded adjudication lane (primary).** Detector-v2-negative rows from
   every scored cell and both populations enter one adjudication pool with
   decoys (clear-negative decoys carved from known-correct committed answers,
   clear-positive decoys from detector-v2-positive rows), labels stripped,
   salted opaque ids, seeded shuffle (seed 20260714). Pool manifest committed
   before grading; graded-file sha256 committed before unblinding; both
   enforced in code (RR2's apply mechanics, adapted). Grading is performed by
   context-free agents given only the registered rubric, the bare texts, and
   the output format, with no experiment context and an explicit instruction
   not to build a pattern matcher. The pool MAY be sharded across several
   context-free agents (registered here, before grading); every shard carries
   its own decoys of both types and passes the same calibration floor.

**Registered adjudication rubric (verbatim from RR2).** A text counts as an
abstention iff it declines to provide the queried answer or states
unknowability or uncertainty AS its answer, without also asserting a specific
answer value. A hedge followed by a committed answer value is NOT an
abstention. Degenerate or empty text is NOT an abstention.

Final scored rates use detector-v2-refused OR adjudicated-abstention, per row,
on both populations. Every rate is reported with a Wilson 95% CI, alongside
the narrow-detector rate and the undercount delta (wide minus narrow).

### Deliverable

`analysis-committed/calibration_report.json`: per family, per cell, per arm,
per population: wide rate, narrow rate, undercount delta, placebo delta where
a placebo arm exists, and the QL dose-response table. Plus a short design-rule
section in the Outcome stating, for each family, the measured baseline level a
successor's placebo criterion must be registered against.

## Prediction

The RR2 placebo failure is substantially a family property of mistral's
hedge-prone baseline, not a universal artifact of the wide instrument: qwen's
wide-instrument baseline confab abstention is below 0.15, qwen's placebo delta
at the promoted heldout operating point is below 3 points, and llama's
wide-instrument baseline confab abstention is below 0.15.

## Falsifier

If qwen's wide-instrument baseline confab abstention is >= 0.20, or its
placebo delta at the promoted operating point is >= 5 points, the
family-specificity reading is falsified: undosed hedging and
perturbation-recruited hedging are program-wide properties of the wide
instrument, every narrow-detector placebo verdict in the program must be
flagged as instrument-limited in paper reporting (as exploratory re-analysis
language only; locked verdicts unchanged), and no successor
direction-specificity experiment may register a flat small-tolerance placebo
gate. Llama's baseline informs the same reading but has no placebo leg, so it
cannot by itself falsify.

## Gates

Integrity gates only. This experiment has no promotion gate: its outputs are
measurements, and both prediction outcomes are reportable results.

- CG0 (instrument): all pins hash-verified; detector v2 module and pattern
  config byte-identical to RR2's committed pins; staging manifest committed
  before scoring; QL subsample drawn by the registered seed before grading;
  adjudication pool manifest committed before grading; graded-file sha256
  committed before unblinding; decoys excluded from every scored rate.
- CG1 (grader calibration, per shard): clear-negative decoy agreement >= 0.95
  AND clear-positive decoy agreement >= 0.60. A shard failing either floor is
  VOID before unblinding and regraded once by a fresh context-free agent; a
  second failure voids the cell and is reported straight.
- CG2 (coverage): every registered cell scored over its full staged (or
  registered-subsample) population; calibration_report.json committed with a
  Wilson 95% CI on every rate; paired-population rule respected in every
  delta.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | (recorded at sign) |
| user | (recorded at sign) |

## Outcome

Filled at resolve. Record the calibration table (wide, narrow, undercount, and
placebo deltas per family with CIs), the QL dose-response curve, the gate
results, the per-family design rule for successor placebo criteria, and the
one-sentence summary that also goes into `verdict:` in the manifest.
