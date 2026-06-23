---
schema_version: research-session/v1
session_id: schema-response-confidence-track
title: Schema Response-Confidence Track
status: active
created_at: '2026-06-22T13:53:26Z'
updated_at: '2026-06-23T00:17:00Z'
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

### 008-planning - Merge-First Downstream Schema Runs

- at: `2026-06-22T15:05:00Z`
- kind: `planning`
- summary: Clarified that Amendment D downstream DPO/KTO/GRPO cells should not run bare from the original Qwen3 base; all downstream cells must start from a merged schema-SFT model and train fresh adapters.
- evidence:
  - `experiment/protocol/AMENDMENT-D-schema-response-confidence.md`
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/final_model`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train.jsonl`
- decisions:
  - Treat `schema_sft` as the only bare-base Amendment D training cell.
  - Merge the completed schema-SFT adapter into a standalone local merged model before DPO, KTO, or GRPO.
  - Train `schema_sft_dpo`, `schema_sft_kto`, and `schema_sft_grpo` as fresh LoRA adapters on that merged schema-SFT base.
  - Exclude bare `schema_dpo`, `schema_kto`, and `schema_grpo` from the initial Amendment D matrix.
  - For GRPO, set `model.model_name` to the merged schema-SFT path and leave `model.lora_path` unset/null to avoid accidental adapter stacking.
- dataset_construction:
    dpo:
      chosen_response_confidence: 0.8
      rejected_response_confidence: 0.2
      ambiguous_chosen: gold answer with `response_confidence = p_correct`
      ambiguous_rejected: sampled wrong answer with high `response_confidence: 0.8`
    kto:
      true_label_response_confidence: 0.8
      false_label_response_confidence: 0.2
      ambiguous_true: gold answer with `response_confidence = p_correct`
      ambiguous_false: sampled wrong answer with high `response_confidence: 0.8`
- next_steps:
  - Merge schema-SFT seed 1.
  - Sanity-eval the merged model against the adapter result.
  - Launch DPO/KTO/GRPO smoke runs from the merged schema-SFT base.

### 009-validation - Schema-SFT Merge Sanity

- at: `2026-06-22T15:22:23Z`
- kind: `validation`
- summary: Merged the completed schema-SFT seed-1 LoRA into a standalone local model and ran a SelfAware mixed-slice smoke; merged behavior stayed close to the adapter smoke and preserved the JSON contract.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/Qwen3-4B-bnb-4bit/merged-16bit`
  - `experiment/phase1/eval/config/eval_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_smoke_4b/schema_sft_merged_seed1__selfaware/metrics.json`
- signals:
    eval_rows: 192
    stated_confidence_coverage_pct: 100.0
    unique_response_confidence_values:
      - 0.8
    refusal_recall_pct: 89.47
    over_refusal_pct: 63.92
    correct_on_known_pct: 40.0
    truthful_pct: 51.56
- interpretation:
  - The merged model is a usable base for Amendment D downstream DPO/KTO/GRPO cells.
  - The confidence-collapse issue is present in the merged base too, so downstream cells are testing whether preference/RL training can shape confidence beyond SFT's constant 0.8.

### 010-blocker - DPO Loader Column Mismatch

- at: `2026-06-22T15:22:23Z`
- kind: `blocker`
- summary: The first DPO smoke from the merged schema-SFT base failed before model loading because appended ambiguous rows added provenance columns that ordinary DPO rows did not have.
- evidence:
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl`
- signals:
    trainer: dpo
    attempted_batch_size: 4
    attempted_gradient_accumulation: 2
    max_steps: 10
    failure_stage: `load_dataset("json")`
    missing_ordinary_row_columns:
      - `label`
      - `p_correct`
- decisions:
  - Fix the dataset projection so normal and ambiguous rows share stable optional provenance columns.
  - Add a regression test for row-key stability before regenerating local scratch datasets and relaunching DPO.

### 011-validation - DPO Smoke Batch Probe

- at: `2026-06-22T15:31:43Z`
- kind: `validation`
- summary: Fixed the schema-response-confidence JSONL projection with typed provenance sentinels, regenerated scratch datasets, and completed DPO smoke runs from the merged schema-SFT base.
- evidence:
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py`
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_smoke/20260622_batch4_step10_typedcols/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_smoke/20260622_batch8_step10_probe/capacity_features.json`
- commands:
  - `python -m pytest experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py experiment/phase1/grpo/tests/test_humility_reward.py -q`
  - `python experiment/phase1/grpo/build_schema_response_confidence_datasets.py --output-dir scratch/schema_response_confidence/qwen3-4b-instruct --include-ambiguous-middle`
