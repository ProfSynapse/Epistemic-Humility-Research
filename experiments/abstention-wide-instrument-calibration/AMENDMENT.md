# Wide-instrument abstention baseline and placebo calibration (CPU re-read)

Status: resolved (2026-07-14; measurements certified by adversarial red-team review; falsifier not fired; QL cell terminally voided per CG1 and reported straight as narrow-only).

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
| orchestrator | Family-specific: qwen wide baseline in the 0.05-0.12 band and placebo delta under 3 points; llama baseline under 0.15; mistral remains the outlier hedger. (recorded 2026-07-14, pre-run) |
| user | Per-family differences, and qwen holds: qwen stays inside the prediction bands (baseline < 0.15, placebo delta < 3 points). (recorded 2026-07-14, pre-run) |

## Outcome

**Verdict: resolved.** The falsifier did not fire; the family-specificity
reading survives; the prediction was NOT cleanly confirmed and the misses are
recorded straight. All numbers below were certified by an adversarial
red-team review (CERTIFIED-MEASUREMENTS) that independently re-derived every
headline rate bit-for-bit from the row-level artifacts before this verdict
was written.

### Calibration table (confab population, Wilson 95% CIs)

| Family | Wide baseline | Narrow baseline | Undercount | Placebo delta (wide, paired) |
|--------|---------------|-----------------|------------|------------------------------|
| mistral7b-v03 (MC, cited from RR2) | 0.280 [0.257, 0.305] | 0.159 (v2) | +12.2 pts | +7.39 pts (recruitment) |
| qwen35-4b (QH) | 139/1332 = 0.104 [0.089, 0.122] | 58/1332 = 0.044 | +6.1 pts | -5.13 pts (suppression), n = 1,286 paired |
| llama32-3b (LB) | 239/1453 = 0.164 [0.146, 0.184] | 52/1453 = 0.036 | +12.9 pts | no placebo text on disk (out of scope as registered) |

Qwen placebo detail: paired baseline wide 139/1286 = 0.108 [0.092, 0.126] vs
random_direction wide 73/1286 = 0.057 [0.045, 0.071]; the CIs do not
overlap. Narrow delta -2.88 points, same sign. The matched-magnitude random
direction SUPPRESSES qwen hedging; it does not recruit it. Known-population
(cost) rates are 0 everywhere they are covered, on every family and arm.

### Falsifier adjudication

The registered falsifier trigger is "placebo delta >= 5 points" and its
consequent interprets a fire as establishing program-wide
"perturbation-recruited hedging". The measured delta is -5.13 points:
suppression, the opposite of recruitment. Under the signed reading the
trigger does not fire (-5.13 is not >= 5); under an absolute-magnitude
reading it would fire while asserting a consequent the data directly
contradicts. The signed, consequent-coherent reading is adopted as the only
one under which the falsifier's own stated inference is consistent with the
evidence; the red-team review reached the same recommendation independently
and the adjudication was made under its certification, not chosen for the
scoreboard. Qwen's baseline leg (0.104 < 0.20) does not fire either. The
family-specificity reading also survives on grounds independent of the
trigger: the three families' undosed wide baselines are genuinely graded
(0.104 / 0.164 / 0.280) and the placebo response is family-specific in SIGN
(qwen -5.13, mistral +7.39).

The prediction is nonetheless not cleanly confirmed, recorded straight:
the placebo leg ("below 3 points") was written as a near-no-op claim and a
5.13-point-magnitude effect exceeds that band even though its direction is
suppressive; the llama baseline leg ("below 0.15") is missed at 0.164 with
the CI entirely above 0.15 (and the LB unknown_refused carve makes 0.164 a
conservative lower bound, which strengthens the miss). Both are reported as
findings, not failures of the instrument.

### Gates

- CG0 (instrument): PASS. All pins hash-verified; detector v2, patterns, and
  grader byte-identical to RR2's committed pins; staging manifest (8 files,
  31,620 rows) committed before scoring; pool manifest (11,788 core + 956/236
  decoys, 17 shards) committed before grading; every graded-file sha256
  committed before unblinding; decoys excluded from all scored rates. One
  instrument correction mid-run, H3-pattern, documented in NOTEBOOK
  2026-07-14 and instrument.repins: the attempt-1 opaque ids collided across
  (hs_index, dose) points in QL; blinding and per-line grades were
  unaffected, the join was corrected to positional with per-line id
  assertions, and the red-team confirmed the corrected CG1 was computed from
  the same committed grades with no gate, floor, rubric, or population
  change.
