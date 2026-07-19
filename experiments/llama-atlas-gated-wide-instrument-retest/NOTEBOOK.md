# Llama atlas-sited gated caution ladder, wide-instrument retest notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-19 (harness-build, unblinding tooling): With the pool manifest
  frozen in git (b7bfa022) and the CG1-gated blinded grading lane running
  under the lead's orchestration (8 context-free graders, one per shard --
  out of scope for this harness-build assignment, and the grader working
  dirs under the session scratchpad were not inspected), ported
  `apply_adjudication.py` from `abstention-wide-instrument-calibration/`,
  cross-checked against `rr3-corrected-placebo-replication/` and
  `.skills/experiment-runner/reference/abstention-grading.md` (read all
  three in full first). Kept the reference implementations' core guarantees
  in code: commit-hash-before-unblind (raises SystemExit otherwise) and a
  positional graded-file/id-map join (raises on length mismatch, reorder, or
  non-boolean `is_abstention`). Added `gates_lib.cg1_evaluate_shard` /
  `cg1_pooled_clear_positive` (ported verbatim from the calibration cell;
  0.95/0.60 floors match this cell's own gates.yaml CG1 exactly; the pooled
  rate is reported only -- this cell registers no pooled gate, unlike RR3's
  successor fix (b)). Simplified the calibration/RR3 multi-cell
  `voided_cells` set down to a single `experiment_voided` boolean, since this
  harness has exactly one adjudication cell; verified in the smoke suite
  that a terminal CG1 void on one shard excludes an otherwise-passing second
  shard's rows too (matches "second failure voids the cell, reported
  straight" when there is only one cell). Beyond the port, `cmd_apply` also
  rebuilds the post-adjudication per-rung table
  (`analysis-committed/llama/post_adjudication_wide_table.json`) by
  re-scanning every RunLog row plus the reused baseline arm and taking
  refused_wide_adjudicated = detector_v2 screen OR the unblinded verdict,
  fail-closed to "not abstention" (with a `n_pending_adjudication` coverage
  counter) for any row with no verdict yet. Verified this table-building
  path against the REAL 30-rung RunLog directory (not real graded files --
  none exist, grading is the lead's lane) with an empty adjudication map:
  confirmed `refused_wide_adjudicated` reduces exactly to
  `refused_wide_screen` and `n_pending_adjudication` exactly equals the
  detector-negative count when nothing has been adjudicated. Wrote
  `test_apply_adjudication_smoke.py` (synthetic 3-line shard + graded-file
  fixtures, isolated to pytest tmp_path, never touching real analysis/
  analysis-committed): 7/7 pass, covering the hash-refusal path, the
  positional-mismatch raise, and the attempt-1-vs-attempt-2 CG1 void ladder.
  Combined with the existing suite: 45/45 CPU tests pass. Did NOT run
  `apply` against any real graded file. `gates.yaml`/`cell.yaml` diff
  remains empty.
- 2026-07-19 (harness-build, completion): Pipeline (PID 30797) exited cleanly
  ("[pipeline] family llama done in 7726s") after ~2h9m wall clock; zero
  Tracebacks anywhere in the run log. All 30 rungs present under
  `analysis/llama/runlog/` (28 gated: 4 layers x 7 dose multipliers, plus the
  2 registered random_direction rungs at hs20 dose12/16); all staged to the
  durable exhaust store (`ehr-exhaust/.../runlog/`, `.../analysis-committed/`,
  `.../adjudication_shards/`, 41M total). G0 re-verified post-hoc from
  committed artifacts: hook placement passed (decoder_blocks [19,21,22,25] =
  h-1 for h in [20,22,23,26]); per-layer FIT gate AUC all >=0.999 (floor
  0.90), with the confounded random-direction reference reported per layer
  (hs20=0.808, hs22=0.816, hs23=0.912, hs26=0.696); double-fit byte-identical
  held at every layer (no SystemExit raised, confirmed by the log's zero
  Traceback count and the clean 4-layer completion -- this check is a hard
  raise, not a logged boolean); pre_sweep_bracket_check passed at every layer
  (token movement confirmed at strongest dose, 8/8 probe rows); the
  batched-vs-sequential parity NOTE (not a gate) recurred at hs20 (4/8
  mismatches) and hs26 (1/8), zero at hs22/hs23 -- consistent with the
  earlier single-layer finding, still informational only. Wide-instrument
  pins re-verified byte-identical to abstention-wide-instrument-calibration's
  current committed source at report time. Built the committed
  PRE-ADJUDICATION per-rung table
  (`analysis-committed/llama/pre_adjudication_wide_vs_narrow_table.json`,
  31 rows: 1 undosed-baseline reference + 30 rungs) from the already
  ID-free `fit_dose_ladder_report.json`. Ran the FINAL
  `build_adjudication_pool.py` (seed 20260719, defaults) over the complete
  22,647-row detector-negative core (2009 baseline + 22,358 gated legitimate
  rows across dose*role*layer + 1,152 random_direction confab rows feeding
  175 clear_positive decoy candidates) plus 4,085 clear_negative candidates;
  produced 8 shards (`llama_wide_retest_shard_00..07`, ~2850 rows each,
  21-22 clear_positive decoys/shard, comfortably above the >14 CG1 lesson
  floor) under gitignored `analysis/shards/`, with the ID-only manifest
  committed to `analysis-committed/adjudication_pool_manifest.json`
  (verified zero occurrences of "text" in the committed manifest; the
  gitignored shard pool files correctly do contain text, confirmed via
  `git check-ignore`). This overwrote the earlier partial smoke-test output
  (`--seed 1 --target-shard-size 50`, which had written only shard_00) in
  `"w"` mode; confirmed exactly 8 shard files on disk post-run, matching the
  manifest 1:1, so no stale smoke-test shard survives as an orphan. Did NOT
  run any blinded grading. Did NOT commit. Re-ran all 38 CPU smoke tests
  post-completion: still 38/38 passing.
- 2026-07-19 (harness-build, cont.): Launched the full ladder in the background
  (`pipeline.py all --family llama --batch-size 8 --i-know-this-runs-on-gpu`,
  PID 30797); `materialize_rows.py` and the layer-20 FIT fit + hook-placement
  assertion + pre-sweep-and-parity smoke completed cleanly (see the dose_ladder.py
  repin trail in experiment.yaml for the parity-smoke self-correction), then
  dose-sweep generation began writing RunLogs under `analysis/llama/runlog/`.
  Wrote `build_adjudication_pool.py` (new module, not a repin -- registered in
  experiment.yaml with the same `none-new-module` precedent as detector_v2.py)
  to build the CG1 blinded pool once generation completes; per the harness-build
  assignment this script BUILDS the pool and STOPS, it does not grade. A small
  dry run against the first three completed rungs (hs20 dose2/4/6, ~800 rows
  each) caught a real bug before trusting the module for the final build:
  `dose_ladder.load_baseline_wide_by_key`'s `role` field is always None
  (`baseline_graded_private.jsonl` carries a different pre-fit `role_candidate`
  label, not the FIT-population role), so every baseline row was silently
  dropped from the pool's TRACKED_ROLES filter (dry run: n_rows_by_arm.baseline
  went 0 -> 2009 after joining against `joined_rows_private.jsonl`'s row_key ->
  role map instead). This gap is benign inside dose_ladder.py itself (its
  paired net-lift lookups match by row_key against already role-filtered FIT
  row lists and never read that field back), so no change was needed there.
  Fixed and repinned (experiment.yaml repins trail has both hashes and the
  full diagnosis). Set up a persistent background monitor that stages each
  completed RunLog (jsonl + .meta.json + .summary.json) to the durable exhaust
  store `/home/profsynapse/code/ehr-exhaust/llama-atlas-gated-wide-instrument-retest/runlog/`
  as it lands (invariant A6), and separately watches for Traceback/Error/FAIL/
  SystemExit/CUDA-OOM/pipeline-exit signals.
