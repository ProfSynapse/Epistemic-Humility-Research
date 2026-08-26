# Llama hs17 wide-instrument regeneration and re-score notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-26 — aggregate exhaust published to HF (user-approved)

`professorsynapse/eh-llama-hs17-wide-instrument-rescore`, revision
`e7de12a938f0133e047dafbdb442df62f7ca317a`. 8 files / ~458 KB
copy-everything mirror of `analysis-committed/` (wide-gates report, scored
summary, generation/pool/graded/applied adjudication manifests) + README +
PROVENANCE; verify gate PASS, zero exclusions, no row text. Recorded in
`docs/public-artifacts.md`. Row-level shape is possible for this cell (the
harness persisted text) but stays unpublished pending per-source license
verdicts for the parent row pools.

### 2026-08-26 — full 17-arm regeneration, blinded adjudication, gates, resolved

Generation: 17 arms (arm0 872+334, arm1 872+334, 15 random-seed arms x 872)
on the local RTX 3090, structural text-capture guard active (`runlog_contract`
+ tuner `required_fields`); first launch attempt died pre-evidence on a
missing log dir (mkdir, relaunched clean). WR-G0 checks passed pre-launch
(sha set, wide-pin hashes, 32/32 CPU persistence smoke); every production
record verified text-bearing on first rows. Lead-owned Monitor watch end to
end; one transient CUDA-preamble false alarm adjudicated against the durable
log (zero CUDA text, single healthy GPU process, rows advancing).

Adjudication lane (per `.skills/experiment-runner/reference/abstention-grading.md`):
pool of every detector-negative row across both tracked roles — 13,477 core +
658 clear-negative + 691 clear-positive decoys, 19 shards (~780 rows each),
seed 20260826, fresh salt; pool manifest committed BEFORE dispatch (c955a69c).
19 context-free opus graders, one per shard, private working dirs, rubric
verbatim + edge conventions in every prompt; pattern-classifier use forbidden
and audited (every workdir scanned: reading chunks, agent-authored
TRUE-index write scripts, verify scripts — no matchers). Lead verified every
graded file before hash-commit (line count, positional opaque_id match,
boolean-only, exactly two keys); all 19 sha256 hashes committed before any
unblinding (86c8dc07). CG1: 19/19 PASS attempt 1 (clear-negative 1.000 every
shard; pooled clear-positive 534/691 = 0.7728). Apply produced 13,477
adjudicated core rows, zero voided shards.

Gates: WR-G1 PASS 0.7305, WR-G2 PASS lift 0.6319, WR-G3 PASS ratio 9.34,
WR-G4 NOT-ADJUDICABLE (fired 0/334, as pre-stated). Lead re-derived every
gate number independently from raw scored rows + id maps + the lead's own
graded-file copies — exact match with `wide_gates_report.json`. Verdict and
full table in `AMENDMENT.md` Outcome (Outcome A; both predictors correct).

Run-log anomaly recorded straight: arm0 confab has 25 duplicated row_keys
(897 lines / 872 unique; crash-resume overlap class). Duplicates agree on
all flags; the 24 detector-negative duplicated rows were blind-graded twice
in different shards with 24/24 verdict agreement (unplanned inter-grader
reliability check). Gate populations are unique row_keys; no number moved.
Companion note: `wide_rescore_scored_summary.json` arm0 narrow_confab n is
per-line (897); WR gates and the G3 narrow companion are unaffected (arm0
narrow rate enters descriptively only).

### 2026-08-26 — sign-time feasibility probe (PASS) and sign

Probe performed by direct artifact read in the primary checkout (lead
session), immediately around sign:

- All six frozen-reuse inputs exist and sha256-match the pins carried over
  from `llama-hs17-direction-specificity` `cell.yaml` (u_d, c_hat, gate_fit,
  standardization, dose_source, row_pools — six exact matches).
- Dose verified: `full_summary.json /layers/hs17/dose_target =
  4.954897429720482`.
- Row pools verified by direct read of `reused_rows_manifest.json`:
  confab held_out 872, known_correct_answered held_out 334 (fit splits
  581/222 and fit_only 947 untouched by this cell).
- Wide pins present: `abstention-wide-instrument-calibration/detector_v2.py`
  plus the committed patterns/rubric (hash equality is WR-G0's job at run).
- Adjudication tooling present: census `apply_adjudication.py` lane.
- Random directions reproducible from the registered recipe + seeds
  (910001..910015, identical to the resolved narrow census).
- Self-blinding intact: no result computed; existence/coverage/sha only.

Signed 2026-08-26 (lead + user). Both predictors on record for outcome A
(wide replicates + specific). Engine exception declared (intervention path;
the bridge requires the identical engine as the resolved narrow cell).

- (add dated entries as the experiment progresses)
