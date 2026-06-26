# Row Selection

Load this when choosing which rows feed an extraction, diagnostic, replay, or
behavior panel, and for per-row logit-target wiring.

Use fixed row keys for causal replay claims:

```yaml
runner_overrides:
  selection:
    row_keys:
      - selfaware::selfaware::000002::selfaware-3
```

For changed-row or behavior-conditioned claims, balanced `max_rows` is not
enough. Use exact `selection.row_keys` or `selection.row_keys_by_candidate` and
record how rows were chosen.

For reusable fixed panels, put row keys in a text file and reference it:

```yaml
runner_overrides:
  selection:
    probe_results: null
    row_keys_file: experiment/phase1/probe/config/example_fixed_row_keys.txt
```

Use one row key per line. Blank lines and `#` comments are allowed. Keep these
files small, named by the panel purpose, and checked in only when they contain
non-restricted row identifiers.

## Behavior-cell replay panels

For behavior-cell replay panels from an existing behavior-labeled rows file,
use the checked-in builder instead of copying row keys from terminal output:

```bash
python experiment/phase1/probe/phase3_behavior_panel_row_keys.py \
  --config experiment/phase1/probe/config/example_behavior_panel_row_keys.yaml
```

The builder selects deterministic row-key quotas by `behavior_cell`, applies
exclude row-key files, and writes selected rows plus a manifest. Use it for
disjoint replay panels such as known-refused / known-correct / unknown-refused
stress tests.

Do not infer rare-cell availability from the current extracted overlay alone.
Full evals can contain enough rare failures even when a prior hidden-state
extraction slice does not. For SelfAware full-eval rare-cell panels, first build
a focused extraction-ready manifest from scored rows:

```bash
python experiment/phase1/probe/phase3_selfaware_behavior_manifest.py \
  --config experiment/phase1/probe/config/example_selfaware_behavior_manifest.yaml
```

Then point a `selection.source: selfaware_manifest` hidden-state extraction at
the generated manifest. Keep quotas explicit and `require_quotas: true` for
balanced axes so sparse rare-cell panels fail closed instead of silently
becoming one-sided.

## Exact probe-pool row-key files

Hidden-state extraction also supports exact probe-pool row-key files:

```yaml
selection:
  source: probe_pool
  questions_frozen: ../data/qwen3-4b-instruct/questions_frozen.json
  probe_results: qwen3-4b-instruct/probe_results.jsonl
  row_keys_file: config/example_fixed_row_keys.txt
```

The extraction selector validates every key against the frozen known/unknown
pools, rejects duplicates and discard/out-of-frozen keys, and preserves file
order. Use this for rare-cell-enriched panels instead of increasing random
`n_known`/`n_unknown` slices blindly.

## Per-row logit targets

For per-row logit targets, prefer structured row fields over copied strings:

```yaml
logit_targets:
  groups:
    - name: wrong_hint_answer
      source: row_field
      field_path: sycophancy.incorrect_answer
      include_leading_space_variants: true
      include_multi_token_first_token: false
```

This requires the extraction rows to preserve the nested metadata field. Verify
`rows.jsonl` before launching live diagnostics.

For row-alias logit targets, verify the live runner actually receives aliases.
Legacy probe result files usually expose `normalized_aliases`; current behavior
row overlays expose `aliases`. The causal-pilot runner supports both, but only
when `selection.probe_results` points at a row source that contains one of
those fields. If answer-alias metrics are absent from `logit_diagnostics.jsonl`,
do not interpret the run as answer-channel evidence; fix alias loading and rerun.
