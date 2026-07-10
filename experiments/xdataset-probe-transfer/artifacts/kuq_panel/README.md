# KUQ Frozen Panel

Committed input artifacts for Amendment P cross-dataset transfer.

- `gen_rows.jsonl`: deterministic KUQ question rows for the baseline generation pass.
- `manifest.json`: frozen row manifest consumed by hidden-state extraction.
- `panel_meta.json`: source hash, seed, and row-count metadata.

These files were migrated from `archive/experiment/phase1/probe/xdataset/kuq_panel/`.
Downstream generated answers, behavior rows, and hidden-state tensors remain
local scratch under this experiment's `analysis/` directory unless deliberately
promoted.