- signals:
    tests_passed: 26
    dpo_batch4_accum2:
      completed: true
      final_step: 10
      effective_batch_size: 8
      oom_risk_level: low
      peak_reserved_vram_gb: 11.092
      peak_steps_per_second: 0.366
    dpo_batch8_accum1:
      completed: true
      final_step: 10
      effective_batch_size: 8
      oom_risk_level: high
      peak_reserved_vram_gb: 22.633
      peak_steps_per_second: 0.358
- decisions:
  - Use batch 4 with gradient accumulation 2 for the full schema-SFT->DPO run unless longer full-run telemetry shows this is unsafe.
  - Do not scale DPO to batch 8 locally; it provides no speed gain and leaves only about 1.4 GB reserved-VRAM headroom.
- gotchas:
  - HF JSON loading needs stable column types, not only stable keys; ordinary rows should use typed sentinels such as `""` and `-1.0` instead of null provenance fields.

### 012-launch - Full Schema-SFT To DPO Seed 1

- at: `2026-06-22T15:33:09Z`
- kind: `launch`
- summary: Launched the first full local schema-SFT->DPO seed-1 run from the merged schema-SFT base after low-risk batch-4 smoke probes.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/Qwen3-4B-bnb-4bit/merged-16bit`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch4_accum2_seed1`
- commands:
  - `docker run -d --name eh-schema-dpo-seed1-full-202606221132 ... train_dpo.py --model-name /workspace/repo/scratch/schema_response_confidence/runs/sft_schema_seed1_full/20260622_141511/Qwen3-4B-bnb-4bit/merged-16bit --local-file /workspace/repo/scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl --output-root /workspace/repo/scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full --run-timestamp 20260622_batch4_accum2_seed1 --batch-size 4 --gradient-accumulation 2 --learning-rate 5e-6 --seed 1 --lora-r 32 --lora-alpha 64 --lora-dropout 0.05 --num-epochs 1`
- signals:
    container: eh-schema-dpo-seed1-full-202606221132
    train_rows: 14943
    batch_size: 4
    gradient_accumulation: 2
    effective_batch_size: 8
    data_loader_status: passed

### 013-recovery - DPO Batch 4 Full Run Aborted For VRAM Risk

- at: `2026-06-22T15:43:09Z`
- kind: `recovery`
- summary: Stopped the first full schema-SFT->DPO run after live telemetry contradicted the 10-step smoke and showed critical VRAM pressure, then relaunched with the same effective batch at lower per-device batch.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch4_accum2_seed1/logs/training_20260622_153402.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch2_accum4_seed1`
  - `.skills/experiment-runner/reference/local-runtime.md`
- signals:
    aborted_run:
      container: eh-schema-dpo-seed1-full-202606221132
      stopped_at_step: 185
      total_steps: 1868
      batch_size: 4
      gradient_accumulation: 2
      effective_batch_size: 8
      live_vram_used_gb: 23.722
      oom_risk_level: critical
      stop_exit_code: 137
    relaunched_run:
      container: eh-schema-dpo-seed1-full-b2a4-202606221144
      batch_size: 2
      gradient_accumulation: 4
      effective_batch_size: 8
      data_loader_status: passed
- decisions:
  - Do not trust a 10-step DPO smoke alone for full-run batch sizing when row lengths vary.
  - Continue schema-SFT->DPO at batch 2 / accumulation 4, preserving effective batch 8 with safer per-device memory.
- next_steps:
  - Confirm the relaunched run remains stable beyond the first 100-200 optimizer steps.
  - After DPO completes, eval the DPO adapter on the schema SelfAware config and launch the schema-SFT->KTO smoke/full path.

### 014-validation - DPO Relaunch Stable And GRPO Prep

- at: `2026-06-22T15:51:52Z`
- kind: `validation`
- summary: The batch-2 DPO relaunch remained low-risk beyond 100 optimizer steps, and the Amendment D GRPO smoke plumbing was prepared with known/unknown/ambiguous coverage.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch2_accum4_seed1/logs/training_20260622_154449.jsonl`
  - `experiment/phase1/grpo/make_smoke_subset.py`
  - `experiment/phase1/grpo/configs/grpo_schema_sft_merged_seed1_micro_smoke.yaml`
  - `experiment/phase1/grpo/configs/grpo_schema_sft_merged_seed1_full.yaml`
  - `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train_smoke_48.jsonl`