- CG1 (grader calibration): PASS on all 16 applied shards; clear-negative
  agreement 1.000 on every shard graded (zero over-credit bias in seven
  independent context-free graders). QL_shard_07 failed clear-positive
  (0.286), its fresh-agent regrade failed again (0.429), and per the
  registered on_second_failure rule the QL CELL IS TERMINALLY VOIDED for
  wide rates and reported straight as detector-v2-only. Observation, not a
  rescue: both failures were on the same 14 planted clear-positives (the
  round-robin partition gives each shard a disjoint decoy draw) while ten
  other QL shards passed at 0.692-0.929, so the void is consistent with a
  hard decoy subset meeting a coarse-grained floor (9/14 effective).
- CG2 (coverage): PASS. QH, LB, MC scored in full (confab wide coverage
  complete, n_uncovered 0 on both graded families); QL handled per CG1's
  registered void path; Wilson CIs on every rate; paired-population rule
  respected in every delta (1,286 paired qwen confabs; 46 unpaired baseline
  confabs and 343 unpaired knowns reported separately, never inside a
  delta); calibration_report.json committed.

### QL narrow dose-response (exploratory, detector-v2-only; wide voided)

Random-direction narrow refusal is flat-to-falling in dose on every layer
(hs20: 0.020 at dose 2 to 0.000 at dose 20; hs23: 0.052 to 0.000; hs26:
0.048 to 0.036; hs30: 0.048 to 0.016) against a ladder baseline narrow rate
of 0.044, consistent in sign with the QH suppression finding.

### Known-population coverage caveat (for successors)

Clear-negative decoys are carved exclusively from detector-negative
known-correct rows and decoys are excluded from scored rates, so the wide
known (cost) rates are sparsely covered (QH 77/360, LB 85/556). This touches
only the cost side, which is 0 everywhere covered and is not a prediction
target; confab coverage is complete. Successors that need tight cost CIs
should draw clear-negative decoys from a held-back pool rather than from
scored rows.

### Scoreboard adjudication

Neither predictor is fully correct; both called the shape.
- user ("per-family differences, qwen holds; baseline < 0.15, delta < 3"):
  per-family differences CORRECT (0.104 / 0.164 / 0.280); qwen baseline leg
  CORRECT (0.104); placebo leg INCORRECT in magnitude (5.13 points,
  suppressive).
- orchestrator (qwen baseline 0.05-0.12; delta < 3; llama < 0.15; mistral
  outlier): qwen baseline leg CORRECT (0.104); mistral-outlier leg CORRECT;
  placebo leg INCORRECT in magnitude; llama leg INCORRECT (0.164).

### Design rule for successor placebo criteria (the deliverable)

Robust to the falsifier-reading question: a successor direction-specificity
experiment must NOT register a flat small symmetric placebo tolerance. The
placebo criterion must be registered against the per-family measured
wide-instrument baseline (qwen 0.104, llama 0.164, mistral 0.280) and must
tolerate several points of non-directional movement in EITHER sign at
matched magnitude (qwen moved -5.13, mistral +7.39), for example via an
effect-ratio gate (gated lift vs |random lift|) or a two-sided tolerance
sized from these measurements. CG1 lesson for any sharded blind lane: use
more clear-positive decoys per shard or a pooled clear-positive floor;
a 14-decoy draw gives the 0.60 floor coarse granularity and exposes a cell
to decoy-draw variance.

One-sentence summary (manifest `verdict:`): Resolved: wide-instrument
baseline abstention is family-graded (qwen 0.104, llama 0.164, mistral
0.280) and placebo response is family-specific in sign (qwen suppresses
-5.13 points where mistral recruits +7.39), so the falsifier did not fire
and RR2's placebo failure is confirmed family-specific, while the
prediction's near-no-op placebo leg and llama band were missed and the QL
dose-response cell voided terminally under the registered grader
calibration rule.
