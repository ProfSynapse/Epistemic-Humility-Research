---
schema_version: research-session/v1
session_id: 20260620T204000Z-thinking-enabled-eval-layer
title: Thinking-Enabled Eval Layer
status: active
created_at: '2026-06-20T20:40:00Z'
updated_at: '2026-06-20T21:00:00Z'
phase: phase1
question: Does enabling Qwen3 thinking change Amendment B stated-confidence epistemic-humility
  behavior relative to the non-thinking seed/model evals?
tags:
- phase1
- eval
- thinking
- stated-confidence
- selfaware
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Phase 1 training-regimen comparisons need a thinking-on eval layer
    before further training decisions.
  changed_by_session: Adds explicit thinking-on eval configs, parser support, Docker
    batch tooling, comparison tooling, and a base-smoke result.
checkpoints:
- id: 001-thinking-smoke-and-batch-launch
  at: '2026-06-20T21:00:00Z'
  kind: result
  title: Thinking-On Eval Smoke Cleared And Full Batch Launched
  summary: 'Added an explicit thinking-on eval path and derived Amendment B SelfAware
    configs. A 192-row base smoke completed with 100% stated-confidence coverage,
    no visible think tags in scored rows, unchanged low refusal rates versus non-thinking,
    slightly lower truthful/correct-on-known, and higher mean stated confidence. The
    full thinking-on eval batch was then launched sequentially in Docker.

    '
  evidence:
  - experiment/phase1/eval/config/eval_amendment_b_stated_confidence_neutral_selfaware_seed1_base_smoke_thinking_local_4b.yaml
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b_thinking_on/base_seed1_smoke__selfaware/metrics.json
  - experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl
  commands:
  - python -m pytest experiment/phase1/eval/tests/test_scorers.py experiment/phase1/eval/tests/test_run_eval_e2e.py
    -q
  - python bin/sync_skills.py --check
  - docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v F:\Code\Epistemic-Humility-Research:/workspace/repo
    -w /workspace/repo unsloth/unsloth:latest experiment/phase1/eval/run_eval.py --config
    experiment/phase1/eval/config/eval_amendment_b_stated_confidence_neutral_selfaware_seed1_base_smoke_thinking_local_4b.yaml
    --live-vllm
  - python experiment/phase1/eval/tools/run_thinking_eval_batch.py --status-path experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl
  decisions:
  - Treat thinking-on as a comparison condition, not a replacement for non-thinking
    measurement.
  - Keep result directories separate with a `_thinking_on` suffix.
  - Do not interpret full results until confidence coverage, retry exhaustion, visible
    think tags, and nearest-control plausibility are checked.
  signals:
    smoke_rows: 192
    smoke_confidence_coverage_pct: 100.0
    smoke_visible_think_tags: 0
    smoke_truthful_pct_thinking: 10.94
    smoke_truthful_pct_nonthinking: 12.5
    smoke_over_refusal_pct_thinking: 1.03
    smoke_over_refusal_pct_nonthinking: 1.03
    smoke_mean_stated_confidence_thinking: 0.942187
    smoke_mean_stated_confidence_nonthinking: 0.899479
- id: 002-seed1-all-arms-complete
  at: '2026-06-20T22:25:00Z'
  kind: result
  title: Seed 1 Thinking-On All-Arms Eval Completed
  summary: 'The full SelfAware Amendment B thinking-on seed 1 all-arms config completed
    in Docker with complete row counts for base, SFT, DPO, and KTO. All four arms
    had no visible think tags in scored rows and high confidence coverage. Compared
    with non-thinking, thinking produced small deltas: base and DPO improved slightly,
    KTO stayed essentially flat, and SFT''s refusal behavior softened slightly without
    changing the core pattern that SFT is the only high-refusal arm.

    '
  evidence:
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b_thinking_on/base_seed1__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b_thinking_on/sft_seed1__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b_thinking_on/dpo_seed1__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b_thinking_on/kto_seed1__selfaware/metrics.json
  - experiment/phase1/eval/analysis/thinking_comparison/seed1_all_arms_thinking_vs_nonthinking_summary.csv
  commands:
  - python experiment/phase1/eval/tools/compare_thinking_eval_results.py --config
    eval_amendment_b_stated_confidence_selfaware_seed1_all_arms_local_4b.yaml --output
    experiment/phase1/eval/analysis/thinking_comparison/seed1_all_arms_thinking_vs_nonthinking_summary.csv
  decisions:
  - Treat seed 1 as a completed thinking comparison, but do not generalize until seed
    2/3 and sequential arms complete.
  - Continue the queued batch; seed 2 all-arms started automatically after seed 1.
  signals:
    row_count_per_arm: 3369
    visible_think_tags_per_arm: 0
    base_confidence_coverage_pct: 99.88
    sft_confidence_coverage_pct: 99.88
    dpo_confidence_coverage_pct: 99.79
    kto_confidence_coverage_pct: 99.73
    base_delta_truthful_pct: 0.15
    sft_delta_truthful_pct: -0.48
    dpo_delta_truthful_pct: 0.66
    kto_delta_truthful_pct: -0.09
    sft_delta_refusal_recall_pct: -2.71
    sft_delta_over_refusal_pct: -3.85
