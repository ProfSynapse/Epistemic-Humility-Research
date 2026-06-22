---
schema_version: research-session/v1
session_id: schema-response-confidence-track
title: Schema Response-Confidence Track
status: active
created_at: '2026-06-22T13:53:26Z'
updated_at: '2026-06-22T14:14:49Z'
phase: phase1
question: Can a schema-trained SFT base plus DPO/KTO/GRPO variants learn response-appropriate
  confidence without endpoint collapse?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Amendment D draft track after GRPO response-confidence endpoint-collapse failure.
  changed_by_session: Defines schema-trained response_confidence data/reward contract, includes ambiguous-middle probe rows, and launches the first local schema-SFT seed-1 run.
checkpoints: []
---
# Schema Response-Confidence Track

## Question

Can a schema-trained SFT base plus DPO/KTO/GRPO variants learn response-appropriate confidence without endpoint collapse?

## Trajectory Position

This session starts a new schema-trained response-confidence track. It preserves
v0.3 and Amendment A/B evidence, but treats prompt-elicited confidence on
models not trained for the schema as weaker evidence than schema-trained
comparisons.

## Summary

Implemented the local plumbing for Amendment D: `response_confidence` replaces
ambiguous generic `confidence` in new configs, SFT/DPO/KTO schema datasets are
projected with non-endpoint confidence targets, middle discard probe rows are
included as `.4-.6` examples, and the GRPO reward now has banded targets with
endpoint penalties. A 512-row schema-SFT smoke completed at batch 16, but its
capacity profile marked OOM risk critical, so the full SFT was launched at
batch 12.

## Checkpoints

### 001-planning - Schema Response-Confidence Track

- at: `2026-06-22T14:14:49Z`
- kind: `planning`
- summary: Started a new schema-trained track because old SFT/DPO/KTO models were not trained to emit the stated-confidence schema and Amendment B's generic `confidence` field was ambiguous.
- evidence:
  - `experiment/protocol/AMENDMENT-D-schema-response-confidence.md`
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `experiment/phase1/grpo/humility_reward.py`
- decisions:
  - Preserve old SFT/DPO/KTO results as behavior evidence, not schema-learned confidence evidence.
  - Use `response_confidence` for new training/eval contracts.
  - Interpret high response-confidence as good for both correct known answers and correct unknown abstentions.
  - Penalize exact endpoint confidence values in GRPO/RLVR reward variants.
- next_steps:
  - Train schema-SFT first, then run schema SFT->DPO, schema SFT->KTO, and schema SFT->GRPO from the merged schema-SFT base.

### 002-observation - Ambiguous Middle Rows

- at: `2026-06-22T14:14:49Z`
- kind: `observation`
- summary: The raw Qwen3-4B probe contains a third `discard` label that the locked Phase 1 dataset builder excluded from known/unknown training. The middle portion of this bucket is useful for response-confidence training.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/response_confidence_schema_manifest.json`
  - `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_manifest.json`
- signals:
    raw_probe_labels:
      known: 8892
      unknown: 7103
      discard: 4005
    discard_buckets:
      p_correct_lt_0_2: 2369
      p_correct_0_2_to_0_4: 990
      p_correct_0_4_to_0_6: 548
      p_correct_0_6_to_0_8: 84
      p_correct_gt_0_8: 14
    schema_projection_with_ambiguous_middle:
      sft_rows: 14943
      dpo_rows: 14943
      kto_rows: 29886
      grpo_train_rows: 14888
      grpo_dev_rows: 1655
- decisions:
  - Include only `discard` rows with `p_correct` in `[0.4, 0.6]` for the first schema-response-confidence track.
  - Train those rows as correct answers with middle `response_confidence`, not as unknown abstentions.

### 003-validation - Schema Data Reward And Eval Tests

- at: `2026-06-22T14:14:49Z`
- kind: `validation`
- summary: Focused GRPO/eval tests passed after adding `response_confidence` parser support, schema data projection, ambiguous-middle rows, and banded reward targets.
- evidence:
  - `experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py`
  - `experiment/phase1/grpo/tests/test_build_grpo_dataset.py`
  - `experiment/phase1/grpo/tests/test_humility_reward.py`
  - `experiment/phase1/eval/tests/test_scorers.py`
  - `experiment/phase1/eval/tests/test_run_eval_e2e.py`
- commands:
  - `python -m pytest experiment/phase1/grpo/tests/test_build_grpo_dataset.py experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py experiment/phase1/grpo/tests/test_humility_reward.py experiment/phase1/eval/tests/test_scorers.py experiment/phase1/eval/tests/test_run_eval_e2e.py -q`
- signals:
    tests_passed: 95
    warnings: 1

### 004-validation - Local SFT Batch Smoke

- at: `2026-06-22T14:14:49Z`
- kind: `validation`
- summary: A 512-row schema-SFT smoke completed successfully at per-device batch 16, proving the local training path and larger batch can run, but capacity telemetry marked OOM risk critical.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_smoke/20260622_141132/capacity_features.json`
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_smoke/20260622_141132/training_lineage.json`
- signals:
    train_rows: 512
    batch_size: 16
    effective_batch_size: 16
    final_step: 32
    training_time_seconds: 70.5
    final_loss: 0.3939
    oom_observed: 0
    oom_risk_level: critical
    capacity_peak_gpu_memory_reserved_pct: 116.49
- decisions:
  - Do not use batch 16 for the full schema-SFT run despite successful smoke completion.
  - Launch full schema-SFT at batch 12 as a speed/safety compromise.

### 005-launch - Full Schema-SFT Seed 1

- at: `2026-06-22T14:14:49Z`
- kind: `launch`
- summary: Launched the first full local schema-SFT seed-1 run from Qwen3-4B base using the response-confidence dataset with ambiguous-middle rows.
- evidence:
  - `experiment/phase1/grpo/configs/sft_schema_response_confidence_seed1_full_config.py`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train.jsonl`
