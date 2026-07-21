# Qwen3-4B family atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
