# Qwen3-4B family atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-08-11 (bookkeeping: `AMENDMENT.md` header corrected to match machine
  state; no goalpost implications). Header still read "draft (not signed; do
  not launch as confirmatory evidence)" — stale boilerplate left over from
  before sign-time. `experiment.yaml` has read `status: resolved` with
  `verdict: FALSIFIER FIRED...` since 2026-07-21, and the "Outcome" section
  below has documented the same since that date. Corrected the header to
  state the true status (resolved, FALSIFIER FIRED) and to point at
  `experiment.yaml` and the "Outcome" section, following the precedent set
  by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s 2026-07-20 header correction.
  No signed content (question, prediction, falsifier, gates, Outcome)
  touched.

- 2026-07-21 (AG1/AG2: profile + read-panel stage, `profile_and_read_family_atlas_panel.py score --cell-id qwen3_4b_raw_base`). Reads only; no pinned file edited.

  **Permission blocker, resolved by container re-run (precedent: gemma-4-e4b-family-atlas hit the identical issue).** First attempt ran directly on the host (`analysis/qwen3_4b_raw_base/read_panel_run1.log`, exit 1, 67s): the full profile+panel computation completed, but the final `write_json` to `analysis-committed/qwen3_4b_raw_base/atlas_summary.json.tmp` raised `PermissionError` -- capture's earlier docker run left `analysis-committed/qwen3_4b_raw_base/` (and `analysis/qwen3_4b_raw_base/atlas_capture/`) `root:root`-owned on the bind mount, unwritable to the host `profsynapse` user. No `sudo` available (non-interactive, no password). Re-ran the SAME unmodified script inside the same pinned `mechinterp-runner` container (`sha256:d445...5c3d23c`, `DOCKER_HOST=unix:///var/run/docker.sock` override, no `--gpus` -- script is CPU-only) so root-in-container matches the directory's root ownership; no host permission escalation, no pinned-file edit, no parameter change. Log `analysis/qwen3_4b_raw_base/read_panel_run2.log`, exit 0, wall clock 68s (matches the 71.27s persistence declaration). Wrote `analysis-committed/qwen3_4b_raw_base/atlas_summary.json`.

  **AG1 (profile):**
  - `eff_dim_frac_every_layer`: 37 `per_layer` entries, hs_index 0-36 inclusive. Pass.
  - `profile_reproducibility` (20% FIT-row subsample, sorted row_key + `random.Random(20260707).shuffle` + slice, 265 of 1325 FIT rows, re-run at all 37 layers via the pinned module's own `eff_dim_frac`/`build_layer_matrix`/`load_captures` directly, no reimplementation): full-profile peak hs_index 5; subsample peak hs_index 5; delta 0 against the +/-1 tolerance. Pass. Script (diagnostic, not committed): `/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/ag1_subsample_reproducibility_qwen3.py`; output at `analysis/qwen3_4b_raw_base/ag1_subsample_reproducibility.json` (gitignored).
  - Profile shape: eff_dim_frac rises from hs_index 0 (0.000755) to a single global maximum at hs_index 5 (0.014891, depth_frac 5/36 = 0.1389), falls back through hs_index 6-19 (0.0135 down to 0.0075-0.0096 band), stays flat/low (0.0068-0.0095) from hs_index 20 through 36 with no second maximum approaching the hs_index-5 peak. hs_index 5's depth_frac (0.1389) is below `gates.yaml falsifier_restated`'s 0.20 interior lower bound -- an early-exterior peak, matching the shape jspace-family-atlas found for llama/mistral and gemma-4-e4b-family-atlas found for gemma (all four families now peak in the outer 20% of depth on the early side). Lead adjudicates the falsifier call; this entry reports the shape only.

  **AG2 (read panel), no numeric pass/fail per `gates.yaml` (the numbers are the atlas):**
  - Per-layer held-out AUROC (point [95% CI], seed 20260707, 2000 bootstrap resamples): doubt ranges 0.500 (hs0) up to 1.000 (hs27-33), climbing steeply from hs1 (0.880) and staying >=0.975 from hs5 onward. caution ranges 0.500 (hs0) up to 0.913 (hs30), staying in a 0.6-0.7 band through hs1-20 then rising to 0.79-0.91 from hs21 onward. raw_refusal ranges 0.500 (hs0) up to 0.975 (hs32-34), similarly flat ~0.73-0.76 through hs1-20 then rising to 0.81-0.97 from hs21 onward.
  - Layers clearing >=0.80 on ALL THREE axes simultaneously: hs_index 22 through 36 (15 layers). Restricted to the falsifier's interior band, strictly inside (20%, 85%) depth (hs/36 in (0.20, 0.85), i.e. hs_index 8 through 30): hs_index 22 through 30 (depth_frac 0.611-0.833) qualify.
  - At hs_index 5 (the profile's own peak): doubt 0.975 [0.966,0.983], caution 0.670 [0.619,0.718], raw_refusal 0.737 [0.703,0.771] -- caution and raw_refusal both below 0.80 at the profile's own peak layer.
  - At hs_index 34 (the fleet's ported L34 write site): doubt 0.999 [0.999,1.000], caution 0.905 [0.883,0.925], raw_refusal 0.975 [0.967,0.982].
  - Random-direction control (best-orientation AUROC, no fitting): mostly near chance but several layers read well above 0.5 on `ref_vs_known` specifically -- hs9 0.911, hs12 0.928, hs19 0.884, hs21 0.892, hs24 0.982, hs32 0.870, hs36 0.838 -- while `ref_vs_confab` stays <=0.69 everywhere. Per the module's own reading convention, the doubt axis's AUROC at those layers should be read against its own layer's `ref_vs_known` control value, not against 0.5; e.g. at hs21, doubt 0.992 vs control 0.892 is a much smaller effective margin than 0.992 vs chance. Full per-layer control table and AUROC table in `atlas_summary.json`.

  Committed `analysis-committed/qwen3_4b_raw_base/atlas_summary.json` only (aggregate, ID-free: no row_key list, no question/answer/alias text, no token_ids -- verified by substring scan before staging; the two literal `row_key`/`answer` substring hits are inside prose field names/values (`refused_pool_split.method`, `ref_vs_answered`), not real IDs or text). Row-level intermediates (`atlas_capture/`, `read_panel_run1.log`, `read_panel_run2.log`, `ag1_subsample_reproducibility.json`) remain gitignored under `analysis/`. Not resolved; verdict left for the lead.

- 2026-07-21 (signed revision 1: render env-var wiring fix, lead-authored).
  First capture launch (capture_run1, container on the pinned image, CUDA
  up, provenance line logged) exited 1 on the FIRST rendered row:
  `render_qwen3_atlas.py` read only the cell-specific
  `QWEN3_ATLAS_RENDER_MODEL/REVISION` env vars, but the shared
  `capture_family_atlas_cell.py` exports `FAMILY_ATLAS_RENDER_MODEL/REVISION`
  from `cell.yaml` (the contract `render_gemma_atlas.py` follows). Zero rows
  captured, so no data is affected. Fix (two hunks in `_tokenizer()` + the
  module docstring): read the shared FAMILY_ATLAS_* names first, retain
  QWEN3_ATLAS_* as a standalone-smoke fallback; rendered surface unchanged
  (system prompt, chat template, thinking-off pin all untouched). CPU smoke
  after the fix: `render()` under FAMILY_ATLAS_* env produces the expected
  surface (trailing empty `<think>` block at the anchor), and the no-env
  error path still raises. Re-signed immediately (`bin/exp sign`), so the
  pins record the fixed module; the crashed run's log is retained at
  `analysis/qwen3_4b_raw_base/capture_run1.log` (exit_code 1).

- 2026-07-21 (recovery: the 341 known_correct_answered row_keys' question
  text, closing the blocker the prior entry flagged). Lead-scoped task: the
  341 missing texts were never truly lost -- `mine_known_correct.py` only
  SELECTED which candidates were known-correct (that selection is frozen as
  the 341 row_keys in `split_manifest.json`); the text lived in that
  script's INPUT, `expansion_candidates.jsonl`, which is deterministically
  rebuildable on CPU from local datasets. No GPU, no sign, no push.

  **Recovery chain** (new script, `rebuild_expansion_candidates.py`, this
  directory; ports three historical pipeline stages VERBATIM, adjusting
  only input paths -- see its own docstring for full citations):

  1. **AF-600 exclusion set** (the one root unknown the lead flagged). Its
     builder, `build_ae_base_pool_rows.py`, and the `load_selfaware_pool`
     function it depends on (POOL_SEED 20260701), were never merged to
     main -- recovered by reading them out of the ABANDONED local branch
     `amendment-ae-base-doubt-coupled-caution` (commit `07c2a0c9`, confirmed
     NOT an ancestor of HEAD via `git merge-base --is-ancestor`; retrieved
     with `git show 07c2a0c9:<path>`, read-only, nothing checked out from
     it). `load_selfaware_pool` itself is independently still live and
     committed at `experiments/common/readouts/amendment_u_unified_extract.py`
     (identical body; the abandoned script's own docstring calls it
     "vendored" from that exact module). The one substitution: the original
     GPU extraction file the algorithm reads as `gate_rows`
     (`archive/experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/.../rows.jsonl`)
     is gone everywhere; substituted with the project's own committed,
     order-preserving distillation of that EXACT file,
     `experiments/common/artifacts/selfaware_gate_pool/selfaware_gate_rows_frozen.jsonl`
     (PROVENANCE.json cites the identical source path + config sha; this is
     the same substitution already relied on elsewhere in the project, e.g.
     Amendment Y's own live extraction manifest cites this same frozen file
     as its `gate_rows_source`). Rebuilt pool: 600 rows, 600 unique
     normalized questions (verified -- no accidental collision).
  2. **candidates.jsonl** (the mined 5,000) rebuilt verbatim from
     `archive/experiment/phase1/probe/amendments/amendment_ah_stage0_candidates.py`
     (SEED 20260703), gated by the rebuilt AF-600 set, from local
     `datasets/selfaware/SelfAware.json` + `datasets/kuq/{knowns_unknowns,unknowns_all}.jsonl`.
  3. **expansion_candidates.jsonl** (13,496) rebuilt verbatim from
     `archive/experiment/phase1/probe/amendments/amendment_ah_stage0_expand_candidates.py`
     (same seed), gated by AF-600 ∪ mined, from the same KUQ files plus
     `datasets/triviaqa-rc-nocontext/validation.jsonl` and
     `datasets/popqa/test.jsonl`.

  **Verification gates** (all hard-asserted in the script; independent
  target numbers fetched from `professorsynapse/eh-doubt-on-command`'s own
  `metadata/stage0_candidates_manifest.json` and
  `metadata/expansion_candidates_manifest.json` -- the ORIGINAL Amendment AH
  run's own committed provenance, not derived from anything in this
  recovery):

  | gate | result |
  |------|--------|
  | AF-600 pool size == 600 | PASS |
  | AF-600 unique normalized questions == 600 | PASS |
  | stage0 candidates n_total == 5000 | PASS |
  | stage0 composition (kuq_ku_unknown 1768 / selfaware_answerable 2034 / selfaware_unanswerable 732 / kuq_ku_known 466) | PASS, exact |
  | stage0 known/unknown split (2500/2500) | PASS |
  | expansion n_total == 13496 | PASS |
  | expansion composition (triviaqa 6000 / popqa 4000 / kuq_ku_unknown_x 3496) | PASS, exact |
  | expansion 11-way KUQ category split | PASS, exact (all 11 categories match, e.g. "future unknown" 672, "counterfactual questions" 485, ..., see script) |
  | join: all 430 known_correct_answered row_keys resolve (0 still missing) | PASS |
  | join: no empty question text or aliases among resolved | PASS |
  | join: resolved-key prefix breakdown matches the pre-verified split (ahx::triviaqa 370, ah::kuq_ku_known 26, ah::selfaware_answerable 22, ahx::popqa 12) | PASS, exact |
  | zero overlap between the originally-resolved 89 keys and originally-missing 341 keys | PASS (89/341/0, confirms they partition the 430 as expected) |
  | **cross-check against ALREADY-VERIFIED text**: for every `ahx::` row_key this rebuild produces that `a0_pool_v21_questions.jsonl` (the trusted staging pool) ALSO already covers, the question text is byte-identical | PASS, 907 keys checked, 0 mismatches -- independent positive evidence beyond count-matching |

  All 12 gates PASS. Script + verification JSON:
  `rebuild_expansion_candidates.py` (committed, no row text) writes
  `analysis/rebuilt_af600_pool.jsonl`, `analysis/rebuilt_candidates.jsonl`,
  `analysis/rebuilt_expansion_candidates.jsonl`,
  `analysis/rebuild_verification.json` (all gitignored, verified via
  `git check-ignore` before writing). Wall clock: 0.86s.

  **Wired into `materialize_rows.py`**: now imports
  `rebuild_expansion_candidates`'s `build_af600_pool` /
  `build_candidates` / `build_expansion` directly (cheap, ~1s, always
  re-derived rather than depending on a cached intermediate) and joins their
  union against `known_correct_answered` row_keys the staging pool doesn't
  already cover (`setdefault` -- never overrides staging-pool-sourced text).
  Hard-fail discipline unchanged. Re-ran once:

  ```
  [materialize] WROTE analysis/rows_with_text.jsonl (1768 rows);
  missing_question=0 missing_by_role={}
  ```

  Final materialized counts, all with non-empty question text: confab
  **309/309**, known_correct_answered **430/430** (89 from the staging pool
  + 341 newly recovered), unknown_refused **1029/1029**. Total 1768/1768,
  zero missing. This cell is no longer blocked on question text for any
  role; the capture-input pipeline is complete pending sign + launch.

- 2026-07-21 (pre-sign, persistence declarations + materialization script):
  Two final pre-sign tasks per the lead.

  TASK 1 -- `instrument.persistence` filled in `experiment.yaml` for all
  four modules, mirroring `gemma-4-e4b-family-atlas`'s pattern:
  - `render_qwen3_atlas.py` (short-run): measured directly, tokenizer load
    + 20 `render()` calls against the real pinned tokenizer, CPU-only,
    synthetic placeholder questions: **6.525s** total.
  - `capture_family_atlas_cell.py` (incremental): NOT re-timed (this is the
    GPU capture stage itself, gated behind sign+launch). Verified the
    checkpoint mechanism directly rather than trusting the gemma citation:
    initialized the `synaptic-tuner` submodule read-only in this worktree
    and confirmed `synaptic-tuner/tuner/batch/persistence.py` defines
    `CHECKPOINT_FILENAME = "checkpoint.json"` plus `_fsync_file`/`_fsync_dir`
    helpers; `cmd_capture` shells out to `tuner.py batch-capture --resume`
    (hf-batched engine), which fsyncs `checkpoint.json` into this cell's own
    `--out-dir` (`analysis/qwen3_4b_raw_base/atlas_capture/`) after each row.
  - `profile_and_read_family_atlas_panel.py` (short-run): measured at this
    cell's ACTUAL pool scale, not the tiny `smoke_family_atlas.py` fixture
    (114 rows / 4 hidden states / hidden_dim=256). Used a scratchpad probe
    (`.../scratchpad/time_profile_panel_realistic_scale_qwen3.py`, adapted
    from gemma's own realistic-scale probe at the same scratchpad path):
    1768 synthetic rows at the cell's real role/split counts (known_correct
    fit 172 / held_out 258, confab fit 124 / held_out 185, unknown_refused
    fit_only 1029), 37 hidden states, hidden_dim=2560, 2000 bootstrap
    resamples. Build 2.57s + score 68.70s = **71.27s** total.
  - `derive_unknown_refused_manifest.py` (short-run): already executed
    one-shot pre-sign (see prior entry); re-run for a clean timing sample,
    **1.196s**, output sha256 unchanged (`71c78f9a...`), confirming
    determinism.
  - All four measurements are well under the 15-minute short-run ceiling;
    nothing flagged to the lead on that front.

  TASK 2 -- `materialize_rows.py` written, mirroring
  `experiments/doubt-gated-caution-tighten/materialize_rows.py`'s
  containment scheme exactly, extended to also materialize the
  `unknown_refused` role (joined against the cached `ak_stage1_pool.jsonl`,
  which carries `question` directly for all 1,029 of this cell's
  unknown_refused row_keys). Ran it once against the real committed
  manifests (`split_manifest.json` + this cell's own
  `unknown_refused_manifest.json`), 1768 rows total. Output:
  `experiments/qwen3-4b-family-atlas/analysis/rows_with_text.jsonl`
  (gitignored; verified `git check-ignore` covers it).

  **Finding, NOT resolved -- flagged to the lead**: `confab` (309/309) and
  `unknown_refused` (1029/1029) resolve fully to question text. But of the
  430 `known_correct_answered` row_keys, only 89 resolve (the original
  AH-A0 pool, staged as `a0_pool_v21_questions.jsonl`). The other **341**
  row_keys were added to the promoted split manifest by
  `doubt-gated-caution-tighten/mine_known_correct.py`, whose question text
  was never re-staged to HF and whose only other copy
  (`doubt-gated-caution-tighten/analysis/mined_a0_known_correct_rows.jsonl`)
  does not exist anywhere on this machine (searched
  `/home/profsynapse` to depth 8, zero hits). Recovering that text requires
  re-running `mine_known_correct.py`, which loads `unsloth/Qwen3-4B` in
  bf16 and GENERATES against
  `archive/experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl`
  -- a live GPU model-generation pass, out of scope for this pre-sign task
  (no capture, no GPU launch). `materialize_rows.py` checks for that local
  cache as a fallback (so it will pick the text up automatically once/if
  that cache is produced) but does not regenerate it itself.
  `materialize_rows.py` therefore correctly hard-fails
  (`missing_question=341`, all in `known_correct_answered`, exit 1) on this
  run, mirroring the sibling script's own hard-fail discipline rather than
  silently writing a partial or fabricated pool. This blocks a capture
  launch for the `known_correct_answered` role until either (a) someone
  runs `mine_known_correct.py`'s generation pass and the resulting cache is
  present locally, or (b) the lead decides on an alternate resolution.

- 2026-07-21 (blocker close + pin re-verification + import smoke):
  Follow-up to the lead's three requests after reviewing the scaffold and
  authoring Prediction/Falsifier/container ruling (commit 1a3a3326). Still
  NO sign, NO launch, NO weight downloads.

  1. **unknown_refused row-key derivation (blocker CLOSED).** Wrote
     `derive_unknown_refused_manifest.py` (this directory). Found the
     private source pool (`professorsynapse/eh-al-prep-staging:pools/ak_stage1_pool.jsonl`)
     already present in the local HF cache under two different snapshot
     commit dirs (`7e1376f...` and, after a fresh `hf_hub_download` call
     with no pinned revision, `da4b84e...`) -- both byte-identical, sha256
     `48654798d5e94edfbf4abb550ed053f863369e14c05be0187fd8ab192befaa9d`, so
     no drift risk from the unpinned `main` ref of that staging repo as of
     this run. Ran the script (fetch via `hf_hub_download`, no
     `local_files_only`, resolved from cache without a fresh network
     download since the local blob already matched):
     - Source pool: 1338 total rows.
     - Filter rule (`extract_l34_anchor.py:99`,
       `not r["confab_on_unanswerable"]`) applied: **1029** unknown_refused
       rows, all unique row_keys. Matches the promoted manifest's own
       `n_unknown_refused_fit_only: 1029` exactly.
     - Cross-check: the SAME pool's `confab_on_unanswerable == True` subset
       (309 rows) is byte-identical AS A SET to the 309 confab row_keys
       already committed in
       `experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`.
       This is the load-bearing check -- it proves the fetched pool is the
       exact source `doubt-gated-caution-tighten` originally extracted
       from, not a same-shaped coincidence.
     - Output: `unknown_refused_manifest.json` (this directory), sha256
       `71c78f9ac4d185bea2c4023778aa7b9bd38060da55eb4b80f190bfbf2e72c891`,
       1029 rows, schema `{row_key, role: "unknown_refused", split:
       "fit_only"}` only -- verified no other keys leaked into any row
       (spot-checked: `{'role', 'row_key', 'split'}` is the complete key
       set across all 1029 rows). Did NOT edit the existing promoted
       manifest at `experiments/common/doubt-gated-caution-tighten-heldout-split/`
       (another cell's committed artifact).
     - `cell.yaml` updated: RESOLVED GAP note replaces the old KNOWN GAP
       note, `source.unknown_refused_manifest_path` added, role_counts/
       role_split_counts caveats removed (now real, verified numbers).
       Explicitly noted what remains NOT done: joining this row-key list
       against question text into a local materialized row-pool JSONL
       (`capture_family_atlas_cell.py`'s actual `--row-pool` input) is a
       separate, later, still sign/launch-gated step -- this entry only
       closes the row-KEY gap, not the full capture-input pipeline.

  2. **Model pin second source (VERIFIED, no drift).** Live HF Hub metadata
     check (no weight download): `HfApi().list_repo_refs("unsloth/Qwen3-4B")`
     -> single branch `main` -> target_commit
     `64033659d5caf1b8ed7f929b29de705e93a4d468`. `HfApi().model_info(...)`
     at both the pinned revision and with no revision arg (i.e. `main`)
     both resolve to the same sha, `lastModified` 2025-05-13T19:32:35Z.
     Checked 2026-07-21T02:36:48Z. **main head == pinned revision: True.**
     No drift since the `h6-genstream-hook-firing-check` NOTEBOOK.md
     citation (which itself dated the same 2025-05-13 unchanged-since
     claim); this is now a second, independent, live-verified source for
     the same pin.

  3. **CPU import-smoke (PASSED).** `python -c` import of
     `render_qwen3_atlas.py`, `capture_family_atlas_cell.py`, and
     `profile_and_read_family_atlas_panel.py` each individually via
     `importlib.util.spec_from_file_location` from the experiment
     directory: all three imported cleanly, no exceptions.
     `capture_family_atlas_cell.py`'s own `ROOT`/`REPO_ROOT` module
     constants resolve correctly at this cell's actual
     `experiments/<slug>/` depth (`REPO_ROOT` == the worktree root,
     confirmed by checking `.git` and `experiments/` both exist under it) --
     no repeat of the path-resolution gap `gemma-4-e4b-family-atlas`
     flagged for itself.

  Post-edit `bin/exp validate`: OK (87 experiments), same three
  no-persistence-declaration warnings on this cell's modules as before
  (resolved at sign time, unchanged by this entry).

  **Noticed, not fixed** (out of scope for this task, flagging for the
  lead): `AMENDMENT.md` now has two "## Predictions scoreboard" sections --
  the lead's authored one (with real orchestrator/user rows) right after
  "## Falsifier", and the original empty scaffold one (still `| | |`) left
  in place further down before "## Outcome". Looks like a leftover from
  the lead's edit rather than an intentional duplicate; did not touch it
  since it's inside prose the lead authored and outside this task's scope.

- 2026-07-21 (scaffold): `bin/exp new` scaffolded this experiment (type
  probe-fit, status draft). Filled `cell.yaml`, `gates.yaml`,
  `render_qwen3_atlas.py` (ported from
  `experiments/common/renders/ah_a0_raw_base_render.py`), and byte-identical
  copies of the shared `capture_family_atlas_cell.py` /
  `profile_and_read_family_atlas_panel.py` (sha256-verified against
  `.skills/family-atlas/scripts/`). `AMENDMENT.md` Prediction/Falsifier left
  as TODO-LEAD placeholders per the orchestrator's instruction; not signed.
  Not launched: no GPU work, no mining, no model downloads.
  Precondition inventory findings (full detail in `AMENDMENT.md` "Design"
  and `cell.yaml` comments):
  - Model pin: `unsloth/Qwen3-4B` @
    `64033659d5caf1b8ed7f929b29de705e93a4d468`, sourced from
    `experiments/h6-genstream-hook-firing-check/NOTEBOOK.md` (only recorded
    revision hash for this repo id anywhere in the codebase; corroborated
    stable on the Hub as of that entry). Distinct from the unrelated
    `Qwen/Qwen3-4B` official pin used by
    `experiments/aq-sycophancy-activation-actuator`.
  - Architecture: num_hidden_layers=36, hidden_size=2560, n_hidden_states=37
    (cross-checked against committed direction-vector JSONs and the
    hs_index/decoder_block_index pairing already committed elsewhere in the
    program for this substrate).
  - Row pool: a vetted, committed split manifest already exists
    (`experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`,
    promoted from `doubt-gated-caution-tighten`), clearing this program's
    standard held-out floors (confab held-out 185 >= 150; known_correct
    held-out 258 >= 250) for the two roles it carries row-level IDs for.
    NOT a fresh-mining cell; no AG0a gate added.
  - BLOCKER before sign: that manifest's `unknown_refused` role (1029 rows)
    is a count field only, no row-key list. The list exists only in a
    gitignored, no-longer-present local file. Needs a cheap CPU-only
    promotion step (deterministic re-derivation from the private AK
    Stage-1 pool, per `extract_l34_anchor.py:99`'s filter) before capture
    can run AG2's read panel (unknown_refused is the doubt axis's negative
    pole, the caution axis's positive pole, and the raw_refusal axis's
    positive pole).
  - Open question for the lead: whether the standing local-GPU pinned-
    container directive applies to this cell's bespoke capture script (see
    AMENDMENT.md "Design", "Execution" paragraph); not resolved here.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 1 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 5 files / ~0.35 MB, built at repo commit b642b7c6.

- HF repo: `professorsynapse/eh-qwen3-4b-family-atlas` (dataset)
- HF revision: `114816c1ff18914abeca0522c3b79c4ae4905b23`
