# Write-direction naming battery: what is the mid-band c_hat write, behaviorally? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
