# Run records — the provenance spine (HANDOFF.md §5 SACROSANCT)

Every launched cell emits a JSON run record to
`experiment/phase1/run_records/<run_id>.json` (committed repo content) BEFORE the
tuner is invoked, so a crashed run still leaves a record; the record is updated
with the outcome after. The records are the run manifest for the released
artifacts — they tie each result back to the exact recipe, seed/override, the
exact training bytes, and BOTH commit SHAs, so any run is deterministic and
re-runnable.

## Schema

```json
{
  "run_id": "kto__4b__lr_panel__lr3.0__seed1",
  "matrix_version": "phase1-v0.3",
  "coordinate": {"arm": "kto", "size": "4b", "cell_type": "lr_panel",
                 "seed": 1, "override": {"learning_rate": 3.0}},
  "source_recipe": "experiment/phase1/recipes/eh_phase1_qwen3_4b_kto_congruence.yaml",
  "materialized_recipe_sha": "<sha256 of the generated recipe text>",
  "method": "kto",
  "model": "unsloth/Qwen3-4B-Instruct-bnb-4bit",
  "lane": "local",
  "data": {
    "source_data_file": "experiment/phase1/data/qwen3-4b-instruct/kto_congruence_train.jsonl",
    "staged_data_file": "scratch/eh_staging/<run_id>/kto_congruence_train.jsonl",
    "hf_dataset_name": null,
    "hf_dataset_revision": null
  },
  "data_sha256": "<sha256 of the exact training file>",
  "research_repo_commit": "<git rev-parse HEAD of this repo>",
  "submodule_commit": "<git rev-parse HEAD of synaptic-tuner>",
  "prereq_check": {"datasets_present": true, "leakage_guard_passed": true},
  "launched_at": "<iso8601 utc>",
  "tuner_invocation": ["python", "tuner.py", "local-run", "--job-config", "...", "--yes"],
  "outcome": {"status": "launched", "job_handle": null, "adapter_path": null,
              "metrics_path": null, "verified": false}
}
```

## The `data` block (local vs cloud)

- **Local lane:** `source_data_file` -> `staged_data_file` (the tuner-repo-
  relative staged copy), `hf_dataset_name` / `hf_dataset_revision` null.
- **Cloud lane:** `hf_dataset_name` + `hf_dataset_revision` (the hub commit SHA
  pinned by the prereq gate), `staged_data_file` null.

`data_sha256` is the SHA-256 of the exact local training file, so even a cloud
run ties back to the bytes it was published from.

## The `verified` flag

`outcome.verified` follows the paper-1 discipline: set `true` ONLY when the
outcome is checked against its metrics artifact (`metrics_path`, the WS-4 eval
harness output, arch §6.7). Never hand-set it.

## Crash-safe ordering

The record is written with `status: "launched"` (or `"skipped"` for gated cells)
BEFORE the tuner invocation, so a crash mid-run still leaves a record naming the
exact inputs. The outcome is patched to `completed` / `failed` after.
