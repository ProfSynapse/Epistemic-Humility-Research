# Modal launch plan

This directory is for the crash-resumable Modal wrapper and launch manifest.

Planned execution shape:

1. One detached Modal function per `model_matrix.yaml` cell.
2. Each function runs the full cell pipeline: mine baseline roles, extract the
   registered layer activations, fit directions on FIT, fit tau on FIT, choose
   dose on FIT, run G0, then score held-out G1/G2/G3.
3. Inside each function, generation and extraction are batched. Intervention
   generation is grouped by `(arm, direction, fire_state, dose)` so rows with
   the same hook configuration decode in one batch.
4. Private row text, aliases, and generations stay in HF/private Modal artifacts
   or local gitignored `analysis/`. Public committed outputs are ID manifests,
   direction vectors, fit summaries, gate summaries, and aggregate result JSON.

Exact Modal launches require explicit user approval naming the cells and lane.