- commands:
  - `python experiment/phase1/grpo/make_smoke_subset.py --input scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train.jsonl --output scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train_smoke_48.jsonl --per-label 16 --labels known,unknown,ambiguous`
  - `python -m pytest experiment/phase1/grpo/tests/test_make_smoke_subset.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py experiment/phase1/grpo/tests/test_humility_reward.py -q`
- signals:
    dpo_relaunch_step_checked: 145
    dpo_total_steps: 1868
    dpo_steps_per_second: 0.358
    dpo_oom_risk_level: low
    dpo_live_vram_used_gb: 10.752
    grpo_smoke_subset_rows: 48
    grpo_smoke_subset_labels:
      known: 16
      unknown: 16
      ambiguous: 16
    tests_passed: 22
- decisions:
  - Leave DPO running at batch 2 / accumulation 4.
  - Use the 48-row schema GRPO smoke subset for first GRPO contact so the ambiguous-middle reward path is exercised.

### 015-heartbeat - DPO Relaunch Mid-Run

- at: `2026-06-22T16:07:44Z`
- kind: `heartbeat`
- summary: The safer batch-2 DPO run is stable after a longer check, but the objective is already separating chosen/rejected very aggressively.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch2_accum4_seed1/logs/training_20260622_154449.jsonl`
- signals:
    step_checked: 480
    total_steps: 1868
    elapsed_seconds: 1352.775
    steps_per_second: 0.355
    oom_risk_level: low
    current_live_vram_used_gb: 9.215
    max_reserved_vram_gb: 11.271
    latest_loss: 0.0002
    rewards_accuracy: 1.0
    rewards_margin: 9.9108
- interpretation:
  - Batch 2 / accumulation 4 is the right local DPO setting for this full run.
  - The near-zero DPO loss and large margins may indicate strong preference overoptimization; eval should be interpreted as evidence about whether this objective improved calibrated expression or merely pushed rejected completions down.
- next_steps:
  - Keep the run going unless OOM or trainer failure occurs.
  - On completion, run schema SelfAware eval against the DPO adapter before launching KTO.

### 016-result - Schema-SFT To DPO Seed 1 Smoke Eval

- at: `2026-06-22T17:23:51Z`
- kind: `result`
- summary: The safer full schema-SFT->DPO seed-1 run completed, but the first SelfAware smoke eval shows no clear behavioral gain over merged schema-SFT and a stronger high-confidence collapse.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch2_accum4_seed1/final_model`
  - `scratch/schema_response_confidence/runs/schema_sft_dpo_seed1_full/20260622_batch2_accum4_seed1/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_d_response_confidence_selfaware_schema_sft_dpo_seed1_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_dpo_seed1_smoke_4b/schema_sft_dpo_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_dpo_seed1_smoke_4b/schema_sft_dpo_seed1__selfaware/scored_rows.jsonl`
- signals:
    training:
      exit_code: 0
      final_step: 1868
      runtime_seconds: 5200.8
      final_loss: 0.0387
      peak_reserved_vram_gb: 11.271
      oom_risk_level: low
    eval:
      rows: 192
      known_rows: 97
      unknown_rows: 95
      stated_confidence_coverage_pct: 100.0
      mean_stated_confidence: 0.873828
      confidence_values:
        0.875: 189
        0.8: 3
      refusal_recall_pct: 87.37
      over_refusal_pct: 64.95
      correct_on_known_pct: 41.18
      truthful_pct: 50.52
- interpretation:
  - DPO successfully trained and preserved the JSON schema, but it did not produce calibrated confidence variation on this smoke slice.
  - Relative to the merged schema-SFT smoke, DPO is behaviorally near-flat or slightly worse while pushing confidence higher, consistent with the near-zero DPO loss and very large preference margins observed during training.
  - Treat this as bounded seed-1 evidence that schema-SFT->DPO alone is not solving response-confidence calibration at these settings.
- next_steps:
  - Launch schema-SFT->KTO from the same merged schema-SFT base.
  - Defer full SelfAware DPO eval until after KTO/GRPO smokes clarify whether DPO is worth broader evaluation.

### 017-launch - Full Schema-SFT To KTO Seed 1