legacy_session:
  id: thinking-enabled-eval-layer
  path: docs/sessions/0013 - thinking-enabled-eval-layer.md
---
# Session 0013 - Thinking-Enabled Eval Layer

Date: 2026-06-20

## Goal

Add a thinking-on evaluation layer before the next training runs so every
completed seed/model can be compared against the Amendment B non-thinking
stated-confidence evals.

## Scope

Current thinking-on matrix:

- Cold-start seed 1/2/3 all-arm SelfAware Amendment B evals:
  `base`, `sft`, `dpo`, `kto`.
- Sequential SelfAware Amendment B evals:
  seed 1 `sft_merged`, `sft->dpo`, `sft->kto`;
  seed 2 `sft_merged`, `sft->dpo`, `sft->kto`;
  seed 3 `sft_merged`, `sft->dpo`, `sft->kto`.
- A 192-row base smoke derived from the existing Amendment B base smoke.

The thinking-on configs are derived from the existing non-thinking configs and
write to separate `*_thinking_on` result directories. The source configs remain
unchanged.

## Implementation Notes

- `run_eval.py` now keeps thinking disabled as the default safe path. When
  `generation.enable_thinking: false`, `<think>` / `</think>` stop strings and
  generated-thinking rejection remain active.
- Explicit thinking-on configs set `generation.enable_thinking: true`; the
  harness does not inject thinking stop strings and records
  `enable_thinking: true` on each scored row.
- `parse_stated_confidence` accepts a final JSON object after an explicit
  `</think>` suffix. It still does not extract JSON from ordinary malformed
  prose, so confidence coverage remains a measurement gate.
- Added reusable tools:
  `experiment/phase1/eval/tools/materialize_thinking_eval_configs.py`,
  `experiment/phase1/eval/tools/run_thinking_eval_batch.py`, and
  `experiment/phase1/eval/tools/compare_thinking_eval_results.py`.

## Smoke Result

Config:
`experiment/phase1/eval/config/eval_amendment_b_stated_confidence_neutral_selfaware_seed1_base_smoke_thinking_local_4b.yaml`

Result dir:
`experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b_thinking_on`

Outcome:

- Exit code 0.
- Rows: 192.
- Confidence coverage: 192/192, 100%.
- Visible `<think>` / `</think>` tags in scored rows: 0.
- `enable_thinking: true` rows: 192/192.
- Metrics versus non-thinking smoke:
  truthful 10.94 vs 12.50; refusal_recall 1.05 vs 1.05;
  over_refusal 1.03 vs 1.03; correct_on_known 20.83 vs 23.96;
  mean stated confidence 0.942187 vs 0.899479.

Interpretation:
the initial base smoke suggests thinking-on did not create a prompt-only
over-refusal shift on this slice, but it did increase stated confidence while
slightly lowering known-answer correctness/truthful score. Treat this as a
gate-clearing diagnostic, not a full result.

Non-blocking runtime noise matched local vLLM patterns: Triton routing warning,
WSL pin-memory warning, NCCL shutdown warning, plus xgrammar nanobind leak
warnings at process teardown. The run still wrote complete metrics and rows.

## Batch Status

Detached batch launched at 2026-06-20 20:48 UTC via:

```bash
python experiment/phase1/eval/tools/run_thinking_eval_batch.py --status-path experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl
```

Status file:
`experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl`

Current first config:
`eval_amendment_b_stated_confidence_selfaware_seed1_all_arms_thinking_local_4b.yaml`

The batch runs configs sequentially in Docker with repo-local HF cache and
skips any config whose summary already exists unless forced.

## Next Checks

- Monitor `batch_status_current.jsonl` and the active per-config log.
- After each completed config, inspect coverage, retry exhaustion, row count,
  visible think tags, and nearest-control plausibility before interpreting.
- After the batch completes, run:

```bash
python experiment/phase1/eval/tools/compare_thinking_eval_results.py
```

- Update this note with the full thinking-vs-non-thinking comparison and decide
  whether thinking changes the training-regimen conclusions enough to affect the
  next training slice.
