# Modal Launch Plan

This directory is for the crash-resumable Modal fan-out wrapper. It does not
own model loading or hidden-state capture; those live in
`capture_atlas_cell.py` (GPU) and the pinned Synaptic-Tuner submodule
(`batch-capture`). Scoring (`profile_and_read_panel.py`) is CPU-only and runs
in the same wrapper invocation right after capture, on the same worker.

READ-ONLY mapping instrument: no steering, no interventions, no writes to
activations. This wrapper never calls `mechinterp steer` or `mechinterp run`.

Planned execution shape:

1. One detached Modal function per cell (`llama32_3b_instruct`,
   `mistral7b_instruct_v03`).
2. The fleet's `eh-doubt-snap-cross-family` volume is mounted for read-only
   input: this wrapper reads `split_rows_private.jsonl` for the requested
   cell and never writes to that volume.
3. This experiment's own `eh-jspace-family-atlas` volume holds `analysis/`
   and `analysis-committed/` for each cell, symlinked onto the volume before
   GPU work starts (same preemption-safety pattern as
   `doubt-snap-cross-family-confirmatory/cloud/modal_doubt_snap_cross_family
   .py`), so `batch-capture --resume` survives a preempted worker.
4. `capture_atlas_cell.py capture` runs the full-depth anchor capture via
   Synaptic-Tuner's `batch-capture --layers all`, then
   `profile_and_read_panel.py score` runs the CPU-only eff_dim_frac profile
   and read panel over the fresh captures.
5. Public committed outputs are `split_manifest.json`, `capture_manifest
   .json`, and `atlas_summary.json` per cell -- aggregates and fitted
   metadata only, never row text, aliases, or token IDs.

Estimated spend is capture (one forward pass per row, no generation) plus CPU
scoring only -- see NOTEBOOK.md for the row-count-derived cost estimate.
Exact launch requires fresh user approval with that estimate restated at
staging time; nothing in this repo spawns a Modal function without
`EHR_LAUNCH_OK`, `MODAL_COST_CAP_USD`, and `EHR_REPO_COMMIT` all set
explicitly.

## Batch sizing

Unlike the fleet's baseline generation, this wrapper never decodes
autoregressively, so the fleet's batch-1 generation-parity constraint
(`doubt-snap-cross-family-confirmatory/cloud/README.md`) does not apply here:
capture is a single deterministic forward pass per row, and tiny
batch-dependent floating-point differences in that forward pass are far
below the precision this atlas's aggregates (eff_dim_frac, AUROC) need.
Start from `--batch-size 8` (the fleet's own `capture_anchor()` default
convention) and reduce on CUDA OOM; there is no registered batch-parity smoke
gate for this capture-only path.
