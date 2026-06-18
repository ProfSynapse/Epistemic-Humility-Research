---
name: mech-interp-runner
description: Run, plan, validate, or aggregate Epistemic-Humility local Phase 3 mechanistic-interpretability sweeps, including hidden-state candidate inventories, causal-pilot sweep planning, explicit non-GPU/GPU gates, base-original skip handling, and offline result aggregation. Use when working on local mech-interp sweeps, causal-pilot diagnostics, activation-addition/logit-diagnostic runs, or future reruns of the Phase 3 full candidate inventory.
---

# Mech-Interp Runner

Use the checked-in scripts. Do not hand-roll terminal loops.

## Scope

- Treat outputs as Tier 2 exploratory local mechanism evidence.
- Do not edit `synaptic-tuner/`.
- Do not run Docker/GPU unless the user explicitly approves that live run.
- Keep base-original `h_base` adapterless work fail-closed until the live runner
  explicitly supports adapterless base execution.

## Full Sweep Plan

Plan the reusable full local sweep without model loading:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml
```

The sweep config points at:

- `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml`
- `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`

Expected current shape: 9 inventory candidates, 8 executable candidates, 1
skipped base-original candidate, and 16 executable jobs across generation and
logit-diagnostic modes. The checked-in local sweep uses Docker command planning
for live GPU execution.

## Materialize Without Running

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --write-plan --materialize-configs
```

This writes a plan plus per-candidate runner configs only. It does not execute
generation or logit diagnostics. Planned live commands should start with
`docker run --rm --gpus all --ipc=host --entrypoint python`, mount the repo to
`/workspace/repo`, and use `/workspace/repo/...` paths for the runner and
materialized configs.

For a logit-only sweep from the full config, filter before planning:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic --write-plan --materialize-configs
```

## Live Execution Gate

Only after explicit user approval:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic
```

The wrapper still relies on `phase3_causal_pilot_runner.py` for live model
loading, hooks, output manifests, and fail-closed control validation. Execution
is serial by default; do not parallelize GPU jobs unless the user explicitly
asks for a capacity experiment.

Live execution observability is under the sweep output root:

- `OUTPUT_ROOT/_execution_logs/*.stdout.log`
- `OUTPUT_ROOT/_execution_logs/*.stderr.log`
- `OUTPUT_ROOT/_execution_logs/execution_results.jsonl`

The wrapper appends one execution-results row after each job finishes. If a
Docker sweep is interrupted or a job fails, inspect this JSONL plus the per-job
logs before deciding what to rerun; do not rely only on `sweep_manifest.json` or
`planned_commands.jsonl`.

Docker materialized runner configs must contain container-readable paths. The
sweep wrapper rewrites obvious runner config paths such as `output.root`,
`selection.probe_results`, `runtime_model.adapter_path`, and candidate direction
artifact paths to `/workspace/repo/...` when `execution.backend: docker`. A mixed
path like `/workspace/repo/F:\Code\...` means the materialized YAML is unsafe to
run and the sweep should be stopped and replanned.

## Aggregate Completed Runs

```bash
python experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  --root experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep \
  --out experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
```

Use aggregate output as an index. Inspect source manifests and JSONL rows before
interpreting surprising effects.

## Validation

Use focused non-GPU checks:

```bash
python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_sweep.py \
  experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py \
  experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
python -m py_compile experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  experiment/phase1/probe/phase3_causal_pilot_aggregate.py
python sync_skills.py --check
```
