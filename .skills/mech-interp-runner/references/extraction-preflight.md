# Hidden-State Extraction Preflight

Load this before launching a hidden-state extraction.

Run a model-free config preflight from the repo root. Importing
`experiments/common/knowledge_probe/hidden_state_probe.py` directly requires the common phase1 probe directory on `PYTHONPATH`;
otherwise root-level imports can fail with
`ModuleNotFoundError: No module named 'hidden_state_schema'`.

PowerShell pattern:

```powershell
$env:PYTHONPATH='archive/experiment/phase1/probe'
@'
from pathlib import Path
from hidden_state_probe import parse_config, resolve_output_dir, select_matched_slice
for path in [
    Path('archive/experiment/phase1/probe/config/example_hidden_state_config.yaml'),
]:
    cfg, sha = parse_config(path)
    rows = select_matched_slice(cfg)
    out = resolve_output_dir(cfg, sha)
    print(path.name, sha[:16], len(rows), out.as_posix())
'@ | python -
```

This validates YAML shape, arm declarations, selection source, row count, and
deterministic output path without constructing the model backend. It is not a
substitute for the manifest verification gate after live extraction.

## Extraction granularity: residual_stream vs attention_head

`extraction.granularity` selects what each row captures (default
`residual_stream`, the original behavior):

- `residual_stream` — one final-prompt-token vector per layer; `expected_layer_count`
  = N+1 (embeddings + N blocks), each width `hidden_dim`. Validated by
  `validate_hidden_state_shape`.
- `attention_head` — the ITI surface: each attention block's final-token o_proj
  INPUT (the concatenated per-head context), captured via forward hooks on
  `...layers.<i>.self_attn.o_proj`. N blocks (NO embedding layer), each width
  `num_attention_heads * head_dim` (this differs from `hidden_dim` under Qwen3
  GQA — head_dim is read from `config.head_dim`, never `hidden_dim // heads`).
  Validated by `validate_head_state_shape`; reshape per head with
  `reshape_o_proj_input_to_heads`.

For the head path the manifest carries `granularity`, `num_attention_heads`, and
`head_dim` (the finalize gate REQUIRES the two dims non-null when
granularity=attention_head; they stay null for residual). Each `rows.jsonl`
record also self-describes its granularity + head layout, so a downstream
per-head reshape can proceed from the rows alone. Persistence is
granularity-agnostic (both write a `layer_id -> vector` map), so the same
`extraction_dir` layout, resume, and verification gate apply unchanged.