- at: `2026-06-22T17:31:31Z`
- kind: `launch`
- summary: KTO smoke probes passed from the merged schema-SFT base, and the full schema-SFT->KTO seed-1 run was launched at batch 8 / accumulation 1.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_smoke/20260622_batch4_step10_probe/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_smoke/20260622_batch8_step10_probe/capacity_features.json`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch8_accum1_seed1`
- signals:
    kto_batch4_accum2_smoke:
      completed: true
      final_step: 10
      effective_batch_size: 8
      oom_risk_level: low
      peak_reserved_vram_gb: 4.486
      peak_steps_per_second: 0.31
    kto_batch8_accum1_smoke:
      completed: true
      final_step: 10
      effective_batch_size: 8
      oom_risk_level: low
      peak_reserved_vram_gb: 6.35
      peak_steps_per_second: 0.469
    full_launch:
      container: eh-schema-kto-seed1-full-b8a1-202606221331
      train_rows: 29886
      batch_size: 8
      gradient_accumulation: 1
      effective_batch_size: 8
      learning_rate: 1.0e-6
      beta: 0.1
- decisions:
  - Use batch 8 / accumulation 1 for the full KTO run; it improves throughput over batch 4 and remains low VRAM risk in smoke.
- next_steps:
  - Monitor until the full KTO run reaches optimizer steps and estimate ETA.
  - On completion, run the same schema SelfAware smoke eval before moving to GRPO.

### 018-heartbeat - KTO Full Run Started

- at: `2026-06-22T17:37:25Z`
- kind: `heartbeat`
- summary: The full schema-SFT->KTO seed-1 run reached optimizer steps and is memory-stable at the faster batch-8 setting.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch8_accum1_seed1/logs/training_*.jsonl`
- signals:
    step_checked: 105
    total_steps: 3736
    steps_per_second: 0.519
    oom_risk_level: low
    current_live_vram_used_gb: 8.402
    max_reserved_vram_gb: 8.068
    latest_loss: 0.4968
    latest_kl: 0.0659
- decisions:
  - Keep KTO running at batch 8 / accumulation 1.
  - Do not launch eval or GRPO in parallel with this full KTO run.
- next_steps:
  - Check again after a longer interval; if it remains stable, let it complete and then run schema SelfAware smoke eval.

### 019-reroute - KTO Batch Increase

- at: `2026-06-22T18:05:00Z`
- kind: `reroute`
- summary: The first full schema-SFT->KTO seed-1 run was intentionally stopped at batch 8 / accumulation 1 after stable telemetry, then relaunched at batch 24 / accumulation 1 to use available RTX 3090 headroom.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch8_accum1_seed1/logs/training_*.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_smoke/20260622_batch16_step10_probe/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_smoke/20260622_batch24_step10_probe/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch24_accum1_seed1`
- signals:
    stopped_batch8_full:
      container: eh-schema-kto-seed1-full-b8a1-202606221331
      exit_code: 137
      stop_reason: manual_user_directed_capacity_reroute
      oom_observed: false
      last_observed_step_approx: 365
      oom_risk_level: low
      peak_reserved_vram_gb_approx: 10.441
    kto_batch16_accum1_smoke:
      completed: true
      final_step: 10
      effective_batch_size: 16
      oom_risk_level: low
      peak_reserved_vram_gb: 10.807
      peak_samples_per_second: 5.235
    kto_batch24_accum1_smoke:
      completed: true
      final_step: 10
      effective_batch_size: 24
      oom_risk_level: low
      peak_reserved_vram_gb: 16.529
      peak_reserved_headroom_gb: 7.47
      peak_samples_per_second: 6.494
    full_launch:
      container: eh-schema-kto-seed1-full-b24a1-202606221405
      train_rows: 29886
      batch_size: 24
      gradient_accumulation: 1
      effective_batch_size: 24
      expected_optimizer_steps_approx: 1246
- decisions:
  - Use batch 24 / accumulation 1 for the full KTO rerun because smoke throughput improved and the card was idle, while keeping an early monitor because DPO showed that 10-step smokes can understate full-run memory growth.
- next_steps:
  - Check startup logs and live VRAM after the trainer reaches optimizer steps.
  - If memory remains below critical range, let the KTO run complete before launching KTO eval.

### 020-reroute - KTO Batch 24 Too Hot

