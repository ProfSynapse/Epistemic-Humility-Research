# dark-actuator-screen notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-06 -- CPU build: launch wrapper, render plug-in, staged rows_pool.jsonl

Build-only (no GPU, no `exp sign`, no steering arms run). Closes items 1-2 of
the prior entry's "what remains" list.

- **`run_screen.py`** (new): the launch-time wrapper `cell.yaml`/`gates.yaml`
  documented as not-yet-built. For each of the 34 `readouts:` directions it
  deep-copies the base recipe, sets `law.readout` to that direction, prefixes
  every arm name `<direction>__<arm>` (the exact convention `gates.yaml`
  already reads -- cross-checked: every `primary_arm`/`control_arm` in
  `gates.yaml` is produced by the wrapper for its direction, 0 misses), and
  calls the tuner's own `MechInterp.cli.run_steer` once per direction --
  nothing in `synaptic-tuner/` is touched or reimplemented. Resumable at the
  direction level (skips a direction whose shared output already has all 4
  prefixed arms x full pool row count) and at the row level for free (each
  direction's config_sha differs, so the tuner's own smoke gate and
  `execution.resume` logic apply per direction unmodified).
  - **Path-resolution fix found and applied**: `cell.yaml`'s own paths
    (`surface.rows_path`, `execution.output_path`, every `readouts[*].path`)
    are written repo-root-relative, matching every other cell under
    `experiments/`. The tuner resolves those strings via a plain `open()`
    relative to the process's CWD at run time. The mechinterp-cells skill's
    documented workflow (`cd synaptic-tuner && ... --mi-config
    ../experiments/<slug>/cell.yaml`) would silently resolve them against
    `synaptic-tuner/` as CWD and miss every file -- no cell in this repo has
    actually been launched yet, so this had no prior test. `run_screen.py`
    sidesteps it: every per-direction materialized config gets those three
    path families rewritten absolute (anchored at this repo's root via
    `__file__`), so the wrapper runs correctly from any CWD.
  - **Model-reload cost, accepted deliberately**: `run_steer` loads the model
    inside every call; there is no supported way to share one loaded model
    across the 34 per-direction calls without editing the tuner, which is out
    of scope. Each direction pays its own model-load cost.
- **`experiments/common/renders/ak_stage1_raw_base_render.py`** (new,
  addition beyond the originally-scoped 3 build tasks -- flagged for lead
  review): the AK Stage-1 raw-base capture
  (`amendment_ak_gentime_positions_extract.py`) deliberately excludes question
  text from `rows.jsonl` ("NO question text -> NO-LICENSE safe"), so the
  staged `rows_pool.jsonl` this screen reads carries no prompt/question field
  at all -- a steer cell cannot render a live prompt from it alone. This
  render function reconstructs the row's original prompt from `row_key` by
  joining against the two AH Stage-0 question pools (`ah_stage0/
  candidates.jsonl` for `ah::` keys, `ah_stage0/expansion/
  expansion_candidates.jsonl` for `ahx::` keys -- both canonical-checkout-only,
  gitignored, never staged into this experiment tree) and re-applying the
  capture manifest's own system prompt + chat template
  (`enable_thinking=False`). Verified byte/token-identical to the original
  capture: retokenizing the reconstructed prompt for all 1,338 raw-base pool
  rows reproduces that row's recorded `prompt_len` exactly (1338/1338 checked,
  1338/1338 match, 0 missing questions).
- **Staged `rows_pool.jsonl`** (gitignored) from
  `$HOME/ak_census_data/ak-stage1-raw-base-r1/data/rows.jsonl` (sha256
  `f4bab74d...` both source and staged copy match; recorded in
  `analysis/prep_manifest.json`'s new `rows_pool` block). Source-tag census:
  `kuq_ku_unknown_x` (751), `kuq_ku_unknown` (455), `selfaware_unanswerable`
  (132) -- no `falseqa`-tagged source present, containment holds. The two AH
  Stage-0 question pools the render function reads are recorded for
  provenance only (`prep_manifest.json`'s new `render_question_pools` block,
  sha256 pinned) -- they are NOT staged into this experiment tree, matching
  the AK capture's own reason for excluding question text.
- **Validated (CPU, no GPU)**: `run_screen.py --dry-run` materializes +
  `load_steer_config`s all 34 per-direction configs successfully (34/34 ok)
  from two different process CWDs; every generated config's `readouts[*].path`
  resolves to a real staged direction file (0 missing) and `rows_path` exists.
  `bin/exp validate` (2 experiments, OK) and `bin/exp regen --check` (registry
  up to date) both pass unchanged. `analysis/_synthetic_gates_check.py`
  re-run: unchanged from the prior entry's validation (mixed pass/fail
  fixture by design; not a real result).
- **What remains before this screen can run on the 3090** (updated): items
  3-5 of the prior entry's list stand (`expected_config_sha` unset until sign;
  a real GPU smoke per direction; user GPU-launch approval). Item 1 (wrapper)
  and item 2 (pool staging) are done as of this entry.

### 2026-07-06 -- CPU build: staged inputs, fit controls, built cell.yaml/gates.yaml

Build-only (no GPU, no `exp sign`, no steering arms run). See AMENDMENT.md
"Build notes" for the authoritative-candidate-copy resolution and the design
decisions summarized below.

- `build_directions.py` staged the 12 authoritative frozen candidates (from
  the `lab-dark-displacement-census` worktree, PR #222, HEAD `787f4b6d`) and
  fit the positive (`refuse`) / negative (`propensity`) controls per layer plus
  12 seeded random-direction controls, into the gitignored
  `directions/` dir. `analysis/prep_manifest.json` (gitignored) records every
  source path + sha256.
- `cell.yaml` declares all 34 directions in `readouts:`; `law.readout`
  defaults to `L34_succ_pc0` for standalone parseability. `gates.yaml` has 3
  G-instrument gates (positive control moves; propensity + one representative
  random control sit at the floor) + 12 G-screen gates (one per candidate,
  `kill_diff_vs_control` at dose3 vs its paired random control, CI-excludes-
  zero graduation bar).
- **What remains before this screen can run on the 3090**:
  1. A launch-time wrapper that, per direction, copies `cell.yaml`, overrides
     `law.readout` and prefixes `arms[*].name` with the direction name, and
     appends into the ONE shared `execution.output_path` (resume=true) so
     `gates.yaml`'s cross-arm comparisons see every direction's rows in one
     file. Not built -- this build task's scope was configs + staging only.
  2. Stage `rows_pool.jsonl` at `analysis/rows_pool.jsonl` (gitignored) from
     `$HOME/ak_census_data/ak-stage1-raw-base-r1/data/rows.jsonl` (or point
     `surface.rows_path` / `DARK_ACTUATOR_ROWS_POOL` directly at it) before any
     real run -- not staged into the repo tree, only referenced by absolute
     path today.
  3. `expected_config_sha` is unset (draft; fill at `exp sign`, after the
     wrapper's override behavior is final -- the sha must be pinned to
     whatever `cell.yaml` shape the wrapper actually launches).
  4. A real smoke run per direction on the 3090 (gen_stream decode-hook-firing
     guard, pinned tuner `294a653`) before any full-arm dose ladder.
  5. User GPU-launch approval, naming cells/lane, per project delegation
     norms -- not requested or granted by this build task.
