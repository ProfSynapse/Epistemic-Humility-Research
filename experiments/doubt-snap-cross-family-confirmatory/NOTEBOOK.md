# doubt-snap-cross-family-confirmatory notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-08 08:15 EDT: Refreshed the pinned hash for
  `cloud/modal_doubt_snap_cross_family.py` after Qwen3.5 4B exposed a Modal
  preemption edge case. The interrupted worker had generated partial baseline
  rows, but those rows lived only on scratch and were not visible to the
  replacement worker, so tuner `--resume` restarted at zero. The wrapper now
  symlinks each cell's `analysis/<cell_id>` and `analysis-committed/<cell_id>`
  directories onto the Modal volume before GPU work starts and periodically
  commits the volume during long tuner subprocesses. This is an operational
  durability fix only; it does not change model selection, rows, generation
  settings, steering configs, gates, scoring, or dose selection.

- 2026-07-08 07:24 EDT: Refreshed the pinned hash for
  `cloud/modal_doubt_snap_cross_family.py` after a wrapper-only artifact
  preservation fix. The change separates Modal volume copy targets for
  `analysis-committed/` and private `analysis/`; it does not change model
  selection, rows, generation settings, steering configs, gates, scoring, or dose
  selection. This keeps the run inspectable when a cell stops at FIT dose
  selection while preserving the signed scientific instrument.

- (add dated entries as the experiment progresses)
