# j-space-layer-contrast-rep2-multisource notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-09: draft scaffold created (`bin/exp new --type steer-cell
  j-space-layer-contrast-rep2-multisource`) in worktree
  `/home/profsynapse/code/ehr-worktrees/jspace-rep2`, branch
  `exp/j-space-layer-contrast-rep2-multisource`. GPU checked idle
  (`nvidia-smi`: 0% util, 1 MiB used, no processes) before any GPU work.

- 2026-07-09: dual-exclusion resolution verified by direct script run
  (`mine_multisource_pool.resolve_excluded_questions()`): 739 predecessor-split
  keys + 2,263 rep1-pool keys = 3,002 union keys, ALL 3,002 resolved to a
  normalized question via the `ah_stage0/candidates.jsonl` /
  `ah_stage0/expansion/expansion_candidates.jsonl` caches, 0 unresolved.
  Post-exclusion candidate pools: kuq_ku_unknown=3,234, kuq_ku_unknown_x=2,491,
  selfaware_unanswerable=987 -- all comfortably above the per-source stop
  targets (70/80/70) and the registered floors (200 total / 40 per harder
  source).

- 2026-07-09: known-side reuse materialized (CPU-only, no GPU) via
  `materialize_known_side_reuse.py` reading rep1's private artifacts from
  worktree `/home/profsynapse/code/ehr-worktrees/jspace-layer-replication`
  (branch `agent/jspace-full-run`, commit `7cf4c444`). Result: 1,957
  known_correct_answered rows copied, 7,828 tensors kept (= 1,957 x 4 layers,
  matches expectation exactly). Local copy hashes: rows
  `0751146e3fe77fb90833041188330b15b6adfd549b484fe575be543feb486fef`, anchors
  `d04020dbf86e9ade996aa62f211c5a29cccce3077e6ebb80ca0dad67815e5f65`. Recorded
  in `analysis-committed/known_side_reuse_manifest.json`.

- 2026-07-09: multi-source confab mining launched on the local 3090
  (`mine_multisource_pool.py`, no args, default targets 70/80/70 per source).
  First launch attempt crashed with `torch.AcceleratorError: CUDA error:
  unknown error` inside the `torch.cuda.empty_cache()` cleanup call, with zero
  rows generated before the crash (no output files, no scanned= log lines).
  A minimal isolated repro (load model, generate one row, empty_cache) run
  immediately after succeeded cleanly, and GPU was confirmed idle again
  (0%/1 MiB) before relaunch -- read as a one-off transient WSL2/CUDA hiccup,
  not a reproducible fault in this script. Relaunched successfully; running
  in background, log at `analysis/mine_multisource_pool.log`, generations
  flushed every 25 rows to `analysis/multisource_pool_generations.jsonl`.

- 2026-07-09: all harness scripts (`mine_multisource_pool.py`,
  `materialize_known_side_reuse.py`, `extract_multisource_confab_anchor.py`,
  `pipeline_multisource.py`, `run_contrast.py`, `analyze_paired_outcomes.py`)
  pass `py_compile` and `--help` cleanly. `run_contrast.py`'s module-level
  surface was refactored to defer its torch/MechInterp-dependent imports
  (`model_lib`, `pipeline_multisource`) into the functions that actually need
  them, so `mcnemar_exact` / `paired_confab_outcomes` stay importable by
  `analyze_paired_outcomes.py` without a GPU-capable environment. Verified:
  `synaptic-tuner` submodule was not initialized in this fresh worktree
  (`git submodule status` showed a leading `-`); ran
  `git submodule update --init synaptic-tuner` to fix `MechInterp` imports for
  `model_lib.py`/`pipeline_multisource.py`.

- 2026-07-09: first mining pass completed and FAILED its own registered G0
  floors: `total=146 by_source={'kuq_ku_unknown': 70, 'kuq_ku_unknown_x': 6,
  'selfaware_unanswerable': 70}`, script printed `ERROR: G0 floors not met
  (total>=200: False, harder-source>=40 each: True)` and returned exit 1.
  Diagnosis before taking any further action (per the stop-gate rule --
  floor failures are stop-not-outcome, not "proceed to see what happens"):
  read the log tail and cross-checked against
  `analysis/multisource_pool_generations.jsonl` (4,793 rows, exactly
  1,404+2,491+898). `kuq_ku_unknown_x` was genuinely EXHAUSTED at its full
  post-exclusion pool (2,491/2,491 scanned, only 6 confabs, ~0.24%
  conversion) -- no further supply exists there under the locked
  dual-exclusion rule. `kuq_ku_unknown` (1,404/3,234 scanned) and
  `selfaware_unanswerable` (898/987 scanned) had both stopped EARLY because
  they hit their own per-source operational stop-targets (70/70), which are
  my own mining-script knobs, not part of the locked G0 floor language
  (locked language only fixes >=200 total and >=40 per harder source; it
  does not fix per-source stop-targets). The shortfall was therefore an
  under-provisioned operational knob, not exhausted supply or a genuine
  floor failure of the registered design.

- 2026-07-09: resumed the SAME mining invocation (script's own
  `read_existing_rows`/`prior` cache confirmed by reading `run()`: rows
  already scanned are looked up by `row_key` and skipped, no
  re-generation) with `--target-kuq-ku-unknown 999
  --target-selfaware-unanswerable 999` to exhaust the remaining supply in
  the two under-scanned sources under the exact same loaders/exclusion
  rule/floors -- no gate, threshold, source, or exclusion rule was changed.
  `kuq_ku_unknown_x`'s target was left untouched (already exhausted,
  resolves from cache only). GPU reconfirmed idle (0%, 1 MiB) before
  relaunch. Result: `kuq_ku_unknown` scanned to full exhaustion
  (3,234/3,234, 139 confabs, ~4.3%), `selfaware_unanswerable` scanned to
  full exhaustion (987/987, 76 confabs, ~7.7%). Final:
  `total=221 by_source={'kuq_ku_unknown': 139, 'kuq_ku_unknown_x': 6,
  'selfaware_unanswerable': 76}`.
  `analysis-committed/multisource_pool_manifest.json` counts confirm
  `g0_total_met: true`, `g0_harder_sources_met: {kuq_ku_unknown: true,
  selfaware_unanswerable: true}`. G0 mining floors PASS: 221 >= 200 total,
  139 >= 40 and 76 >= 40 for the two harder sources.

- 2026-07-09: anchor extraction run (`extract_multisource_confab_anchor.py`)
  over all 221 fresh confab rows: `n_rows_extracted: 221`, i.e. anchor
  coverage is exactly 221/221 (100%), satisfying the G0 "anchor extraction
  covers every eval row" check for the confab side. Known-side anchors were
  already covered verbatim by the earlier reuse materialization
  (1,957/1,957).

- 2026-07-09: 8-row smoke run (`run_contrast.py --mode smoke --n-rows 8
  --fresh --i-know-this-is-the-multisource-replication-run`). Doses
  selected exactly as locked: hs23=25.0, hs26=75.0, hs29=125.0, hs34=175.0.
  Readback: `frac_readback_within_tol=1.0` on all four arms (readback means
  24.9997/74.9936/125.0067/175.0440 against targets 25/75/125/175, all well
  within 5%+0.5). Collapse: `collapse_rate_on_dosed=0.0` on all four arms.
  `g0_smoke_pass: true`. Before this run, the submodule's checked-out commit
  in this worktree (`e4ca5d4`, from before the branch's fork point) does not
  contain `shared/utilities/run_log.py` -- confirmed present at the merged
  `cd30d482` (tuner `main`, "Merge pull request #141 from
  ProfSynapse/feature/runlog"), which was already a local git object (no
  network fetch needed). Temporarily detached the submodule worktree to
  `cd30d482` (`git -C synaptic-tuner checkout --detach cd30d482`) to
  exercise the RunLog import for this smoke only, confirmed via
  `git diff --submodule=short -- synaptic-tuner` that this showed only as an
  UNSTAGED working-tree change in the superproject (never `git add`'d,
  never committed), then restored the submodule to `e4ca5d4`
  (`git -C synaptic-tuner checkout e4ca5d4`) immediately after the smoke and
  reconfirmed `git status --short -- synaptic-tuner` was clean before any
  commit. RunLog operative check: `analysis/runlog/smoke/{hs23,hs26,hs29,
  hs34}.jsonl` were created, each with exactly 8 lines (one per smoke row)
  plus a `.meta.json` fingerprint sidecar; file mtimes advanced from
  15:51:16 (hs23) to 15:52:16 (hs34), roughly a minute apart across the
  four arms -- confirming genuine per-row, per-arm incremental persistence
  during the run rather than a single end-of-run dump. This is the same
  wiring pattern used by `j-space-cross-family-layer-contrast`, now
  confirmed operative end-to-end in this experiment ahead of sign. This
  worktree's own submodule pin stays at `e4ca5d4` (no run_log.py) until the
  branch is rebased onto current `main` per `LAUNCH-PLAN.md`; a future
  `bin/exp sign` on this branch must happen AFTER that rebase so the import
  resolves from the merged pin without needing this manual detach-and-test
  maneuver again.

- (add dated entries as full-run results land)

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 5 files / ~2.34 MB, built at repo commit f06d9a3b.
- HF repo: `professorsynapse/eh-j-space-layer-contrast-rep2-multisource` (dataset)
- HF revision: `08a4052d98ad912c0e64a8085b23ec46284b86fc`
