# Standard Sweep Workflow

Load this when planning, executing, aggregating, or observing a causal-pilot
sweep, and for runtime-identity / adapter-fallback semantics.

## Plan / materialize / execute

Plan/materialize before live execution:

```bash
python experiments/common/mechinterp/causal_pilot_sweep.py \
  --config archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs
```

Only after approval, execute:

```bash
python experiments/common/mechinterp/causal_pilot_sweep.py \
  --config archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic
```

Aggregate completed runs:

```bash
python experiments/common/mechinterp/causal_pilot_aggregate.py \
  --root experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep \
  --out experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
```

Use aggregate output as an index. Inspect `run_manifest.json`, per-row JSONL,
and source configs before interpreting surprising effects.

Aggregation collects every completed run under the root. If a candidate was
rerun after a failed or partial attempt, filter to the latest successful
`run_manifest.json` per candidate/mode before reporting metrics.

## Live execution observability

Sweep execution logs are under:

- `OUTPUT_ROOT/_execution_logs/*.stdout.log`
- `OUTPUT_ROOT/_execution_logs/*.stderr.log`
- `OUTPUT_ROOT/_execution_logs/execution_results.jsonl`

`execution_results.jsonl` is append-only. If a failed Docker attempt is rerun,
group by candidate/mode and use the latest successful event while preserving
failed events as retry provenance.

Docker materialized runner configs must contain container-readable paths. A path
like `/workspace/repo/F:\Code\...` is unsafe; stop and replan.

## Runtime semantics

For live `experiments/common/mechinterp/causal_pilot_runner.py` diagnostics, runtime identity is
controlled by `runtime_model`, not descriptive `model` metadata. If
`runtime_model.adapter_path` is null, the runner falls back to the candidate
extraction manifest adapter by default. That is an arm-native panel.

For same-runtime adapterless SFT panels, disable extraction-adapter fallback:

```yaml
runner_overrides:
  runtime_model:
    model_name: /workspace/repo/path/to/sft/merged-16bit
    adapter_path: null
    use_extraction_adapter: false
    allow_adapterless: true
```

Use `runner_overrides` for reusable sweep-level changes such as exact row
slices, runtime pins, logit target groups, and control settings.
