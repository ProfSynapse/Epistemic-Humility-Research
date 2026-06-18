# Phase 3 Causal-Pilot Sweeps

Use this reference for local exploratory mechanism sweeps around
`experiment/phase1/probe/phase3_causal_pilot_runner.py`.

## Scope

- Treat every output as Tier 2 exploratory local mechanism evidence.
- Do not promote results into Phase 1 headline evidence or protocol claims.
- Do not edit `synaptic-tuner/`.
- Do not run Docker/GPU unless the user explicitly approves the live run.
- Prefer `phase3_causal_pilot_sweep.py` over ad hoc terminal loops.

## Non-GPU Planning

Plan the current sweep:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml
```

Write the plan and materialized per-candidate runner configs without execution:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --write-plan --materialize-configs
```

For logit diagnostics only, filter before planning/materialization:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic --write-plan --materialize-configs
```

The sweep config reads candidate directions from
`experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml` and
uses the generation-enabled runner config as a template. This keeps the full
candidate set reusable while preserving the live runner's explicit gates. The
checked-in local sweep plans Docker commands for live GPU execution, not host
Python commands. The adapterless base-original candidate is inventoried but
skipped by default until the live runner supports base execution without a LoRA
adapter.

## Live Execution

Only after explicit user approval, execute with the mode-specific gates:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic --allow-generation
```

The wrapper passes `--allow-logit-diagnostic` and `--allow-generation` to the
underlying runner only when executing jobs. The runner still owns model loading,
hooks, output manifests, and fail-closed control validation. Planned commands
should use `docker run --rm --gpus all --ipc=host --entrypoint python`, mount
the repo at `/workspace/repo`, set narrow HF cache env vars, and pass
`/workspace/repo/...` paths to the runner and materialized configs. Keep jobs
serial unless the user explicitly approves a GPU-capacity experiment.

Execution writes per-job observability under `OUTPUT_ROOT/_execution_logs/`:

- `*.stdout.log`
- `*.stderr.log`
- `execution_results.jsonl`

If a sweep fails or is interrupted, inspect these files before rerunning. Docker
materialized YAML must use container-readable `/workspace/repo/...` paths for
runner-consumed paths such as `output.root`, direction artifacts, extraction
manifests, and `selection.probe_results`; a mixed path like
`/workspace/repo/F:\Code\...` means the run should be stopped and the sweep
wrapper/path rewriting fixed.

## Aggregation

Aggregate completed run manifests offline:

```bash
python experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  --root experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep \
  --out experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
```

Use the aggregate as a run index and sanity surface. Interpret from the original
`run_manifest.json`, `metrics.json`, `logit_metrics.json`, `generations.jsonl`,
or `logit_diagnostics.jsonl` when a row looks surprising.

The aggregator maps Docker manifest output paths rooted at `/workspace/repo/...`
back to the host checkout, so host-side aggregation should work after Docker
runs without manually editing manifests.

## Controls

Live controls are intentionally narrower than readiness-plan controls. The
current executable controls are:

- `no_vector_baseline`
- `activation_addition`
- `activation_subtraction`

Do not add readiness-only controls such as random direction, shuffled labels,
wrong-layer neighbors, or sign flips to the live sweep until the runner
implements and tests their exact semantics.
