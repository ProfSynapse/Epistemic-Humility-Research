# Hidden-State Probe — Smoke Recipe

The end-to-end smoke for the off-matrix hidden-state extraction capability
(feature #40). It exercises the runner-side gate, the `aligned_run_record_id`
resolver, the GPU-free prepare step, and (on a GPU host) one real extraction whose
delta tensors are eyeballed nonzero. This is the F1-confound guard (issue #30):
a `delta = h_lora - h_base` that is all-zero means the adapter never engaged.

> **GPU boundary (architecture §10).** Steps 1–4 are GPU-FREE and CI-testable.
> Step 5 (`--run-extraction`) is GPU-REQUIRED and deferred until a GPU frees;
> the cloud lane is additionally cost-incurring and needs explicit user approval.

## The chain

| # | Step | Lane | GPU? |
|---|------|------|------|
| 0 | Fetch the frozen split + the probe tier inputs (WS-0). | local | no |
| 1 | Produce a minimal `probe_results.jsonl` for the model_tag — a SUBSAMPLED WS-1 run with at least 16 known + 16 unknown rows (matches `selection.n_known` / `n_unknown`). | local | yes (probe tier) |
| 2 | Resolve `aligned_run_record_id` from the active arm's adapter (runner-side, fail-closed). | local | no |
| 3 | Run the GPU-free prepare/gate: `prepare_extraction_cell.py` (default, no `--run-extraction`). | local | no |
| 4 | Inspect the PASS/SKIP report + the temp effective config. | local | no |
| 5 | Run the extraction (`--run-extraction`) and eyeball the delta tensors nonzero. | local | **yes** |

## Step 0–1 — inputs (probe tier)

The extraction reads three things the probe tier produces:
`questions_frozen.json` (the frozen known/unknown keys), `probe_results.jsonl`
(the ~123MB streamed alignment source, **gitignored**), and the trained contrast
adapter (`final_model/` with `adapter_config.json`). For a smoke, subsample WS-1
so `probe_results.jsonl` holds at least the 16+16 rows the slice selects — a full
probe run is unnecessary to validate the pipeline.

## Step 2–4 — GPU-free gate + resolve (the CI path)

```bash
# Default path: gate (E1..E4) + resolve aligned_run_record_id + report. Launches
# nothing. Exit 0 on PASS *and* on SKIP (a SKIP is an exploratory degrade, not an
# error — e.g. probe_results.jsonl absent, or the run-record link unresolvable).
python3 .agents/skills/experiment-runner/scripts/prepare_extraction_cell.py \
    --config experiment/phase1/probe/config/hidden_state_probe.yaml
```

The report is JSON. On `"status": "PASS"` it carries `resolved_run_record_ids` and
the path to a TEMP `effective_config` with `manifest_provenance.aligned_run_record_id`
filled — the committed YAML is NEVER mutated (link-never-mutate, §5.5). On
`"status": "SKIP"` it carries `skip_reason`; the gate checks in order:

- **E1** `probe_results.jsonl` present for the model_tag;
- **E2** its first-row `probe_config_sha` matches `selection.expected_probe_config_sha`
  (null ⇒ presence-only + WARN);
- **E3** `aligned_run_record_id` resolvable — the resolver reverse-looks-up the
  active arm's adapter against `run_records/<id>.json`, FAIL-CLOSED on
  zero-match / ambiguous / unverified (the sft/dpo/kto divergence, §5.4);
- **E4** the adapter dir carries `adapter_config.json`.

A null `model.revision` is a WARN (not a SKIP) locally — the post-load snapshot SHA
still pins identity for an exploratory run, but pin it before a reproducible run.

The unverified escape hatch (e.g. the dpo arm whose run record is `verified=False`):

```bash
python3 .agents/skills/experiment-runner/scripts/prepare_extraction_cell.py \
    --config experiment/phase1/probe/config/hidden_state_probe.yaml \
    --allow-unverified        # opt-in; default is fail-closed
```

## Step 5 — the real extraction (GPU)

```bash
# GPU-REQUIRED. After the gate PASSes, shells out to the merged harness with the
# temp effective config. On a SKIP the harness is NOT invoked (exit 0).
python3 .agents/skills/experiment-runner/scripts/prepare_extraction_cell.py \
    --config experiment/phase1/probe/config/hidden_state_probe.yaml \
    --run-extraction
```

Eyeball the delta tensors nonzero (the issue-#30 confound guard) under
`experiment/phase1/probe/<model_tag>/hidden_states/extraction__<sha>/`:

```python
from safetensors import safe_open
with safe_open("delta.safetensors", framework="pt") as f:
    t = f.get_tensor(f.keys()[0])
    assert float(t.abs().sum()) > 0, "delta all-zero — adapter never engaged (F1 confound)"
```

## Skill-tree sync invariant (do NOT edit a mirror)

All of these scripts are authored ONCE in the canonical `.skills/experiment-runner/`
tree and propagated to the `.claude/` and `.agents/` mirrors:

```bash
python3 sync_skills.py --write      # canonical -> both mirrors (LF-normalized)
python3 sync_skills.py --check      # drift-check (sha256 on CRLF-normalized
                                    # content — NEVER the rtk-proxied diff, which
                                    # lies with a false "[ok] identical" banner)
```

`sync_skills.py --check` is the CI gate (`tests/test_skills_sync.py`). Never
hand-edit a mirror — edit `.skills/` and re-run `--write`.
