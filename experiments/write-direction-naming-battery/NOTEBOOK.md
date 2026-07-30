# Write-direction naming battery: what is the mid-band c_hat write, behaviorally? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-30 - Taxonomy calibration FAILED: disagreement 0.43 vs floor 0.05; AXIS_G_VOID fires as registered (LEAD)

The blinded 200-row calibration ran exactly as registered: pool manifest
git-committed before grading (2cab5d4c), isolated adjudicator (fresh
agent, opaque_id and text only, id maps untouched, per-row reading with
no keyword classifier, method report on file), graded-file hashes
git-committed before unblinding (e880ab87), then the pinned
apply_form_adjudication.py join.

Result (analysis-committed/form_adjudication_applied_manifest.json,
verbatim): core disagreement 86/200 = 0.4300 against the registered
floor 0.05, FAIL. Clear-positive decoy agreement 19/19 = 1.00 against
the 0.60 floor, PASS; the user-approved 19-vs-25 decoy deviation
recorded in the previous entry ends up moot, since the failure is
entirely on the core disagreement check, a fully registered floor with
no shortfall question. Lead re-derivation from the id maps, graded
files, and merged runlogs independently reproduces 86/200 and the
per-shard rates (0.42/0.36/0.56/0.38).

VERDICT: AXIS_G_VOID, exactly as registered (AMENDMENT.md "If the
taxonomy fails its calibration slice, Arms A and D are instrument-void
and no name is earned from them"; gates.yaml G2
on_calibration_failure: axis_G_void). Axis G resolves VOID, not GRADED
and not BINARY. The Arm A form-pass distributions recorded earlier
(F4 monotone in dose, F2+F3 flat) are NOT citable: the instrument that
produced form_class failed its construct check. Arms B and C proceed
unaffected; they read only existing validated fields.

Diagnostic observation, descriptive only, no goalpost implication: the
mismatch direction is one-sided. Of the 86 core disagreements, 79 are
rows the automated taxonomy classed F1_committed_assertion that the
blinded judge read as F2 (62) or F3 (17); the reverse direction
(automated F2/F3, judge F1) totals 2. The regex pattern battery
under-detects hedging and non-answerability relative to careful
reading. Any wider-recall taxonomy would be a NEW instrument requiring
its own registration and calibration in a future cell; nothing is
re-run here.

### 2026-07-30 - Calibration pool built; decoy floor shortfall ruled a governed deviation, proceed at 19 (LEAD + USER)

The pinned pool builder ran over the sidecar-merged rows
(`--runlog-dir analysis/runlog_form_merged`, pinned file unmodified) and
wrote 4 blinded shards plus `analysis-committed/form_adjudication_pool_manifest.json`
(git-committed 2cab5d4c BEFORE any grading, per the registered order). Core
slice: 200/200 exact, stratified across the five real Arm A sub-arms.
Clear-positive decoys: 19 against the registered minimum of 25
(AMENDMENT.md "a minimum of 25 decoys, mirroring M1's C1 floors";
gates.yaml G2 `min_decoys: 25`).

The shortfall is data-determined, not a builder choice: the decoy source is
registered as the placebo sub-arms' F2/F3 rows, and the placebo arms
produced exactly 19 such rows in total (a_placebo_0p5: F2=2 F3=5;
a_placebo_1: F2=5 F3=7; counts in the pool manifest coverage block). The
candidate pool is exhausted; no selection rule can reach 25 without
redefining the decoy source post-data, which would be its own goalpost
move.

RULING (user, 2026-07-30, on lead escalation): proceed to blinded
adjudication with all 19 decoys as a RECORDED governed deviation from the
registered floor. The agreement threshold itself is unchanged: decoy
agreement >= 0.60 now means at least 12/19 (0.632) with failure at
11/19 (0.579), i.e. the check runs at reduced statistical power but the
same bar. The 200-row core disagreement check is unaffected. The lead
declined to make this call unilaterally (D-3 precedent: weakening a
registered constraint is rejected); the deviation is user-approved and
recorded here and in the resolve report. If the calibration fails its
registered thresholds on this slice, the registered consequence stands
unweakened: axis G void, Arms A and D instrument-void.

Next: isolated adjudicator (fresh agent, sees only opaque_id and
generation text, never the id maps or automated labels) grades the 4
shards three-way {F1, F2, F3}; each graded file's sha256 is committed
before that shard's id map is read (apply_form_adjudication.py enforces
this order).

### 2026-07-30 - Arm A form-pass complete, acceptance gate PASS; driver pinned (LEAD)