- at: `2026-06-22T18:15:00Z`
- kind: `reroute`
- summary: The batch-24 KTO full run was stopped after early live telemetry hit critical VRAM, then relaunched at batch 16 / accumulation 1 as the faster-but-safer capacity point.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch24_accum1_seed1/logs/training_*.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch16_accum1_seed1`
- signals:
    stopped_batch24_full:
      container: eh-schema-kto-seed1-full-b24a1-202606221405
      exit_code: 137
      stop_reason: manual_pre_oom_capacity_reroute
      last_observed_step: 25
      total_steps: 1246
      live_vram_used_gb: 23.709
      gpu_vram_utilization_pct: 98.79
      max_reserved_vram_gb_reported: 26.779
      oom_risk_level: critical
    full_relaunch:
      container: eh-schema-kto-seed1-full-b16a1-202606221415
      train_rows: 29886
      batch_size: 16
      gradient_accumulation: 1
      effective_batch_size: 16
      expected_optimizer_steps_approx: 1868
- decisions:
  - Treat KTO batch 24 as too close to the RTX 3090 limit for this dataset despite a low-risk 10-step smoke.
  - Use batch 16 / accumulation 1 as the current KTO full-run speed/safety compromise.
- next_steps:
  - Monitor batch 16 after optimizer steps begin; if live VRAM remains comfortably below the ceiling, let the run complete.

### 021-heartbeat - KTO Batch 16 Stable

- at: `2026-06-22T18:18:00Z`
- kind: `heartbeat`
- summary: The schema-SFT->KTO seed-1 batch-16 rerun reached optimizer steps and is stable enough to continue.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch16_accum1_seed1/logs/training_*.jsonl`
- signals:
    step_checked: 30
    total_steps: 1868
    steps_per_second: 0.354
    samples_per_second: 5.665
    live_vram_used_gb: 16.857
    max_reserved_vram_gb: 16.523
    reserved_headroom_gb: 7.476
    oom_risk_level: low
    latest_loss: 0.4996
    latest_kl: 0.0131
- decisions:
  - Continue the batch-16 KTO full run.
  - Do not run parallel eval while confirming whether batch-16 stays stable beyond the early long-row region.
- next_steps:
  - Recheck after a longer interval; if it remains low risk, let the full run finish and then run the schema SelfAware KTO smoke eval.

### 022-reroute - KTO Batch 16 Also Too Tight

- at: `2026-06-22T18:30:00Z`
- kind: `reroute`
- summary: The batch-16 KTO full run was stopped after later telemetry climbed into a high-risk VRAM band; batch 12 / accumulation 1 was launched as the last speed-up attempt before falling back to the proven batch-8 setting.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch16_accum1_seed1/logs/training_*.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch12_accum1_seed1`
- signals:
    stopped_batch16_full:
      container: eh-schema-kto-seed1-full-b16a1-202606221415
      exit_code: 137
      stop_reason: manual_pre_oom_capacity_reroute
      last_observed_step: 250
      total_steps: 1868
      live_vram_used_gb_range: "23.473-23.72"
      gpu_vram_utilization_pct_range: "97.8-98.83"
      reserved_headroom_gb: 0.861
      oom_risk_level: high
    full_relaunch:
      container: eh-schema-kto-seed1-full-b12a1-202606221430
      train_rows: 29886
      batch_size: 12
      gradient_accumulation: 1
      effective_batch_size: 12
      expected_optimizer_steps_approx: 2491
- decisions:
  - Treat batch 16 as too tight for unattended full KTO despite early low-risk logs.
  - Try batch 12 because it still improves effective batch over batch 8, but revert to batch 8 if batch 12 enters high/critical VRAM risk.
- next_steps:
  - Monitor batch 12 at startup and after the long-row region; keep only if it remains below high risk.

### 023-heartbeat - KTO Batch 12 Cleared Long-Row Check

- at: `2026-06-22T18:35:00Z`
- kind: `heartbeat`
- summary: The schema-SFT->KTO seed-1 batch-12 run passed the step range where batch 16 became unsafe, with low OOM risk and materially more headroom.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch12_accum1_seed1/logs/training_*.jsonl`
- signals:
    step_checked: 390
    total_steps: 2491
    steps_per_second: 0.362
    samples_per_second: 4.343
    live_vram_used_gb: 12.037
    current_reserved_vram_gb: 11.703
    max_reserved_vram_gb: 15.973
    max_reserved_headroom_gb: 8.027
    oom_risk_level: low
    latest_loss: 0.0503
    rewards_margin: 6.4391
- decisions:
  - Treat batch 12 / accumulation 1 as the current accepted KTO full-run setting.
  - Continue without parallel GPU eval until KTO completes.