- 2026-07-19 (harness-build): Staged the two private inputs neither existed
  anywhere under /home/profsynapse/code (row pool, atlas capture) by pulling
  them read-only from their Modal volumes (no compute launched, data
  staging only): `eh-doubt-snap-cross-family`
  (`doubt-snap-cross-family-r1/llama32_3b_instruct/analysis/
  split_rows_private.jsonl` -> `analysis/staged_inputs/llama/
  split_rows_private.jsonl`, 2956 rows; and `.../baseline_graded_private.jsonl`
  -> same dir, 4000 rows, the registered `baseline` arm) and
  `eh-jspace-family-atlas` (`jspace-family-atlas-r1/llama32_3b_instruct/
  analysis/atlas_capture/{capture.jsonl,checkpoint.json,tensors/}` ->
  `experiments/jspace-family-atlas/analysis/llama32_3b_instruct/atlas_capture/`,
  2956 safetensors files, 1017M). The CLI `modal volume get` silently
  downloaded only ONE file for the 2956-file `tensors/` directory across
  three repeated attempts (once returning 0 bytes, once 358KB) despite
  reporting success; worked around with a small script using the Modal
  Python SDK's `Volume.iterdir(recursive=True)` +
  `read_file_into_fileobj` instead (script:
  `/tmp/.../scratchpad/pull_atlas_tensors.py`, not committed). **A1
  resolution**: `materialize_rows.py --family llama` ran clean against the
  staged inputs -- anchor coverage 2956/2956 = 1.0 at all four candidate
  layers (20, 22, 23, 26); NO layer was missing from the atlas's full-depth
  capture, so NO GPU recapture was needed. FIT population: confab_fit=581,
  known_correct_answered_fit=222, unknown_refused_fit_only=947 (held-out
  872/334 counted for provenance, not touched). Also initialized the
  `synaptic-tuner` submodule in this worktree (was an empty dir after the
  worktree checkout; `git submodule update --init synaptic-tuner`), needed
  for `MechInterp.intervention` and `shared.utilities.run_log`.
- 2026-07-19: Scaffolded and SIGNED. Design from the task #7 designer report
  (lead-verified against rr-cross-family-raw-refusal, abstention-wide-instrument-
  calibration, jspace-family-atlas, and the fleet model_matrix.yaml). Lead
  adjudications folded in pre-sign: A0 fresh GPU re-run (rr dosed text
  unrecoverable), A2 FIT-only, A3 random_direction at hs20 dose 12 and 16, A4
  keep hs26 in-grid, A5 hidden-state-index convention pinned in AMENDMENT
  Design/Substrate, A6 durable exhaust staging to
  /home/profsynapse/code/ehr-exhaust/ before worktree teardown. Harness modules
  copied VERBATIM from rr at sign (pins identical to rr's); the scorer swap
  (wide instrument primary), single-family trim, and full-ladder scoring (no
  FIT dose selection) happen in the harness-build assignment via audited
  `bin/exp repin` entries, mirroring rr's own lifecycle. A1 (atlas anchor
  coverage) resolves at staging and is recorded here. Local 3090 launch
  pre-approved by the PI 2026-07-18.