The Arm A form-pass regeneration authorized in the previous entry is
complete: all 7 sub-arms at 400/400 (2800 rows), zero duplicate row_keys,
sidecar at 2800/2800 with only {row_key, answer_value, answer_text},
elapsed ~38 min. ACCEPTANCE GATE PASS: 2800/2800 rows compared against the
phase 2 runlogs on semantic_refuse, refused_v2, degenerate, well_formed,
terminated_naturally, readback_measured (abs tol 1e-6), 0 mismatches
(16800 field comparisons) - the runner's in-run check, the runner's
standalone recompute, and a 200-row lead re-derivation all agree, and the
lead re-derived two arms' full form_class distributions exactly. The
regeneration is therefore the SAME behavior as phase 2 with form_class
attached; the phase 2 runlogs remain the evidence of record for all
non-form fields.

`run_arm_a_form_pass.py` is pinned into instrument.modules after review
(imports the pinned modules unmodified, 15/15 pins verified intact before
and after the run). Its acceptance_check initially compared the 8-row
smoke output against the full 400-row phase 2 file and reported a false
key-mismatch failure; the comparison was scoped to produced keys and
re-scored, with the smoke runlog itself untouched - recorded here because
a false-FAIL that had been rationalized INTO a pass would have been the
dangerous direction, and this was the reverse.

Form_class distributions are RECORDED (runner report, lead-verified) but
NOT adjudicated: gates.yaml G2's taxonomy calibration (blinded 200-row
slice, isolated adjudicator) must pass before any F1/F2/F3 count is
citable, per on_calibration_failure: axis_G_void. Noted for the record
without adjudication: the clear-positive decoy source (placebo-arm F2/F3
hits) totals 19 rows against the registered min_decoys: 25; the pinned
pool builder runs next and whatever it reports is adjudicated against the
registered gate text as-is. Pool input path: the pinned builder assumes
unredacted runlogs carrying form_class; the run's redacted
runlog_form rows are joined with the private sidecar text into
analysis/runlog_form_merged/ (private, never committed) and the builder
consumes that directory via its --runlog-dir argument, unmodified.

### 2026-07-30 - port-fidelity audit adjudicated; harness pinned; Arm A form-pass regeneration authorized (LEAD)

**Audit result (red-team, delegated).** The three files carrying the
registered byte-for-byte port claim (grader.py, gen_lib.py, detector_v2.py;
AMENDMENT.md line 235 lineage margin-mapping/harness/) are AST-identical to
their source after docstring stripping; detector_v2_patterns.yaml is
byte-identical; render.py is construction-identical to the heldout lineage
with inert WDNB_ namespacing. Differential execution over 550 real
margin-mapping exhaust rows: the port and the source produce byte-identical
grades, and the port's recomputation matches margin-mapping's persisted
values on all 12 alias-independent fields, zero mismatches. Invariant audit
over all 6105 rows of this run: zero violations (counts, arm/readout/
multiplier/dose_abs transcription, readback nullity pattern, grader field
implications, no redaction leaks). All eight harness files are now pinned in
instrument.modules; the lead recomputed every sha256 independently before
pinning and verified the full pin table programmatically (15/15 match).

**Finding F1/F2 adjudication: the first run executed two of the three
registered graders.** cell.yaml registers the grader chain grader:grade,
detector_v2:grade_one_v2, form_taxonomy:classify (execution.graders) AND
registers redact_fields stripping answer_text/answer_value from runlog rows.
The run wired only the first two graders (the taxonomy module was built
under a parallel assignment and was not present in the run worktree), so
runlog rows carry no form_class, and because redaction is applied at write
time (correctly, per the pinned instrument; audit confirmed zero text
anywhere in the runlogs), the F1/F2/F3 split cannot be recomputed offline.
Ruling: complete the registered instrument by REGENERATING ARM A ONLY (the
only arm form scoring is registered for; gates.yaml G2 arm: A) with the full
three-grader chain wired, via a NEW standalone driver that imports the
pinned modules unmodified. The regeneration writes to a namespaced path
(analysis/runlog_form/), never touching the phase 2 runlogs, and writes a
PRIVATE adjudication text sidecar under analysis/ (answer text keyed by
opaque ids, for the registered blinded calibration slice only; gitignored,
never committed). Acceptance check: greedy decode on the pinned surface is
deterministic, so every regenerated row must reproduce the phase 2 runlog's
verdict fields (semantic_refuse, refused_v2, degenerate, well_formed,
terminated_naturally, readback_measured within float tolerance) row-by-row;
any mismatch halts the pass and comes back to the lead. This is instrument
completion under the signed design, not a design change: no gate, threshold,
population, seed, or arm moves.