- next_steps:
  - Let the KTO run continue with longer heartbeat checks; expected remaining time from this checkpoint is roughly 95-100 minutes.
  - On completion, run schema SelfAware smoke eval against the KTO adapter.

### 024-heartbeat - KTO Batch 12 Mid-Run

- at: `2026-06-22T19:13:00Z`
- kind: `heartbeat`
- summary: The accepted batch-12 schema-SFT->KTO seed-1 run remains low-risk around the midpoint.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch12_accum1_seed1/logs/training_*.jsonl`
- signals:
    step_checked: 1200
    total_steps: 2491
    steps_per_second: 0.349
    samples_per_second: 4.187
    live_vram_used_gb: 15.398
    current_reserved_vram_gb: 15.064
    max_reserved_vram_gb: 16.18
    max_reserved_headroom_gb: 7.82
    oom_risk_level: low
    latest_loss: 0.0026
    rewards_margin: 15.1594
- decisions:
  - Continue the batch-12 KTO full run.
  - Keep GPU eval paused until the KTO run finishes.
- next_steps:
  - Recheck near completion; then run schema SelfAware smoke eval against the KTO adapter.

### 025-result - KTO Seed 1 Completed And Evaluated

- at: `2026-06-22T20:44:20Z`
- kind: `result`
- summary: The accepted schema-SFT->KTO seed-1 batch-12 run completed cleanly and its SelfAware schema smoke eval shows no meaningful confidence-calibration rescue relative to schema-SFT or schema-SFT->DPO.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_kto_seed1_full/20260622_batch12_accum1_seed1/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_d_response_confidence_selfaware_schema_sft_kto_seed1_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_kto_seed1_smoke_4b/schema_sft_kto_seed1__selfaware/metrics.json`
- signals:
    training:
      status_completed: 1
      final_step: 2491
      training_time_seconds: 7678.4
      batch_size: 12
      gradient_accumulation: 1
      effective_batch_size: 12
      peak_reserved_vram_gb: 21.1
      min_reserved_headroom_gb: 2.9
      oom_observed: 0
      oom_risk_level: moderate
      final_loss: 0.065176
    eval:
      n: 192
      refusal_recall_pct: 86.32
      over_refusal_pct: 61.86
      truthful_pct: 50.52
      correct_on_known_pct: 40.54
      answer_on_unknown_pct: 13.68
      stated_confidence_coverage_pct: 100.0
      mean_stated_confidence: 0.8
      confidence_mae_vs_response_appropriateness: 0.496875
      confidence_brier_vs_response_appropriateness: 0.336875
    local_comparison:
      schema_sft_seed1_truthful_pct: 51.04
      schema_sft_seed1_mean_stated_confidence: 0.8
      schema_sft_dpo_seed1_truthful_pct: 50.52
      schema_sft_dpo_seed1_mean_stated_confidence: 0.873828
- interpretation:
  - KTO preserved the schema contract but did not teach response-appropriate confidence under this setup.
  - Relative to schema-SFT, KTO slightly reduced over-refusal but also reduced refusal recall; truthful rate stayed effectively flat/slightly lower.
  - Confidence remains collapsed to a narrow high value, so preference training after schema-SFT is not yet shaping the confidence scalar.
- decisions:
  - Treat schema-SFT->KTO seed 1 as a completed bounded local diagnostic, not headline evidence.
  - Before scaling additional downstream preference runs, prioritize reward/data changes that directly penalize endpoint or constant confidence collapse.
- next_steps:
  - Keep the KTO eval config as reusable source, while leaving generated training/eval artifacts local/ignored.
  - Use this result to inform the next GRPO bootstrap attempt from the schema-SFT base.

### 026-result - Full Merged Schema-SFT Eval Gate

