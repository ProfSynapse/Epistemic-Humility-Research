# dark-actuator-screen notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