- commands:
  - `docker run -d --name eh-schema-sft-seed1-full-20260622101423 --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v "${PWD}:/workspace/repo" -w /workspace/repo unsloth/unsloth:latest synaptic-tuner/Trainers/sft/train_sft.py --config experiment/phase1/grpo/configs/sft_schema_response_confidence_seed1_full_config.py`
- signals:
    container: eh-schema-sft-seed1-full-20260622101423
    batch_size: 12
    effective_batch_size: 12
    dataset_rows: 14943
- next_steps:
  - Monitor full schema-SFT logs, capacity, and final artifacts.
  - After completion, run a schema eval smoke before launching schema DPO/KTO/GRPO.

### 006-progress - Ambiguous Rows And Full SFT Capacity

- at: `2026-06-22T14:20:00Z`
- kind: `progress`
- summary: Confirmed the schema projection keeps the strict ambiguous/discard middle band as middle-confidence answer rows, while the live full schema-SFT run is progressing but saturating local VRAM.
- evidence:
  - `scratch/schema_response_confidence/qwen3-4b-instruct/response_confidence_schema_manifest.json`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_manifest.json`
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/logs/training_20260622_141604.jsonl`
- signals:
    sft_locked_known_unknown_rows: 14395
    sft_ambiguous_middle_rows: 548
    ambiguous_response_confidence_min: 0.40625
    ambiguous_response_confidence_max: 0.59375
    grpo_ambiguous_middle_rows: 548
    live_step_checked: 200
    total_steps: 1246
    live_steps_per_second: 0.88
    live_vram_used_gb: 23.68
    live_oom_risk_level: critical
- decisions:
  - Treat ambiguous middle rows as useful signal in Amendment D, not waste.
  - Do not launch parallel GPU work during this full schema-SFT cell.
  - If the cell fails or needs rerun, use batch 8 rather than batch 12.

### 007-result - Full Schema-SFT Seed 1 And Eval Smoke

- at: `2026-06-22T14:49:30Z`
- kind: `result`
- summary: Full schema-SFT seed 1 completed locally and a SelfAware mixed-slice live eval smoke passed the JSON contract, but the model emitted constant `response_confidence: 0.8` on every row.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/final_model`
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_d_response_confidence_selfaware_schema_sft_seed1_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_smoke_4b/schema_sft_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_smoke_4b/schema_sft_seed1__selfaware/scored_rows.jsonl`
- signals:
    training_exit_code: 0
    train_rows: 14943
    train_runtime_seconds: 1419.544
    final_loss: 0.1609
    training_oom_observed: 0
    training_oom_risk_level: critical
    eval_rows: 192
    eval_known_rows: 97
    eval_unknown_rows: 95
    stated_confidence_coverage_pct: 100.0
    unique_response_confidence_values:
      - 0.8
    endpoint_confidence_count: 0
    refusal_recall_pct: 90.53
    over_refusal_pct: 70.1
    correct_on_known_pct: 41.38
    truthful_pct: 51.04
- interpretation:
  - SFT learned the JSON envelope and the response-confidence key cleanly.
  - SFT alone did not learn calibrated confidence variation; it collapsed to the dominant desirable target value of `0.8`.
  - This is not the same failure as the previous endpoint-`1.0` bridge, but it is still degenerate confidence for analysis.
  - The next confidence-shaping evidence should come from DPO/KTO/GRPO or from adding more explicit low/middle contrast to supervised data.
- gotchas:
  - OOD eval config keys must be canonical loader IDs such as `selfaware`; invented keys like `selfaware_unknown_smoke` fail before generation.
