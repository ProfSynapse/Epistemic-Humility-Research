# Modal Launch Plan

This directory is for the crash-resumable Modal fan-out wrapper. It does not
own model loading, generation, hidden-state capture, or activation hooks.
Those live in the pinned Synaptic-Tuner submodule.

Planned execution shape:

1. One detached Modal function per `model_matrix.yaml` cell.
2. `prep_tuner_cell.py` uses existing tuner batch verbs (`batch-generate` and
   `batch-capture`) plus project scoring code to mine baseline roles, extract
   the registered layer activations, fit directions on FIT, and fit tau on FIT.
3. The wrapper runs a FIT-only `mechinterp steer` dose sweep, then
   `prep_tuner_cell.py select-dose` freezes the lowest viable dose.
4. `materialize_tuner_cells.py` writes restartable `mechinterp steer` configs
   for c-hat and random-direction arms from frozen FIT artifacts.
5. The Modal wrapper runs `python synaptic-tuner/tuner.py mechinterp run` on
   those configs. Intervention generation batches rows through the tuner's
   row-local active masks and strengths.
6. Private row text, aliases, and generations stay in HF/private Modal artifacts
   or local gitignored `analysis/`. Public committed outputs are ID manifests,
   direction vectors, fit summaries, gate summaries, and aggregate result JSON.

The user approved Modal spend for this batch up to $500 on 2026-07-07.

## Batch Sizing

Use the live-volume wrapper path before pushing batch size: each cell's
`analysis/<cell_id>` and `analysis-committed/<cell_id>` directories must be on
the Modal volume so a preempted worker can resume from already persisted rows.

For production runs after the Qwen3.5 parity failure, do not size generation
from VRAM headroom alone. Use batch-1 generation unless that exact model has a
passing registered batch-parity smoke at a larger batch. Since batch-1 generation
underutilizes A100 memory, future batch-1 cells should run on Modal A10G by
default; set `DOUBT_SNAP_MODAL_GPU=A100` only for an explicit exception.

Empirical anchors from 2026-07-08:

- `Qwen/Qwen3.5-4B` baseline generation at batch 80 completed with peak GPU
  memory about 13.8/39.5 GiB, but failed the registered semantic batch-parity
  smoke at batch 8. Relaunched from a clean namespace at batch 1.
- `Qwen/Qwen3.5-9B` baseline generation and anchor capture completed at batch
  48 with capture peak about 22.3/39.5 GiB, but failed the registered semantic
  batch-parity smoke. A diagnostic sweep found batch 1 passed and batch 2 failed,
  so batch 1 is the highest evidenced passing generation batch for this cell.

Generation, capture, and steering can have different memory curves, but the
governing constraint here is semantic batch parity, not memory.
