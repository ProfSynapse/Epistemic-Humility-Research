# Modal Launch Plan

This directory is for the crash-resumable Modal fan-out wrapper. It does not
own model loading, generation, hidden-state capture, or activation hooks.
Those live in the pinned Synaptic-Tuner submodule.

Planned execution shape:

1. One detached Modal function per `model_matrix.yaml` cell.
2. Prep stages use existing tuner batch verbs (`batch-generate` and
   `batch-capture`) plus project scoring code to mine baseline roles, extract
   the registered layer activations, fit directions on FIT, fit tau on FIT, and
   choose dose on FIT.
3. `materialize_tuner_cells.py` writes restartable `mechinterp steer` configs
   for c-hat and random-direction arms from frozen FIT artifacts.
4. The Modal wrapper runs `python synaptic-tuner/tuner.py mechinterp run` on
   those configs. Intervention generation batches rows through the tuner's
   row-local active masks and strengths.
5. Private row text, aliases, and generations stay in HF/private Modal artifacts
   or local gitignored `analysis/`. Public committed outputs are ID manifests,
   direction vectors, fit summaries, gate summaries, and aggregate result JSON.

The user approved Modal spend for this batch up to $500 on 2026-07-07.