- at: `2026-06-22T21:20:00Z`
- kind: `result`
- summary: Ran the full SelfAware eval on the merged schema-SFT seed-1 model before launching another downstream fine-tune; the checkpoint is structurally usable but behaviorally over-refusal-heavy with collapsed confidence.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_full_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_full_4b/schema_sft_merged_seed1__selfaware/metrics.json`
- signals:
    n: 3369
    known_rows: 2337
    unknown_rows: 1032
    stated_confidence_coverage_pct: 100.0
    stated_confidence_retry_exhausted: 0
    unique_response_confidence_values:
      - 0.8
    refusal_recall_pct: 89.05
    answer_on_unknown_pct: 10.95
    over_refusal_pct: 59.14
    correct_on_known_pct: 48.06
    truthful_pct: 40.9
    response_confidence_mae_vs_response_appropriateness: 0.554586
    response_confidence_brier_vs_response_appropriateness: 0.394586
- interpretation:
  - The merged schema-SFT model is not bunk as an output-contract base: JSON coverage is complete and no retries were needed.
  - SFT alone still fails the calibration question: every row emits `response_confidence: 0.8`, including wrong answers and over-refusals.
  - The model has enough structural competence to justify GRPO, because the reward can directly target over-refusal, hallucinated answers, malformed JSON, and confidence banding.
- decisions:
  - Do not launch more DPO/KTO variants before testing whether GRPO can move the collapsed response-confidence scalar.
  - Use the merged schema-SFT seed-1 checkpoint as the GRPO base.

### 027-validation - GRPO Full Dataset Schema Repair

- at: `2026-06-22T21:34:00Z`
- kind: `validation`
- summary: The first full-dataset GRPO batch probe exposed a Hugging Face JSON schema mismatch because ambiguous rows had provenance fields that normal known/unknown rows lacked; the builder now emits stable typed columns for every row.
- evidence:
  - `experiment/phase1/grpo/build_grpo_dataset.py`
  - `experiment/phase1/grpo/tests/test_build_grpo_dataset.py`
  - `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train.jsonl`
- commands:
  - `python -m pytest experiment/phase1/grpo/tests/test_build_grpo_dataset.py experiment/phase1/grpo/tests/test_humility_reward.py -q`
  - `py -3.11 experiment/phase1/grpo/build_grpo_dataset.py --model-tag qwen3-4b-instruct --output-dir scratch/schema_response_confidence/qwen3-4b-instruct-grpo --confidence-field response_confidence --include-ambiguous-middle`
- signals:
    tests_passed: 21
    regenerated_train_rows: 14888
    regenerated_dev_rows: 1655
    train_labels:
      known: 7981
      unknown: 6414
      ambiguous: 493
    unique_jsonl_column_sets: 1
    normal_row_p_correct_sentinel: -1.0
    normal_row_ambiguity_band_sentinel: ""
- decisions:
  - Keep `p_correct` and `ambiguity_band` present on all GRPO rows using typed sentinels for non-ambiguous rows.
  - Treat mixed row-family JSONL schema stability as a preflight requirement before full trainer launches.

### 028-validation - GRPO Micro And Batch Probes

- at: `2026-06-22T21:52:00Z`
- kind: `validation`
- summary: GRPO smoke and full-dataset batch probes completed from the merged schema-SFT base; batch 32 is the fastest safe local setting tested so far.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_micro_smoke/20260622_212817/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_batch8_probe/20260622_213553/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_batch16_probe/20260622_214301/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_batch32_probe/20260622_214717/capacity_features.json`
- signals:
    micro_smoke:
      completed: true
      max_steps: 6
      batch_size: 4
      peak_reserved_vram_gb: 4.416
      oom_risk_level: low
      nonzero_reward_variance_steps: 4
      zero_variance_steps: 2
    batch8_probe:
      completed: true
      max_steps: 12
      peak_reserved_vram_gb: 4.357
      peak_samples_per_second: 1.603
      projected_full_steps: 7444
    batch16_probe:
      completed: true
      max_steps: 12
      peak_reserved_vram_gb: 5.746
      peak_samples_per_second: 2.661
      projected_full_steps: 3722
    batch32_probe:
      completed: true
      max_steps: 12
      peak_reserved_vram_gb: 10.934
      peak_samples_per_second: 3.128
      projected_full_steps: 1861
      oom_risk_level: low
- decisions:
  - Launch the full schema-SFT->GRPO seed-1 run at batch 32 / accumulation 1 / 4 generations per prompt.
  - Do not spend more time probing batch 64 unless the batch-32 full run proves too slow or too conservative.

### 029-launch - Full Schema-SFT To GRPO Seed 1

- at: `2026-06-22T22:05:00Z`
- kind: `launch`
- summary: Launched the full local schema-SFT->GRPO seed-1 run at batch 32 after the full SFT eval gate and batch probes; early training telemetry is healthy.
- evidence:
  - `experiment/phase1/grpo/configs/grpo_schema_sft_merged_seed1_full.yaml`
  - `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_full/20260622_215344/logs/training_20260622_215457.jsonl`
  - `scratch/schema_response_confidence/reward_debug/schema_sft_grpo_seed1_full_b32_latest.jsonl`
