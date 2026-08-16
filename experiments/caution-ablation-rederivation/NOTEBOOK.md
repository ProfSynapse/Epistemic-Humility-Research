# Re-deriving the archived caution-ablation over-refusal collapse (0.994 to 0.030) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-08-15 — lead prep and sign

Pre-sign verification: both direction-vector shas recomputed on disk and
match the amendment pins exactly; all three archived configs exist and were
copied byte-identical into configs/ (shas match the archive originals); the
checkpoint adapter (20260624_095831/final_model) and its seed-1 merged base
(20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit) are both on disk; live
drivers located (residual_intervention_runner.py via the legacy wrapper,
causal_pilot_sweep.py for the coeff sweep); the coeff sweep's three
archive-referenced dependency configs and row-keys file all exist.

Known instrument-environment fact, recorded before launch: the archived
configs reference inputs and output roots under
experiment/phase1/probe/analysis/, which is now an EMPTY stub dir (inputs
moved to archive/experiment/phase1-data/probe/analysis/ at archival).
Resolution pre-declared in cell.yaml: symlink the two input names into the
stub dir pointing at their archived homes, and symlink the declared output
roots into this cell's gitignored analysis/ dir. Config bytes untouched
per CA-G0; the shims are mount-level environment, not instrument edits.

Signed via bin/exp sign: 5 files pinned (cell.yaml, gates.yaml, three
archived configs). Engine exception parity-locked recorded in the manifest
with reason. Launch authorized by the PI 2026-08-15; run delegated next
with a lead-owned watcher armed in the launch turn.