**Finding F3 (recorded).** pipeline.py's in-run G1 check compared the wide
refused_v2 rate (0.040) against the heldout comparator
baseline.confab.refused rate (0.0), whose key is the narrow detector; the
mismatch is strict-direction only (wide >= narrow) and the like-for-like
narrow comparison (0.000 vs 0.0, exact) also passes, so the G1 lift stands
on both readings, consistent with Ruling 1 of the previous entry.

**Also recorded.** run_summary.json's per-arm refused/correct summary lines
are vacuous (null) because grade_row never emits bare refused/correct keys;
axis arithmetic will be computed from the runlogs directly.
cell.yaml:30 expected_config_sha remains TBD_AT_SIGN and nothing computes
it; the instrument pins now carry the run-to-code binding that field was
meant to provide, and filling it retroactively would be a pointless repin
cycle; recorded as vestigial. materialize_rows.py's default heldout rows
path points at a gitignored working file in the main checkout; P_CONFAB
question text is machine-local, consistent with the containment rules, and
the committed ID manifests remain the reproducibility surface.

### 2026-07-30 - generation complete; completion-report adjudication; taxonomy instrument pinned (LEAD)

**Generation complete.** All 14 arms at exact plan counts (7x400 Arm A, 5x421
Arm B, 2x600 Arm C), total 6105/6105, elapsed ~4480 s, zero duplicate row_keys
within any arm, `readback_measured` non-null on 100% of dosed rows. Verified
independently by the lead from `analysis/runlog/*.jsonl` (line counts, five
spot-checked rates, and the b_neg_2 readback error re-derived; all matched the
runner's report exactly).

**Ruling 1, G1 field choice.** `gates.yaml` G1 does not pin a detector field.
Adjudicated on the wide detector `refused_v2` as primary, narrow
`semantic_refuse` recorded alongside. a_baseline `refused_v2` 0.0400 (16/400)
vs the held-out comparator baseline confab refused rate, diff within the 0.05
tolerance; narrow reading 0.0 also passes. c_baseline `correct_v2` 0.9917
(595/600) >= 0.90 floor. G1 PASS under either reading; the mid-run
halt-and-lift stands.

**Ruling 2, Arm B collapse boundary.** Per the registered C1 construct gate
(`regime_invalid_degenerate_ceiling: 0.20`): b_neg_2 degenerate rate 0.8979
(378/421) is REGIME-INVALID; excluded from form scoring with the exclusion
count committed, exactly as registered. b_neg_1 at 0.1021 (43/421) is below
the ceiling and stays valid, with its elevated rate (and 0.2969
truncated-without-natural-stop) reported alongside per
`degenerate_rate_reported_per_arm_and_dose`. How the collapse shapes the axis
B read (including the slot-2 O-2 scenario) is deferred to the naming-table
adjudication after form scoring; no axis arithmetic was read today.

**Ruling 3, full-run offtarget/parity.** Full-run offtarget collection was
never registered; the smoke-phase parity check (offtarget_abs_max 0.0, both
directions) is the standing evidence. The full run's per-row
commanded-vs-measured readback (worst abs error 0.046 on b_neg_2, under the
0.05 smoke floor everywhere) is recorded as descriptive support only.

**Taxonomy instrument pinned.** The five files built under the harness
assignment (`form_taxonomy.py`, `form_patterns.yaml`,
`build_form_adjudication_pool.py`, `apply_form_adjudication.py`,
`test_form_taxonomy.py`) are added to `instrument.modules` with sha256 pins in
`experiment.yaml`, after lead review: the classifier implements the registered
F5>F4>F3>F2>F1 table verbatim, consumes only fields merged by the two
registered graders (no imports of them), and its 36/36 tests pass in this run
worktree. The five builder judgment calls are signed off: (1) runlog naming
`analysis/runlog/<arm_key>.jsonl`, confirmed against the actual runlogs;
(2) scan text prefers `answer_value` with `answer_text` fallback; (3) F4/F5
rows excluded from the adjudication pool core because the registered gate is
explicitly the F1/F2/F3 boundary; (4) single-pass PASS/FAIL with
clear-positive decoys only, exactly as `gates.yaml` registers it; the CG1
reference's clear-negative decoy pool and regrade ladder are NOT added
post-sign (adding unregistered checks after signing is goalpost movement in
either direction); (5) Arm A placebo sub-arms as the clear-positive decoy
source. Note for the record: the generation run predates this pin, so the
runlogs carry no `form_class` field; classification is post-hoc by
construction, which is the registered design (the classifier is deterministic
over already-written rows and cannot influence generation).

**Harness port files committed, fidelity audit delegated.** The eight harness
files the runner built and ran (`grader.py`, `gen_lib.py`, `detector_v2.py`,
`detector_v2_patterns.yaml`, `render.py`, `steer_lib.py`, `pipeline.py`,
`materialize_rows.py`) were still untracked in the run worktree at completion.
They are committed now for provenance (they are the code that produced the
runlogs), but they are NOT added to `instrument.modules` yet:
`detector_v2_patterns.yaml` is byte-identical to
`margin-mapping/harness/detector_v2_patterns.yaml`, while the seven .py files
differ textually from every candidate source cell. The registered claim is a
byte-for-byte port of the scoring logic with per-cell headers; a delegated
port-fidelity audit (every behavioral difference vs the named source lineage,
docstring/constant adaptations listed separately) runs before form
classification is trusted, and the module pins for these eight follow that
audit's PASS.

### 2026-07-30 - draft written; blinding disclosures recorded

Drafted under a lead design assignment. Draft only: not signed, no GPU work, no
model loads, nothing committed. `bin/exp validate` passes with the draft in
place (96 experiments, zero warnings attributable to this slug).

**Recomputation provenance for the AMENDMENT disclosures D-1 through D-4.** All
four were computed on 2026-07-30 from the M1 ladder's on-disk, gitignored row
logs at `experiments/margin-mapping/analysis/runlog/qwen35_4b__*.jsonl` (11
files: `baseline_reused` plus rungs 0p0625, 0p125, 0p25, 0p5, 0p75, 1, 1p5, 2,
3, 4; each exactly 760 rows = 400 confab + 360 known_correct_answered; each row
carrying `answer_text`, `answer_value`, `refused_v2`, `semantic_refuse`,
`correct_v2`, `well_formed`, `degenerate`, `matched_pattern_ids`,
`readback_measured`). Computation was read-only, ran under
`/home/profsynapse/miniconda3/bin/python3`, and wrote nothing. The exact
per-rung tables are reproduced in the AMENDMENT disclosure section; the
one-liner that produced them should be promoted to a committed
`analysis-committed/disclosures/recompute_m1_rungs.py` at sign so the numbers
are reproducible rather than quoted.

D-3 additionally joined the 133 PopQA known rows to `datasets/popqa/test.jsonl`
on the numeric suffix of the `popqa:<id>` row_key. Join coverage was 133/133
with no id-namespace mismatch. The within-pool median `s_pop` was 680. Note that
Arm C's split is a DIFFERENT median, computed over the 2,744-row
`correct_on_answerable` census pool, and must be frozen before generation.

**Instrument facts established during drafting** (all read-only, all from
existing files):

- There is no shared grader module in this repo. Every steer cell owns a
  byte-for-byte port of `grader.py` / `gen_lib.py` / `detector_v2.py`. This cell
  follows that convention.
- `semantic_refuse` is literally
  `bool(answer_value) and ("i don't know" in answer_value.lower())`
  (`experiments/doubt-snap-cross-family-confirmatory/gen_lib.py:117`). The wide
  detector `is_refused_v2` adds the `diverse_idioms` list from
  `detector_v2_patterns.yaml` and is reported-only in the cells that carry it.
- No hedging, qualification, or partial-answer predicate exists anywhere in the
  grader stack. The F2/F3 classes of the Arm A taxonomy are genuinely new code.
- The random-direction placebo is reimplemented per cell, not imported; the
  construction is `unit(np.random.default_rng(seed).normal(size=hidden_dim))`,
  the same one `direction_fit.fit_directions` uses
  (`experiments/placebo-seed-distribution-census/direction_draw.py`).
- `experiments/margin-evidence-responsiveness-worldknown/harness/census.py` line
  17 documents `s_pop` as a field of its gitignored sidecar, and the sidecar does
  not carry it. Any `s_pop` join must target `datasets/popqa/test.jsonl`. Worth
  a one-line correction to that docstring under separate housekeeping.

**Open provenance problem raised to the lead.** The KG mechanism note
`caution-residual-ablation-relaxes-overrefusal-asymmetrically` (over-refusal
0.994 to 0.030) has no re-derivable governed source in this checkout. Paper 3
states the number and defers ownership to paper 5; paper 5 does not restate it;
`papers/series/plan.md` line 55 records the ownership move as pending; the
underlying sweeps survive as config only, with their declared output paths
absent from disk. See the AMENDMENT section "The ablation result the assignment
asked us to replicate". This is why Arm B is registered as an analogue rather
than a replication.

**Not yet done, gated on lead and PI review of this draft**: harness build
(materialization, runner, `form_taxonomy.py`, `form_patterns.yaml`), population
ID manifests, scoreboard predictor calls, `bin/exp sign`.
