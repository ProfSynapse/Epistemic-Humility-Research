# Phase 1 run records

One JSON run record per launched matrix cell, written here by the experiment
runner (`.claude/skills/experiment-runner/scripts/run_matrix.py`) BEFORE the
tuner is invoked. These are committed repo content — the provenance spine for
the released Phase 1 artifacts (HANDOFF.md §5 SACROSANCT).

Each record ties a result back to the exact recipe, seed/override, training
bytes (`data_sha256`), and BOTH commit SHAs (research repo + `synaptic-tuner`
submodule), so every run is deterministic and re-runnable. Schema and discipline:
[../../../.claude/skills/experiment-runner/reference/run-records.md](../../../.claude/skills/experiment-runner/reference/run-records.md).

Records are named `<run_id>.json`, where the run id is the cell coordinate
(`<arm>__<size>__<cell_type>[__<override>]__seed<n>`).