- commands:
  - `docker run -d --name eh-schema-sft-grpo-seed1-full-b32-202606221753 --gpus all --ipc=host --entrypoint python3 ... synaptic-tuner/Trainers/grpo/train_grpo.py --config experiment/phase1/grpo/configs/grpo_schema_sft_merged_seed1_full.yaml`
- signals:
    container: eh-schema-sft-grpo-seed1-full-b32-202606221753
    run_dir: `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_full/20260622_215344`
    train_rows: 14888
    batch_size: 32
    gradient_accumulation: 1
    num_generations: 4
    total_steps: 1861
    first_logged_step: 25
    steps_per_second: 0.081
    samples_per_second: 2.596
    peak_reserved_vram_gb_at_step25: 10.934
    oom_risk_level_at_step25: low
    reward_mean_at_step25: -0.308637
    reward_std_at_step25: 1.122555
    frac_reward_zero_std_at_step25: 0.105
- interpretation:
  - The repaired full GRPO dataset is loading correctly, including `known`, `unknown`, and `ambiguous` rows with stable columns.
  - Early reward-debug rows show enough behavioral diversity for GRPO to learn from: correct known answers, hallucinations, abstentions, malformed JSON, and varied confidence values.
  - The run is still early; the next evidence gate is completion plus a full schema SelfAware eval against the GRPO adapter.
- next_steps:
  - Monitor the GRPO run with direct Docker/log checks.
  - On completion, run the schema SelfAware eval and compare against merged schema-SFT, schema-SFT->DPO, and schema-SFT->KTO.

### 030-recovery - GRPO Reward Refusal Matcher Fix

- at: `2026-06-23T00:07:00Z`
- kind: `recovery`
- summary: Stopped the first full schema-SFT->GRPO seed-1 run and its first retry after reward-debug inspection showed semantic unknown abstentions being penalized as hallucinations; patched the reward matcher before relaunching retry2.
- evidence:
  - `scratch/schema_response_confidence/reward_debug/schema_sft_grpo_seed1_full_b32_latest.jsonl`
  - `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_full/20260622_215344/logs/training_20260622_215457.jsonl`
  - `experiment/phase1/grpo/humility_reward.py`
  - `experiment/phase1/grpo/tests/test_humility_reward.py`
- signals:
    stopped_container: eh-schema-sft-grpo-seed1-full-b32-202606221753
    stopped_exit_code: 137
    last_logged_step: 600
    total_steps: 1861
    stop_reason: reward_alignment_bug
    observed_bad_case:
      label: unknown
      answer: `I'm really not sure what the answer is, so I'd rather not guess.`
      old_reward: -1.9
      issue: Semantic abstention was not counted as refusal because the matcher covered only narrower canonical forms.
    fixed_case:
      is_refusal: true
      unknown_reward: 0.75
      known_over_refusal_reward: -1.1
    retry1:
      container: eh-schema-sft-grpo-seed1-full-b32-retry1-202606222003
      status: stopped_early
      stop_reason: second_semantic_abstention_matcher_gap
      additional_bad_forms:
        - `NONE OF US KNOW THE ANSWER TO THAT ONE.`
        - `How can I know the answer to this question?`
        - `I can't answer reliably.`
    retry2:
      container: eh-schema-sft-grpo-seed1-full-b32-retry2-202606222015
      run_dir: `scratch/schema_response_confidence/runs/schema_sft_grpo_seed1_full/20260623_001629`
      reward_debug: `scratch/schema_response_confidence/reward_debug/schema_sft_grpo_seed1_full_b32_retry2_latest.jsonl`
      first_logged_step: 25
      total_steps: 1861
      steps_per_second: 0.077
      reward_std: 1.106988
      frac_reward_zero_std: 0.12
      peak_reserved_vram_gb: 10.934
      oom_risk_level: low
- commands:
  - `docker stop eh-schema-sft-grpo-seed1-full-b32-202606221753`
  - `docker stop eh-schema-sft-grpo-seed1-full-b32-retry1-202606222003`
  - `python -m pytest experiment/phase1/grpo/tests/test_humility_reward.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py -q`
- decisions:
  - Discard the first GRPO full run and retry1 as flawed reward-contract evidence.
  - Relaunch GRPO from scratch after expanding the refusal matcher to semantic abstentions such as "I'm not sure", "not confident", "rather not guess", collective "none of us know", indirect "how can I know", and "can't answer reliably".
  - Keep reward-debug inspection as an early gate for new reward contracts, not just a debugging convenience.
