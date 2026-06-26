---
schema_version: research-session/v1
session_id: probe-scaled-response-confidence-retrain
title: Probe-Scaled Response Confidence Retrain
status: active
created_at: '2026-06-23T09:36:54Z'
updated_at: '2026-06-23T12:24:00Z'
phase: phase1
question: Can probe-derived 32-sample p_correct targets prevent response_confidence
  collapse in schema-SFT and downstream GRPO?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Amendment D schema-response-confidence seed-1 showed output-contract learning but confidence collapse to constant 0.8 across schema-SFT, KTO, and GRPO evals.
  changed_by_session: Opens Amendment E to replace constant SFT/DPO/KTO response-confidence targets with probe-scaled targets derived from the original 32-sample p_correct evidence.
checkpoints: []
---
# Probe-Scaled Response Confidence Retrain

## Question

Can probe-derived 32-sample p_correct targets prevent response_confidence collapse in schema-SFT and downstream GRPO?

## Trajectory Position

This session follows the Amendment D schema-response-confidence failure mode:
the model learned JSON reliably, but `response_confidence` collapsed to a single
high value. The next local research step is to repair the target construction
before retraining schema-SFT.

## Summary

Started a governed method revision for probe-scaled response-confidence targets.
The existing schema-SFT projection gave 14,395 ordinary rows
`response_confidence: 0.8` and only 548 ambiguous-middle rows in `[0.4, 0.6]`,
so the constant-0.8 eval collapse is likely a data/target failure rather than
only a GRPO failure.

## Checkpoints

### 001-planning - Probe-Scaled Target Revision

- at: `2026-06-23T09:37:00Z`
- kind: `planning`
- summary: Opened a new session and Amendment E draft to repair schema response-confidence targets using the original 32-sample probe evidence before retraining SFT.
- evidence:
  - `experiment/protocol/AMENDMENT-D-schema-response-confidence.md`
  - `experiment/protocol/AMENDMENT-E-probe-scaled-response-confidence.md`
  - `experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl`
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `docs/sessions/0017 - schema-response-confidence-track.md`
- signals:
    old_schema_sft_rows: 14943
    old_constant_0_8_rows: 14395
    old_middle_rows: 548
    old_low_confidence_sft_rows: 0
    probe_samples_per_question: 32
    old_full_schema_sft_eval_unique_response_confidence_values:
      - 0.8
    old_full_grpo_eval_unique_response_confidence_values:
      - 0.8
- decisions:
  - Treat the constant-0.8 collapse as a method failure in the current Amendment D target projection.
  - Use `p_correct` and `sampled_correct` from the original probe results as the calibration signal for the next schema-SFT dataset.
  - Define response confidence as confidence that the response is appropriate: answer targets use factual confidence, abstention targets use one minus factual confidence.
  - Keep output targets away from exact 0.0/1.0 endpoints.
- next_steps:
  - Patch dataset projection and tests.
  - Regenerate scratch schema datasets and inspect the confidence histogram.
  - Create probe-scaled SFT run configs and smoke before launching a full retrain.

### 002-validation - Probe-Scaled Dataset Projection

- at: `2026-06-23T09:40:26Z`
- kind: `validation`
- summary: Patched and regenerated the schema response-confidence datasets so ordinary rows use probe-derived 32-sample confidence instead of a constant 0.8 target.
- evidence:
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/response_confidence_schema_manifest.json`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl`
- commands:
  - `python -m pytest experiment\phase1\grpo\tests\test_build_schema_response_confidence_datasets.py experiment\phase1\grpo\tests\test_build_grpo_dataset.py experiment\phase1\grpo\tests\test_humility_reward.py -q`
  - `python experiment\phase1\grpo\build_schema_response_confidence_datasets.py --output-dir scratch\schema_response_confidence\qwen3-4b-instruct --include-ambiguous-middle`
- signals:
    tests_passed: 29
    sft:
      rows: 14943
      unique_response_confidence_values: 20
      min_response_confidence: 0.4294
      max_response_confidence: 0.8765
      mean_response_confidence: 0.8387
      high_band_rows: 13773
      mid_band_rows: 1170
      low_band_rows: 0
      probe_scaled_rows: 14943
    dpo_chosen:
      rows: 14943
      unique_response_confidence_values: 20
      high_band_rows: 13773
      mid_band_rows: 1170
      low_band_rows: 0
    dpo_rejected:
      rows: 14943
      unique_response_confidence_values: 21
      high_band_rows: 3
      mid_band_rows: 1170
      low_band_rows: 13770
    kto:
      rows: 29886
      unique_response_confidence_values: 35
      high_band_rows: 13804
      mid_band_rows: 2284
      low_band_rows: 13798
      probe_scaled_rows: 29702
      constant_fallback_rows: 184
- interpretation:
  - The SFT target is no longer a single scalar, but it still contains only appropriate-response examples, so it has high and middle targets rather than low targets.
  - Low-confidence supervision is carried mainly by DPO/KTO rejected/undesirable rows and later by GRPO reward, which avoids SFT directly teaching wrong answers.
  - The 184 KTO fallback rows come from interleaved KTO rows whose source keys were not preserved and whose duplicate normalized questions could not be safely disambiguated; this is small but should be fixed upstream if KTO becomes the main evidence path.
- decisions:
  - Proceed with a probe-scaled schema-SFT smoke before any full retrain.
  - Do not interpret the regenerated scratch datasets as final evidence until a new SFT checkpoint and eval exist.

### 003-execution - Probe-Scaled SFT Smoke And Full Launch

- at: `2026-06-23T09:56:00Z`
- kind: `execution`
- summary: Ran the bounded probe-scaled schema-SFT smoke, fixed a generic SFT post-training logging bug, confirmed clean trainer exit, and launched the full probe-scaled schema-SFT retrain.
- evidence:
  - `experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_smoke_config.py`
  - `experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_full_config.py`
  - `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_smoke/20260623_094821/training_lineage.json`
  - `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_smoke/20260623_094821/capacity_features.json`
  - `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_smoke/20260623_094821/final_model/adapter_model.safetensors`
  - `synaptic-tuner/Trainers/sft/train_sft.py`
- commands:
  - `docker run -d --name eh-probe-scaled-sft-smoke-20260623a ... train_sft.py --config experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_smoke_config.py --max-steps 32 --no-dashboard`
  - `python -m py_compile synaptic-tuner\Trainers\sft\train_sft.py`
  - `docker run -d --name eh-probe-scaled-sft-smoke-20260623b ... train_sft.py --config experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_smoke_config.py --max-steps 2 --no-dashboard`
  - `docker run -d --name eh-probe-scaled-sft-full-20260623a ... train_sft.py --config experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_full_config.py --no-dashboard`
- signals:
    smoke_32_step:
      container: eh-probe-scaled-sft-smoke-20260623a
      exit_status: 1
      trainer_status: completed
      post_training_failure: generic SFT unified-tracking logging import bug after artifacts were saved
      run_dir: scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_smoke/20260623_094821
      final_step: 32
      train_loss: 0.6769
      final_logged_loss: 0.3374
      training_time_seconds: 45.2
      peak_reserved_vram_gb: 12.938
      oom_risk_level: low
      final_model_saved: true
    logging_fix_confirmation:
      container: eh-probe-scaled-sft-smoke-20260623b
      max_steps: 2
      exit_status: 0
      run_dir: scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_smoke/20260623_095431
    full_sft_launch:
      container: eh-probe-scaled-sft-full-20260623a
      status_at_checkpoint: running
      batch_size: 12
      gradient_accumulation_steps: 1
      dataset_rows: 14943
- interpretation:
  - The corrected probe-scaled dataset and SFT config load correctly, the trainer respects explicit CLI `--max-steps`, and the short run shows safe initial VRAM headroom.
  - The smoke exit-1 was not a training/data failure; artifacts were written before a best-effort registry logging path crashed.
  - Batch 12 remains the prudent full-run setting because previous full SFT runs showed later VRAM growth that short smokes can miss.
- decisions:
  - Patch the SFT trainer logging bug generically in the Synaptic Tuner submodule.
  - Continue the full probe-scaled schema-SFT retrain before starting DPO/KTO/GRPO from the new SFT base.
  - After full SFT completes, run a schema eval focused on JSON validity and response-confidence diversity before committing to downstream preference/RL training.

### 004-finding - Probe-Scaled SFT Still Collapses Scalar

- at: `2026-06-23T10:31:00Z`
- kind: `finding`
- summary: Full probe-scaled schema-SFT completed and passed JSON-format eval, but the 192-row mixed SelfAware smoke emitted a single response-confidence value on every row.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_full/20260623_095638/training_lineage.json`
  - `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_full/20260623_095638/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_4b/probe_scaled_schema_sft_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_4b/probe_scaled_schema_sft_seed1__selfaware/scored_rows.jsonl`
- commands:
  - `docker run -d --name eh-probe-scaled-sft-full-20260623a ... train_sft.py --config experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_full_config.py --no-dashboard`
  - `docker run -d --name eh-probe-scaled-sft-eval-smoke-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_local_4b.yaml --live-vllm`
- signals:
    full_sft:
      container: eh-probe-scaled-sft-full-20260623a
      exit_status: 0
      run_dir: scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_full/20260623_095638
      final_step: 1246
      train_loss: 0.2043
      final_logged_loss: 0.1646
      training_time_seconds: 1438.3
      oom_risk_level: critical
      peak_reserved_vram_gb: 29.295
      peak_live_vram_pct_observed: 98.87
    eval_smoke:
      container: eh-probe-scaled-sft-eval-smoke-20260623a
      exit_status: 0
      rows: 192
      known_rows: 97
      unknown_rows: 95
      json_confidence_coverage_pct: 100.0
      unique_response_confidence_values:
        - 0.8765
      mean_response_confidence: 0.8765
      refusal_recall_pct: 88.42
      answer_on_unknown_pct: 11.58
      over_refusal_pct: 69.07
      truthful_pct: 51.04
      retries_exhausted: 0
    target_histogram:
      sft_rows: 14943
      unique_target_values: 20
      dominant_target_value: 0.8765
      dominant_target_rows: 12222
      dominant_target_pct: 81.79
      high_band_rows: 13973
      mid_band_rows: 970
      low_band_rows: 0
- interpretation:
  - Probe scaling by itself did not fix SFT scalar collapse because the SFT target distribution still has a dominant top value.
  - This is a cleaner failure than Amendment D: the scalar moved from constant 0.8 to constant 0.8765, matching the new dominant target, which implicates target imbalance rather than parser or eval behavior.
  - Do not use this SFT as the downstream DPO/KTO/GRPO confidence-learning base unless the specific question is whether preference/RL can rescue a collapsed SFT scalar.
- decisions:
  - Pause downstream SFT->DPO/KTO/GRPO launches from this checkpoint.
  - Add a reusable balanced SFT projection so the SFT stage cannot minimize loss by emitting the modal response-confidence value.
  - Keep this run as Amendment E v1 evidence for target-imbalance failure.

### 005-method-note - UaIT-Style Contrastive Target Shaping

- at: `2026-06-23T10:48:00Z`
- kind: `method-note`
- summary: Paused the row-cap balancing direction and captured the preferred method as a KG note: full-size UaIT-style contrastive response-confidence target shaping.
- evidence:
  - `library/concepts/methods/contrastive-response-confidence-target-shaping.md`
  - `library/concepts/methods/uncertainty-aware-instruction-tuning.md`
  - `library/notes/2024.emnlp-main.1205--llms-learn-uncertainty-uait.md`
  - `library/pdfs/2024.emnlp-main.1205.pdf`
- commands:
  - `bin\search.cmd UAIT uncertainty instruction tuning confidence dataset --limit 10`
  - `pdftotext -layout library\pdfs\2024.emnlp-main.1205.pdf - | Select-String -Pattern "Uncertainty-aware|self-training|training data|probabilistic|confidence|sampling|temperature|dataset|instruction" -Context 2,3`
  - `python .agents\skills\knowledge-graph\scripts\validate_kg_relationships.py --root F:\Code\Epistemic-Humility-Research\library F:\Code\Epistemic-Humility-Research\library\concepts\methods\contrastive-response-confidence-target-shaping.md`
- signals:
    kg_note_validated: true
    validator_output: OK 1 graph notes validated
    uait_training_examples:
      source: generated answers plus probabilistic/multi-sampling uncertainty estimate
      filter: keep correct/high-confidence and incorrect/low-confidence examples
      reported_train_samples:
        llama2: 31391
        mistral: 25362
      finetuning:
        epochs: 4
        batch_size: 32
        learning_rate: 2.0e-5
        lora_r: 64
        lora_alpha: 16
        lora_dropout: 0.05
- interpretation:
  - UaIT's key design lesson is contrast, not dataset row reduction: supervised data includes low-confidence incorrect answers as well as high-confidence correct answers.
  - For our response-confidence track, the next dataset should preserve rows where possible and mathematically shape targets to avoid a dominant scalar.
  - Random jitter is less desirable than deterministic transforms because deterministic transforms are auditable and reproducible.
- decisions:
  - Do not launch the balanced row-cap SFT without further review.
  - Prefer a full-size contrastive dataset revision with high targets for appropriate responses, low targets for wrong answers/over-refusals, middle targets for ambiguous rows, and deterministic band spreading or quantile mapping to prevent modal collapse.

### 006-semantic-clarification - IDK High Confidence And Ambiguous Answers

- at: `2026-06-23T10:55:00Z`
- kind: `semantic-clarification`
- summary: Clarified response-confidence semantics before the next dataset revision.
- evidence:
  - `library/concepts/methods/contrastive-response-confidence-target-shaping.md`
  - `experiment/protocol/AMENDMENT-E-probe-scaled-response-confidence.md`
- interpretation:
  - High `response_confidence` means the response is appropriate, not that the model gave a factual answer.
  - A correct "I don't know" on a true unknown should therefore be high confidence.
  - Ambiguous model-specific rows should not automatically become abstentions; answering can still be appropriate, but the answer should carry low-to-middle confidence to express uncertainty.
- decisions:
  - Preserve this distinction in the next target-construction patch.

### 007-validation - Contrastive SFT Dataset Revision

- at: `2026-06-23T11:08:00Z`
- kind: `validation`
- summary: Replaced the row-cap balancing idea with a full-size contrastive SFT projection that mathematically spreads confidence targets by response appropriateness role.
- evidence:
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/response_confidence_schema_manifest.json`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive.jsonl`
  - `experiment/protocol/AMENDMENT-E-probe-scaled-response-confidence.md`
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_smoke_config.py`
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_full_config.py`
- commands:
  - `python experiment\phase1\grpo\build_schema_response_confidence_datasets.py --output-dir scratch\schema_response_confidence\qwen3-4b-instruct --include-ambiguous-middle`
  - `python -m pytest experiment\phase1\grpo\tests\test_build_schema_response_confidence_datasets.py experiment\phase1\grpo\tests\test_build_grpo_dataset.py experiment\phase1\grpo\tests\test_humility_reward.py -q`
- signals:
    tests_passed: 31
    sft_contrastive:
      rows: 29338
      appropriate_rows: 14395
      inappropriate_rows: 14395
      ambiguous_answer_rows: 548
      unique_response_confidence_values: 4986
      min_response_confidence: 0.1
      max_response_confidence: 0.9
      mean_response_confidence: 0.512539
      high_band_rows: 14395
      low_band_rows: 14394
      mid_band_rows: 549
      largest_exact_target_count: 20
      formula: deterministic_uait_style_band_spread_v1
- interpretation:
  - The v1 probe-scaled-only dataset failed because one modal value covered 81.79% of SFT rows; the v2 contrastive dataset removes that shortcut without discarding ordinary rows.
  - High response confidence continues to mean confidence that the response is appropriate, so true-unknown abstentions are high confidence and known-question over-refusals are low confidence.
  - Ambiguous/discard rows remain answer-supervised with middle confidence instead of being turned into abstention examples.
- decisions:
  - Use `sft_response_confidence_train_contrastive.jsonl` for the next local seed-1 schema-SFT smoke/full rerun.
  - Keep the failed v1 probe-scaled SFT run as target-imbalance evidence, not as the base for downstream DPO/KTO/GRPO.

### 008-launch - Contrastive SFT Smoke And Full Launch

- at: `2026-06-23T11:04:30Z`
- kind: `launch`
- summary: Ran a 32-step contrastive schema-SFT smoke successfully, then launched the full seed-1 contrastive schema-SFT rerun.
- evidence:
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_smoke_config.py`
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_full_config.py`
  - `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_smoke/20260623_110043/training_lineage.json`
  - `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_smoke/20260623_110043/capacity_features.json`
  - `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_smoke/20260623_110043/final_model/adapter_model.safetensors`
- commands:
  - `docker run -d --name eh-contrastive-sft-smoke-20260623a ... train_sft.py --config experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_smoke_config.py --max-steps 32 --no-dashboard --quiet`
  - `docker run -d --name eh-contrastive-sft-full-20260623a ... train_sft.py --config experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_full_config.py --no-dashboard --quiet`
- signals:
    smoke:
      container: eh-contrastive-sft-smoke-20260623a
      exit_status: 0
      run_dir: scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_smoke/20260623_110043
      dataset_rows: 29338
      batch_size: 12
      max_steps: 32
      final_step: 32
      train_loss: 0.880669
      final_logged_loss: 0.5805
      training_time_seconds: 54.4
      oom_risk_level: critical
      peak_live_vram_pct_observed: 98.74
    full_launch:
      container: eh-contrastive-sft-full-20260623a
      status_at_checkpoint: starting
      dataset_rows: 29338
      batch_size: 10
      gradient_accumulation_steps: 1
      rationale_for_batch: smoke batch-12 capacity profile was critical, so full run uses batch 10 rather than increasing throughput.
- interpretation:
  - The contrastive file loads under the explicit tokenized SFT contract and trains for a bounded smoke without schema/data failures.
  - The smoke loss moved normally, but local VRAM telemetry again reached the critical range, so batch-size expansion is not justified for the full run.
- next_steps:
  - Monitor the full SFT run through tokenization, training start, and completion.
  - Evaluate the resulting checkpoint for JSON validity and response-confidence diversity before launching downstream DPO/KTO/GRPO.

### 009-correction - Clean Mainline Separated From Contrastive Exploratory Branch

- at: `2026-06-23T11:48:00Z`
- kind: `correction`
- summary: Clarified that the currently running contrastive SFT is exploratory scalar-movement evidence, while the preferred mainline is clean SFT followed by DPO/KTO/GRPO for contrastive accuracy tuning.
- evidence:
  - `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
  - `experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/response_confidence_schema_manifest.json`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_clean.jsonl`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive.jsonl`
  - `experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_smoke_config.py`
  - `experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_full_config.py`
  - `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`
  - `experiment/protocol/AMENDMENT-E-probe-scaled-response-confidence.md`
- commands:
  - `python experiment\phase1\grpo\build_schema_response_confidence_datasets.py --output-dir scratch\schema_response_confidence\qwen3-4b-instruct --include-ambiguous-middle`
  - `python -m pytest experiment\phase1\grpo\tests\test_build_schema_response_confidence_datasets.py experiment\phase1\grpo\tests\test_build_grpo_dataset.py experiment\phase1\grpo\tests\test_humility_reward.py -q`
- signals:
    tests_passed: 33
    clean_sft:
      rows: 14943
      known_appropriate_rows: 7981
      unknown_appropriate_rows: 6414
      ambiguous_answer_rows: 548
      unique_response_confidence_values: 2489
      min_response_confidence: 0.3508
      max_response_confidence: 0.9
      mean_response_confidence: 0.78834
      largest_exact_target_count: 17
      supervises_rejected_completions: false
    contrastive_sft:
      rows: 29338
      status: exploratory_scalar_movement_branch
      supervises_rejected_completions: true
    downstream_preference_data:
      dpo_rows: 14943
      kto_rows: 29886
      role: accuracy_and_calibration_contrast_after_clean_sft
- interpretation:
  - The questions are not invented; they come from the frozen TriviaQA/probe split, with known/unknown/ambiguous labels from the model's 32-sample probe behavior and source gold answers where applicable.
  - The exploratory contrastive SFT branch uses rejected completions as low-confidence supervised targets, usually model-generated wrong answers or over-refusals from the existing DPO/KTO construction. This tests whether the scalar can move but is not the clean format/style SFT control.
  - The clean SFT mainline better matches the intended stage separation: SFT teaches format and broadly appropriate response-confidence expression; DPO/KTO/GRPO then tune accuracy, abstention, and calibration using contrastive signals.
- decisions:
  - Leave `eh-contrastive-sft-full-20260623a` running as exploratory evidence.
  - Do not use the contrastive SFT checkpoint as the default downstream DPO/KTO/GRPO base.
  - After the exploratory branch is evaluated, run clean SFT from `sft_response_confidence_train_clean.jsonl`, merge it, sanity-eval the merged model, then launch DPO/KTO/GRPO from that merged clean-SFT base.

### 010-recovery-result - Interrupted Contrastive SFT Checkpoint 1500 Eval

- at: `2026-06-23T12:24:00Z`
- kind: `recovery`
- summary: After a host restart interrupted the exploratory contrastive SFT run, checkpoint-1500 was usable and a mixed SelfAware smoke showed scalar movement but poor behavior.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260623_110457/checkpoints/checkpoint-1500/adapter_model.safetensors`
  - `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260623_110457/logs/training_20260623_110527.jsonl`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_contrastive_sft_seed1_checkpoint1500_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_contrastive_sft_seed1_checkpoint1500_smoke_4b/contrastive_schema_sft_seed1_checkpoint1500__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_contrastive_sft_seed1_checkpoint1500_smoke_4b/contrastive_schema_sft_seed1_checkpoint1500__selfaware/scored_rows.jsonl`
- commands:
  - `docker run -d --name eh-contrastive-sft-ckpt1500-eval-smoke-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_contrastive_sft_seed1_checkpoint1500_smoke_local_4b.yaml --live-vllm`
- signals:
    interrupted_training:
      container: eh-contrastive-sft-full-20260623a
      exit_status_after_restart: 255
      last_logged_step: 1700
      total_steps: 2934
      completed_epoch_fraction: 0.5794
      checkpoints_present:
        - checkpoint-1000
        - checkpoint-1500
      final_model_present: false
      training_lineage_present: false
      capacity_features_present: false
    checkpoint1500_eval:
      container: eh-contrastive-sft-ckpt1500-eval-smoke-20260623a
      exit_status: 0
      rows: 192
      known_rows: 97
      unknown_rows: 95
      json_confidence_coverage_pct: 99.48
      unique_response_confidence_values: 31
      min_response_confidence: 0.111
      max_response_confidence: 0.8222
      mean_response_confidence: 0.456674
      refusal_recall_pct: 70.53
      answer_on_unknown_pct: 29.47
      over_refusal_pct: 40.21
      correct_on_known_pct: 17.24
      truthful_pct: 40.1
    category_confidence_means:
      known_wrong_answer: 0.2799
      known_correct_answer: 0.4436
      known_over_refusal: 0.4654
      unknown_answer: 0.2455
      unknown_refusal: 0.6682
- interpretation:
  - The exploratory contrastive SFT did answer the narrow question: supervised high/low contrast can break constant-scalar collapse before a full epoch.
  - It is not a good base to continue. Known-question accuracy and over-refusal are poor, and confidence is not yet cleanly aligned for known correct answers versus known over-refusals.
  - This supports moving to the clean SFT mainline rather than resuming or finishing the contrastive SFT branch.
- decisions:
  - Do not resume `eh-contrastive-sft-full-20260623a`.
  - Keep checkpoint-1500 and its eval as exploratory evidence that the scalar is movable.
  - Next training target should be `schema_clean_sft` using `sft_response_confidence_train_clean.jsonl`.

### 011-gate-validation - Clean SFT Smoke Caught Max-Steps Wiring Bug

- at: `2026-06-23T12:36:00Z`
- kind: `gate`
- summary: The first clean-SFT smoke was stopped because config-level `max_steps` was ignored; the generic SFT trainer was patched and the corrected smoke exited cleanly at 32 steps.
- evidence:
  - `experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_smoke_config.py`
  - `synaptic-tuner/Trainers/sft/train_sft.py`
  - `synaptic-tuner/Trainers/sft/configs/config_loader.py`
  - `synaptic-tuner/tests/trainers/sft/test_train_sft_source.py`
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_smoke/20260623_123251/training_lineage.json`
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_smoke/20260623_123251/capacity_features.json`
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_smoke/20260623_123251/final_model/adapter_model.safetensors`
- commands:
  - `docker run -d --name eh-clean-sft-smoke-20260623a ... sft_schema_clean_response_confidence_seed1_smoke_config.py --no-dashboard --quiet`
  - `docker stop eh-clean-sft-smoke-20260623a`
  - `python -m pytest synaptic-tuner\tests\trainers\sft\test_train_sft_source.py -q`
  - `python -m py_compile synaptic-tuner\Trainers\sft\train_sft.py synaptic-tuner\Trainers\sft\configs\config_loader.py experiment\phase1\grpo\configs\sft_schema_clean_response_confidence_seed1_smoke_config.py`
  - `docker run -d --name eh-clean-sft-smoke-20260623b ... sft_schema_clean_response_confidence_seed1_smoke_config.py --no-dashboard --quiet`
- signals:
    bad_smoke:
      container: eh-clean-sft-smoke-20260623a
      intended_max_steps: 32
      observed_total_steps: 1246
      action: stopped
    fix:
      generic_trainer_change: config_level_max_steps_honored_with_cli_override_precedence
      sft_source_tests_passed: 4
      py_compile_passed: true
    corrected_smoke:
      container: eh-clean-sft-smoke-20260623b
      exit_status: 0
      total_steps: 32
      train_runtime_seconds: 52.8837
      train_loss: 0.878419354557991
      oom_risk_level: low
      max_gpu_memory_reserved_gb: 12.938
      final_model_present: true
      training_lineage_present: true
      capacity_features_present: true
- interpretation:
  - The clean SFT data/trainer path is viable, but smoke gates must verify the trainer's resolved total step count rather than trusting the config alone.
  - The generic SFT fix is reusable for any future Python/YAML config that sets `training.max_steps`; CLI `--max-steps` remains the explicit override.
- decisions:
  - Proceed to the real clean SFT seed-1 full run at batch 10 only after this corrected smoke pass.
  - Continue to stop and inspect if a run's resolved step count, artifact path, or early capacity profile contradicts the intended gate.

### 012-result - Clean SFT Full Run And Merge Gate

- at: `2026-06-23T14:58:00Z`
- kind: `training-result`
- summary: Clean response-confidence SFT seed 1 completed, merged successfully, and passed a 192-row mixed SelfAware behavioral smoke.
- evidence:
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/final_model/adapter_model.safetensors`
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/training_lineage.json`
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/capacity_features.json`
  - `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit/`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_smoke_4b/clean_schema_sft_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_smoke_4b/clean_schema_sft_seed1_merged__selfaware/metrics.json`
- signals:
    adapter_eval:
      rows: 192
      known_rows: 97
      unknown_rows: 95
      json_confidence_coverage_pct: 100.0
      refusal_recall_pct: 87.37
      answer_on_unknown_pct: 12.63
      over_refusal_pct: 69.07
      correct_on_known_pct: 33.33
      truthful_pct: 48.44
      mean_response_confidence: 0.7822
    merged_eval:
      rows: 192
      known_rows: 97
      unknown_rows: 95
      json_confidence_coverage_pct: 100.0
      refusal_recall_pct: 86.32
      answer_on_unknown_pct: 13.68
      over_refusal_pct: 63.92
      correct_on_known_pct: 37.14
      truthful_pct: 49.48
      mean_response_confidence: 0.7562
- interpretation:
  - Clean SFT learned the schema and much of the abstention behavior, but it remains heavily over-refusal-biased on known questions.
  - The merged checkpoint is semantically plausible relative to the adapter eval, so it is acceptable as the base for preference/RL follow-on runs.
  - Confidence moved away from exact endpoint collapse, but the scalar is still not a strong calibration signal.
- decisions:
  - Use the merged clean SFT checkpoint as the base for DPO/KTO/GRPO.
  - Treat preference/RL follow-ons as attempts to reduce known-question over-refusal without losing unknown-question refusal.

### 013-invalidated - Clean SFT -> DPO Seed 1 Smoke Used Wrong Eval Base

- at: `2026-06-23T15:32:00Z`
- kind: `invalidated-eval`
- summary: DPO seed 1 from the merged clean-SFT base completed cleanly, but the first behavioral smoke is invalidated because the eval loaded the DPO adapter on the original Qwen base instead of the merged clean-SFT base.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed1_full/20260623_132930/final_model/adapter_model.safetensors`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed1_full/20260623_132930/training_lineage.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed1_full/20260623_132930/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_smoke_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_smoke_4b/clean_schema_sft_dpo_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_smoke_4b/clean_schema_sft_dpo_seed1__selfaware/scored_rows.jsonl`
- signals:
    training:
      container: eh-clean-sft-dpo-seed1-full-20260623a
      exit_status: 0
      train_examples: 14943
      batch_size: 2
      gradient_accumulation_steps: 4
      effective_batch_size: 8
      learning_rate: 0.000005
      beta: 0.1
      epochs: 1
      final_step: 1868
      runtime_seconds: 6111.7
      final_loss: 0.040386
      peak_reserved_vram_gb: 11.203
      peak_reserved_vram_pct: 46.68
      min_reserved_headroom_gb: 12.796
      oom_risk_level: low
    eval:
      status: invalidated_base_adapter_mismatch
      expected_model_name: /workspace/repo/scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit
      observed_model_name: unsloth/Qwen3-4B-bnb-4bit
      rows: 192
      known_rows: 97
      unknown_rows: 95
      json_confidence_coverage_pct: 100.0
      refusal_recall_pct: 96.84
      answer_on_unknown_pct: 3.16
      over_refusal_pct: 84.54
      refusal_rate_pct: 90.62
      correct_on_known_pct: 33.33
      truthful_pct: 50.52
      mean_response_confidence: 0.927083
      confidence_values_top:
        "0.95": 150
        "0.9": 32
        "0.8": 5
        "1.0": 2
        "0.0": 2
        "0.7": 1
      answer_text_top: "I don't know the answer"
      answer_text_top_count: 174
      known_refused_count: 82
      unknown_answered_count: 3
    data_audit:
      dpo_rows: 14943
      source_label_known: 7981
      source_label_unknown: 6414
      source_label_discard_ambiguous: 548
      first_200_rows: "known=102, unknown=98"
      later_windows: "mixed known/unknown; no obvious unknown-only front-loading"
      known_chosen_confidence_avg: 0.8334
      known_rejected_confidence_avg: 0.1666
      unknown_chosen_confidence_avg: 0.8765
      unknown_rejected_confidence_avg: 0.1239
- interpretation:
  - The DPO trainer completed, but this eval is not valid DPO behavioral evidence because the adapter was applied to the wrong base.
  - The confident-abstention pattern is still useful as an audit trigger, but it must not be cited as a DPO objective failure until rerun with the merged clean-SFT base as `model_name`.
  - A quick generated-file audit did not show a trivial label-order bug: known rows are the majority and early windows are mixed. The failure is more likely objective/data-strength related than a simple ordering accident.
- decisions:
  - Rerun a corrected 192-row DPO smoke with `model_name` set to the merged clean-SFT checkpoint and `adapter` set to the DPO final model before interpreting DPO behavior.
  - If DPO is rerun for throughput, batch can likely be increased from batch 2 / accumulation 4 because this full run peaked at only 11.203 GB reserved VRAM, but the next run must still gate on behavior, not just low OOM risk.
  - Pause after the full SFT baseline because the user needs to restart the computer; do not launch corrected DPO eval until after restart.

### 014-result - Clean SFT Merged Full SelfAware Eval

- at: `2026-06-23T18:16:00Z`
- kind: `eval-result`
- summary: Full SelfAware eval completed for the merged clean schema-SFT seed-1 checkpoint; this is the valid full SFT baseline for the next corrected DPO/KTO/GRPO comparisons.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b/clean_schema_sft_merged_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b/clean_schema_sft_merged_seed1__selfaware/scored_rows.jsonl`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b/comparisons/summary_table.csv`
- commands:
  - `docker run -d --name eh-clean-sft-merged-full-eval-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_local_4b.yaml --live-vllm`
- signals:
    container: eh-clean-sft-merged-full-eval-20260623a
    exit_status: 0
    config_sha: 79a7d4265ba2b328
    rows: 3369
    known_rows: 2337
    unknown_rows: 1032
    json_confidence_coverage_pct: 100.0
    thinking_tag_hits: 0
    refusal_recall_pct: 87.02
    answer_on_unknown_pct: 12.98
    over_refusal_pct: 57.51
    refusal_rate_pct: 66.55
    correct_on_known_pct: 47.23
    truthful_pct: 40.58
    truthful_ci_95:
      lo: 38.94
      hi: 42.06
    mean_response_confidence: 0.748489
    known_confidence_mean: 0.746
    unknown_confidence_mean: 0.754
    dominant_confidence_values:
      "0.711": 1428
      "0.811": 350
      "0.714": 220
      "0.8116": 167
      "0.8016": 140
    dominant_answer_texts:
      "I don't know the answer to that, but I'd be glad to help with something else.": 1391
      "I don't know the answer to that question.": 699
      "I'm sorry, but I don't know the answer here.": 80
- interpretation:
  - The clean SFT model is still strongly over-refusal-biased on the full SelfAware distribution: it refuses 57.51% of known rows while correctly refusing 87.02% of unknown rows.
  - The full eval confirms the 192-row smoke directionally but gives a better estimate: known accuracy retention is 47.23%, and truthful rate is 40.58%.
  - The response-confidence scalar is schema-complete and non-endpoint, but it remains poorly discriminative: known and unknown mean confidence are nearly identical.
- decisions:
  - Use this full eval as the SFT baseline for Amendment E clean-schema follow-on comparisons.
  - Next action after restart: create/run corrected DPO smoke using the merged clean-SFT base plus the DPO adapter, then proceed to full DPO only if the smoke is wired cleanly.

### 015-result - Corrected Clean SFT -> DPO Full SelfAware Eval

- at: `2026-06-23T19:16:00Z`
- kind: `eval-result`
- summary: Corrected-base DPO eval completed. The DPO adapter is validly evaluated on the merged clean-SFT base, but behavior is essentially flat versus clean SFT with higher stated confidence and no meaningful calibration gain.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_smoke_local_4b.yaml`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_smoke_4b/clean_schema_sft_dpo_seed1_corrected_base__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_4b/clean_schema_sft_dpo_seed1_corrected_base__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_4b/clean_schema_sft_dpo_seed1_corrected_base__selfaware/scored_rows.jsonl`
- commands:
  - `docker run -d --name eh-clean-sft-dpo-corrected-smoke-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_smoke_local_4b.yaml --live-vllm`
  - `docker run -d --name eh-clean-sft-dpo-corrected-full-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_local_4b.yaml --live-vllm`
- signals:
    corrected_smoke:
      rows: 192
      known_rows: 97
      unknown_rows: 95
      config_sha: e3d4e98dc5c981f4
      json_confidence_coverage_pct: 100.0
      thinking_tag_hits: 0
      refusal_recall_pct: 87.37
      answer_on_unknown_pct: 12.63
      over_refusal_pct: 62.89
      correct_on_known_pct: 36.11
      truthful_pct: 50.0
      mean_response_confidence: 0.819805
    corrected_full:
      container: eh-clean-sft-dpo-corrected-full-20260623a
      exit_status: 0
      rows: 3369
      known_rows: 2337
      unknown_rows: 1032
      config_sha: 070f526aa86d21ab
      json_confidence_coverage_pct: 100.0
      thinking_tag_hits: 0
      refusal_recall_pct: 87.11
      answer_on_unknown_pct: 12.89
      over_refusal_pct: 56.18
      refusal_rate_pct: 65.66
      correct_on_known_pct: 46.09
      truthful_pct: 40.69
      truthful_ci_95:
        lo: 39.00
        hi: 42.36
      mean_response_confidence: 0.812083
      known_confidence_mean: 0.8055
      unknown_confidence_mean: 0.8269
    full_delta_vs_clean_sft:
      truthful_pct: "+0.11"
      refusal_recall_pct: "+0.09"
      answer_on_unknown_pct: "-0.09"
      over_refusal_pct: "-1.33"
      correct_on_known_pct: "-1.14"
      mean_response_confidence: "+0.063594"
      brier_vs_response_appropriateness: "+0.044028"
    answer_text_concentration:
      sft_top_abstention: "I don't know the answer to that, but I'd be glad to help with something else."
      sft_top_abstention_count: 1391
      dpo_top_abstention: "I don't know the answer to that question."
      dpo_top_abstention_count: 1812
- interpretation:
  - The original catastrophic DPO smoke was indeed confounded by the wrong base. With the corrected base, DPO does not collapse; it is mostly behaviorally inert.
  - Full DPO slightly reduces known-row over-refusal count (1344 -> 1313) and unknown answering (134 -> 133), but it also slightly lowers correct-on-known percentage and leaves truthful rate effectively unchanged within the bootstrap CI.
  - DPO increases stated confidence substantially without improving response-appropriateness calibration; this is a negative signal for the current DPO objective as a confidence-calibration tool.
  - The response style concentrates further around one canonical abstention phrase, suggesting preference tuning may be regularizing the output form more than changing the epistemic decision boundary.
- decisions:
  - Treat clean SFT -> DPO seed 1 as a valid but weak/mostly-inert result, not a failure caused by eval wiring.
  - Next highest-value follow-on is KTO from the same merged clean-SFT base or GRPO with the revised reward, using the full clean-SFT baseline and corrected DPO result as comparators.
  - If rerunning DPO later, change objective/hyperparameters before spending a larger batch rerun; batch headroom is available but the behavioral target did not move enough to justify repeating the same run.

### 016-progress - Clean SFT -> KTO Seed 1 Launched

- at: `2026-06-23T20:05:00Z`
- kind: `train-progress`
- summary: Clean schema SFT -> KTO seed 1 is running from the merged clean-SFT base with the checked-in runbook hyperparameters. An earlier launch was stopped before meaningful compute because it used stale handoff-summary values rather than the runbook values.
- evidence:
  - `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/logs/training_20260623_200010.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/checkpoints/checkpoint-100/trainer_state.json`
- commands:
  - `docker stop eh-clean-sft-kto-seed1-full-20260623b`
  - `docker run -d --name eh-clean-sft-kto-seed1-full-20260623c ... train_kto.py --model-name /workspace/repo/scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit --local-file /workspace/repo/scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl --output-root /workspace/repo/scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full --run-timestamp 20260623_200200 --seed 1 --batch-size 12 --gradient-accumulation 1 --learning-rate 1e-6 --num-epochs 1 --beta 0.1 --max-seq-length 2048 --lora-r 32 --lora-alpha 64 --lora-dropout 0.05`
- signals:
    valid_container: eh-clean-sft-kto-seed1-full-20260623c
    aborted_container: eh-clean-sft-kto-seed1-full-20260623b
    aborted_reason: stale_handoff_summary_hyperparameters
    train_rows: 29886
    desirable_rows: 14943
    undesirable_rows: 14943
    base_model: scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit
    batch_size: 12
    gradient_accumulation: 1
    learning_rate: 1e-6
    beta: 0.1
    lora_r: 32
    lora_alpha: 64
    checkpoint_confirmed: 100
    total_steps: 2491
    observed_steps_per_second: 0.38
    projected_total_runtime_minutes: 109
    max_gpu_memory_reserved_gb_at_step_100: 12.605
    oom_risk_level_at_step_100: low
- interpretation:
  - The corrected KTO run is live and capacity-safe so far; batch 12 is not showing the high/critical VRAM pattern seen in earlier response-confidence KTO probes.
  - The KTO dataset is balanced and the logged samples match the intended preference contrast, but the DPO result raises a live hypothesis that preference tuning may mostly regularize response form unless the objective creates a sharper epistemic decision-boundary signal.
- decisions:
  - Let KTO continue unless VRAM enters high/critical risk, metrics diverge, or the container exits nonzero.
  - When KTO completes, run a corrected-base KTO smoke eval before any full eval, using the merged clean-SFT base plus the KTO adapter.
  - Treat handoff summaries as orientation only for hyperparameters; verify against the checked-in runbook before launching governed cells.

### 017-result - Corrected Clean SFT -> KTO Full SelfAware Eval

- at: `2026-06-23T22:25:00Z`
- kind: `eval-result`
- summary: Clean schema SFT -> KTO seed 1 completed and was evaluated on the merged clean-SFT base. KTO moved behavior more than DPO, but mostly by reducing refusal overall, increasing unknown answering, and increasing stated confidence; it did not improve truthful response selection.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/final_model`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/training_lineage.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_smoke_local_4b.yaml`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_smoke_4b/clean_schema_sft_kto_seed1_corrected_base__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_4b/clean_schema_sft_kto_seed1_corrected_base__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_4b/clean_schema_sft_kto_seed1_corrected_base__selfaware/scored_rows.jsonl`
- commands:
  - `docker run -d --name eh-clean-sft-kto-corrected-smoke-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_smoke_local_4b.yaml --live-vllm`
  - `docker run -d --name eh-clean-sft-kto-corrected-full-20260623a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_local_4b.yaml --live-vllm`
- signals:
    training:
      container: eh-clean-sft-kto-seed1-full-20260623c
      exit_status: 0
      train_runtime_seconds: 6580.4427
      train_steps: 2491
      train_steps_per_second: 0.379
      train_loss: 0.0950038
      final_step_loss_near_end: 0.0035
      final_reward_margin_near_end: 16.345
      peak_reserved_vram_gb: 21.447
      final_oom_risk_level: moderate
    smoke_eval:
      container: eh-clean-sft-kto-corrected-smoke-20260623a
      exit_status: 0
      rows: 192
      known_rows: 97
      unknown_rows: 95
      config_sha: ab1c68a7744be326
      json_confidence_coverage_pct: 100.0
      refusal_recall_pct: 83.16
      answer_on_unknown_pct: 16.84
      over_refusal_pct: 57.73
      correct_on_known_pct: 36.59
      truthful_pct: 48.96
      mean_response_confidence: 0.852319
    full_eval:
      container: eh-clean-sft-kto-corrected-full-20260623a
      exit_status: 0
      rows: 3369
      known_rows: 2337
      unknown_rows: 1032
      config_sha: 7f3b47cb745b180f
      json_confidence_coverage_pct: 100.0
      thinking_tag_hits: 0
      refusal_recall_pct: 81.01
      answer_on_unknown_pct: 18.99
      over_refusal_pct: 52.37
      refusal_rate_pct: 61.15
      correct_on_known_pct: 44.03
      truthful_pct: 39.36
      mean_response_confidence: 0.852712
      known_confidence_mean: 0.8507
      unknown_confidence_mean: 0.8572
      refused_confidence_mean: 0.8642
      answered_confidence_mean: 0.8346
    full_delta_vs_clean_sft:
      truthful_pct: "-1.22"
      refusal_recall_pct: "-6.01"
      answer_on_unknown_pct: "+6.01"
      over_refusal_pct: "-5.14"
      correct_on_known_pct: "-3.20"
      mean_response_confidence: "+0.104223"
      brier_vs_response_appropriateness: "+0.087923"
    full_delta_vs_clean_sft_dpo:
      truthful_pct: "-1.33"
      refusal_recall_pct: "-6.10"
      answer_on_unknown_pct: "+6.10"
      over_refusal_pct: "-3.81"
      correct_on_known_pct: "-2.06"
      mean_response_confidence: "+0.040629"
      brier_vs_response_appropriateness: "+0.043895"
    answer_text_concentration:
      kto_top_abstention: "I don't know the answer to that question."
      kto_top_abstention_count: 1888
      kto_top_generated_answer: '{"answer": "I don''t know the answer to that question.","response_confidence": 0.8666}'
      kto_top_generated_answer_count: 1329
- interpretation:
  - KTO is not behaviorally inert in the way DPO mostly was. It shifted the refusal boundary toward answering more often.
  - The direction is not aligned with the epistemic-humility target: it answered 196 unknown rows versus 134 for SFT and 133 for DPO, while known-row correctness also fell.
  - KTO's training objective separated preferred/rejected completions strongly, but the eval suggests that separation did not become better know/unknown discrimination. It appears to harden response form and confidence while loosening abstention.
  - Confidence got worse for response appropriateness despite being schema-complete and non-endpoint; KTO made both known and unknown means high and close together.
- decisions:
  - Treat this KTO seed 1 as a valid negative/diagnostic result, not an infrastructure failure.
  - Do not repeat the same KTO objective unchanged merely with more batch. If KTO is revisited, change the preference construction or reward target so unknown-answer penalties and known-answer rewards create a sharper decision-boundary signal.
  - The next highest-value training branch remains revised GRPO from the clean SFT base, because the reward can directly encode correctness, refusal appropriateness, and confidence bands instead of relying on static KTO labels.

### 018-progress - Clean SFT -> GRPO Seed 1 Smoke Passed, Full Run Launched

- at: `2026-06-23T23:40:00Z`
- kind: `train-progress`
- summary: Revised GRPO was launched from the merged clean-SFT base after a local smoke confirmed nonzero reward variance, valid reward parsing, low OOM risk, and healthy capacity at the planned batch/generation settings.
- evidence:
  - `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_smoke.yaml`
  - `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_full.yaml`
  - `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_smoke/20260623_232511/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_smoke/20260623_232511/logs/training_20260623_232558.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_smoke/reward_debug_20260623a.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/logs/training_20260623_233413.jsonl`
- commands:
  - `python -m pytest experiment\phase1\grpo\tests\test_humility_reward.py experiment\phase1\grpo\tests\test_build_schema_response_confidence_datasets.py -q`
  - `docker run -d --name eh-clean-sft-grpo-smoke-20260623a ... train_grpo.py --config experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_smoke.yaml`
  - `docker run -d --name eh-clean-sft-grpo-full-20260623a ... train_grpo.py --config experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_full.yaml`
- signals:
    tests:
      grpo_reward_and_dataset_tests: "30 passed"
    dataset:
      train_rows: 14888
      known_rows: 7981
      unknown_rows: 6414
      ambiguous_rows: 493
    smoke_training:
      container: eh-clean-sft-grpo-smoke-20260623a
      exit_status: 0
      run_dir: scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_smoke/20260623_232511
      train_steps: 12
      runtime_seconds: 138.9583
      steps_per_second: 0.086
      final_loss: 0.0042
      peak_reserved_vram_gb: 10.914
      oom_risk_level: low
      reward_std_nonzero_steps: 12
      max_frac_reward_zero_std: 0.625
      max_clipped_ratio: 0.03125
      reward_debug_rows: 384
      reward_debug_valid_json_rows: 374
      reward_debug_invalid_json_rows: 10
      reward_debug_reward_min: -2.0
      reward_debug_reward_max: 1.5
      reward_debug_reward_mean: -0.0369
    full_training:
      container: eh-clean-sft-grpo-full-20260623a
      status_at_first_metric: running
      run_dir: scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309
      base_model: scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit
      total_steps: 1861
      first_metric_step: 25
      first_metric_steps_per_second: 0.08
      first_metric_elapsed_seconds: 312.979
      first_metric_reward_std: 1.03475
      first_metric_combined_reward_std: 1.41361
      first_metric_frac_reward_zero_std: 0.16
      first_metric_clipped_ratio: 0.005
      first_metric_gpu_reserved_gb: 10.914
      first_metric_oom_risk_level: low
- interpretation:
  - The GRPO reward path is live: reward variance is not collapsed, malformed schema outputs are visible but not dominant, and the reward span is exercising both positive and negative cases.
  - The smoke did not show the prior confidence-collapse failure mode at launch; response confidence is still being parsed and shaped by the reward.
  - Capacity is safe at batch 32 with 4 generations on the RTX 3090, so the full run is worth continuing unless later metrics show reward collapse, schema collapse, or VRAM risk.
- decisions:
  - Continue the full GRPO run from the clean merged SFT base.
  - After completion, inspect final artifacts and capacity, then run a corrected-base GRPO smoke eval before any full eval.
  - Compare GRPO primarily against clean SFT, clean SFT -> DPO, and clean SFT -> KTO on unknown-answering, known over-refusal, truthful response selection, and confidence calibration.

### 019-progress - Clean SFT -> GRPO Seed 1 Full Heartbeat

- at: `2026-06-24T01:15:00Z`
- kind: `train-progress`
- summary: Full GRPO remains healthy at the first long heartbeat. Reward variance remains nonzero, schema-length clipping remains low, and VRAM risk remains low.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/logs/training_20260623_233413.jsonl`
- signals:
    container: eh-clean-sft-grpo-full-20260623a
    container_status: running
    latest_step: 475
    total_steps: 1861
    steps_per_second: 0.081
    elapsed_seconds: 5892.582
    estimated_remaining_hours: 4.75
    reward_std: 1.0144
    combined_reward_std: 1.42353
    frac_reward_zero_std: 0.22
    completions_clipped_ratio: 0.00625
    latest_reserved_vram_gb: 11.143
    max_reserved_vram_gb: 12.998
    oom_risk_level: low
    final_model_present: false
- interpretation:
  - No intervention is indicated. The run is slow but stable, and the reward channel is still providing a useful learning signal.
  - The next meaningful gate is successful completion plus a corrected-base smoke eval of the resulting adapter.

### 020-progress - Clean SFT -> GRPO Seed 1 Midpoint Heartbeat

- at: `2026-06-24T02:42:00Z`
- kind: `train-progress`
- summary: Full GRPO reached roughly the halfway point. Training remains capacity-safe and the reward channel remains active, though the fraction of within-group zero reward standard deviation is higher than early in training and should remain on the watchlist.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/logs/training_20260623_233413.jsonl`
- signals:
    container: eh-clean-sft-grpo-full-20260623a
    container_status: running
    latest_step: 925
    total_steps: 1861
    steps_per_second: 0.082
    elapsed_seconds: 11241.588
    estimated_remaining_hours: 3.17
    reward_std: 0.80611
    combined_reward_std: 1.28456
    recent_frac_reward_zero_std_range: "0.305-0.425"
    latest_frac_reward_zero_std: 0.355
    completions_clipped_ratio: 0.00125
    latest_reserved_vram_gb: 9.848
    max_reserved_vram_gb: 13.57
    oom_risk_level: low
    final_model_present: false
- interpretation:
  - Continue the run. The reward signal has narrowed somewhat but remains live; this is a monitoring flag, not a stop condition.

### 021-progress - Clean SFT -> GRPO Seed 1 Late-Run Heartbeat

- at: `2026-06-24T04:17:00Z`
- kind: `train-progress`
- summary: Full GRPO is past three quarters complete and remains healthy. Reward variance is narrower than early training but still clearly nonzero, while VRAM remains below risk thresholds.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/logs/training_20260623_233413.jsonl`
- signals:
    container: eh-clean-sft-grpo-full-20260623a
    container_status: running
    latest_step: 1400
    total_steps: 1861
    steps_per_second: 0.083
    elapsed_seconds: 16946.224
    estimated_remaining_hours: 1.54
    reward_std: 0.78436
    combined_reward_std: 1.26586
    recent_frac_reward_zero_std_range: "0.36-0.445"
    latest_frac_reward_zero_std: 0.385
    completions_clipped_ratio: 0.0075
    latest_reserved_vram_gb: 14.969
    max_reserved_vram_gb: 14.969
    oom_risk_level: low
    final_model_present: false
- interpretation:
  - Continue. No signs of OOM, schema-length collapse, or all-zero reward groups are present.

### 022-result - Clean SFT -> GRPO Seed 1 Train Complete and Smoke Eval Passed

- at: `2026-06-24T06:00:00Z`
- kind: `train-and-eval-progress`
- summary: Full GRPO seed 1 completed successfully and the corrected-base smoke eval passed as a valid but strongly refusal-shifted result. Full eval was launched to determine whether the smoke tradeoff holds over all SelfAware rows.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/final_model`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/training_lineage.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_seed1_full/20260623_233309/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_smoke_local_4b.yaml`
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_smoke_4b/clean_schema_sft_grpo_seed1_corrected_base__selfaware/metrics.json`
- commands:
  - `docker run -d --name eh-clean-sft-grpo-full-20260623a ... train_grpo.py --config experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_full.yaml`
  - `docker run -d --name eh-clean-sft-grpo-corrected-smoke-20260624a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_smoke_local_4b.yaml --live-vllm`
  - `docker run -d --name eh-clean-sft-grpo-corrected-full-20260624a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_local_4b.yaml --live-vllm`
- signals:
    training:
      container: eh-clean-sft-grpo-full-20260623a
      exit_status: 0
      final_step: 1861
      train_runtime_seconds: 22441.788
      train_steps_per_second: 0.083
      final_loss: 0.1578
      peak_reserved_vram_gb: 17.396
      peak_reserved_vram_pct: 72.49
      min_reserved_headroom_gb: 6.603
      oom_risk_level: low
      dataset_rows: 14888
      batch_size: 32
      num_generations: 4
    smoke_eval:
      container: eh-clean-sft-grpo-corrected-smoke-20260624a
      exit_status: 0
      rows: 192
      known_rows: 97
      unknown_rows: 95
      config_sha: 1c5d5990af41e14e
      json_confidence_coverage_pct: 100.0
      refusal_recall_pct: 93.68
      answer_on_unknown_pct: 6.32
      over_refusal_pct: 80.41
      refusal_rate_pct: 86.98
      correct_on_known_pct: 47.37
      truthful_pct: 51.04
      mean_response_confidence: 0.744005
    smoke_delta_vs_clean_sft_merged:
      truthful_pct: "+1.56"
      refusal_recall_pct: "+7.36"
      answer_on_unknown_pct: "-7.36"
      over_refusal_pct: "+16.49"
      correct_on_known_pct: "+10.23"
      mean_response_confidence: "-0.012205"
- interpretation:
  - GRPO did not fail structurally: training completed, schema coverage is complete, and the smoke result is internally coherent.
  - Behaviorally, the smoke suggests GRPO learned a much more conservative decision rule. It sharply reduced unknown answering but paid for that with a large increase in known-row over-refusal.
  - This is a valid tradeoff to quantify on the full eval, not a reason to discard the run before measuring it.
- decisions:
  - Continue with the full corrected-base GRPO eval.
  - If the full eval confirms this tradeoff, treat GRPO seed 1 as "effective at reducing hallucination pressure, too blunt on answerability discrimination" rather than as an infrastructure failure.

### 023-result - Corrected Clean SFT -> GRPO Full SelfAware Eval

- at: `2026-06-24T06:45:00Z`
- kind: `eval-result`
- summary: Clean schema SFT -> GRPO seed 1 completed full SelfAware eval. GRPO strongly reduced unknown answering and increased answered-known accuracy, but it did so by refusing far more known questions; total truthful rate was slightly lower than clean SFT.
- evidence:
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b/clean_schema_sft_grpo_seed1_corrected_base__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b/clean_schema_sft_grpo_seed1_corrected_base__selfaware/scored_rows.jsonl`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b/comparisons/summary_table.csv`
- commands:
  - `docker run -d --name eh-clean-sft-grpo-corrected-full-20260624a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_local_4b.yaml --live-vllm`
- signals:
    full_eval:
      container: eh-clean-sft-grpo-corrected-full-20260624a
      exit_status: 0
      rows: 3369
      known_rows: 2337
      unknown_rows: 1032
      config_sha: c7d618bf9048c77c
      json_confidence_coverage_pct: 100.0
      refusal_recall_pct: 95.54
      answer_on_unknown_pct: 4.46
      over_refusal_pct: 75.7
      refusal_rate_pct: 81.78
      answered_known: 568
      correct_known: 351
      correct_on_known_pct_answered_known_denominator: 61.8
      answered_unknown: 46
      truthful_pct: 39.69
      mean_response_confidence: 0.746546
      brier_vs_response_appropriateness: 0.369721
    full_delta_vs_clean_sft:
      truthful_pct: "-0.89"
      refusal_recall_pct: "+8.52"
      answer_on_unknown_pct: "-8.52"
      over_refusal_pct: "+18.19"
      refusal_rate_pct: "+15.23"
      correct_on_known_pct_answered_known_denominator: "+14.57"
      answered_known_count: "-425"
      correct_known_count: "-118"
      answered_unknown_count: "-88"
      mean_response_confidence: "-0.001943"
      brier_vs_response_appropriateness: "+0.006065"
    full_delta_vs_clean_sft_dpo:
      truthful_pct: "-1.00"
      refusal_recall_pct: "+8.43"
      answer_on_unknown_pct: "-8.43"
      over_refusal_pct: "+19.52"
      refusal_rate_pct: "+16.12"
      mean_response_confidence: "-0.065537"
    full_delta_vs_clean_sft_kto:
      truthful_pct: "+0.33"
      refusal_recall_pct: "+14.53"
      answer_on_unknown_pct: "-14.53"
      over_refusal_pct: "+23.33"
      refusal_rate_pct: "+20.63"
      mean_response_confidence: "-0.106166"
    row_level:
      top_generated_answer: '{"answer": "I don''t know the answer to that, but I''d be glad to help with something else.","response_confidence": 0.711}'
      top_generated_answer_count: 874
      top_confidence_value: 0.711
      top_confidence_count: 1521
      known_confidence_mean: 0.746235
      unknown_confidence_mean: 0.747248
- interpretation:
  - GRPO is a valid run and a useful diagnostic, but not a solution yet. It learned a much more conservative response policy, not a clean "know what it knows" boundary.
  - The reward appears to make the model answer only when it is more likely to be correct, which raises answered-known accuracy, but it also rejects too many known rows. The real all-row outcome is visible in `truthful_pct`, not in `correct_on_known_pct` alone.
  - Confidence expression did not improve materially. Mean confidence stayed close to SFT, known/unknown confidence means are nearly identical, and values remain concentrated around a few bands.
  - Relative to DPO/KTO, GRPO is the only downstream method so far that strongly reduces unknown answering, but it overcorrects into over-refusal.
- decisions:
  - Treat GRPO seed 1 as "conservative refusal boundary; hallucination pressure reduced; answerability discrimination too blunt; confidence still weak."
  - Update the experiment-runner eval gotchas with the conditional-denominator trap for `correct_on_known_pct`.
  - Next research step should change the reward/data balance rather than rerunning the same GRPO recipe: add stronger credit for correct known answers, explicit cost for known over-refusal, and/or stratify batches/rewards so known-answer retention competes directly with unknown abstention.

### 024-plan - GRPO Reward V2 Design

- at: `2026-06-24T07:05:00Z`
- kind: `design-and-implementation-start`
- summary: Began a separate GRPO reward-v2 branch to address the two confirmed seed-1 GRPO failures: over-refusal on known rows and inaccurate/confidence-clustered response-confidence values.
- evidence:
  - `experiment/phase1/grpo/humility_reward.py`
  - `experiment/phase1/grpo/tests/test_humility_reward.py`
  - `experiment/phase1/grpo/humility_reward_v2.py`
  - `experiment/phase1/grpo/tests/test_humility_reward_v2.py`
  - `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_smoke.yaml`
  - `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_full.yaml`
- signals:
    prior_v1_reward_grid:
      known_correct_high: 1.5
      unknown_abstain_high: 0.75
      known_overrefusal_low: -0.1
      known_overrefusal_high: -1.1
      unknown_guess_low: -0.6
      unknown_guess_high: -1.9
    diagnosed_issue:
      - Low-confidence known over-refusal was barely penalized, giving GRPO a path toward conservative refusal.
      - Confidence band rewards could improve the score of an inappropriate response, so confidence shaping could soften rather than fix the wrong behavior.
    v2_reward_goals:
      - Behavior dominates confidence; confidence cannot turn bad behavior into good behavior.
      - Known correct answers receive the largest reward.
      - Known over-refusal is strongly negative even when low-confidence.
      - Unknown abstention remains positive, especially when high response-confidence.
      - Unknown guesses and known wrong answers are less bad when low-confidence, but remain negative.
      - Ambiguous answers prefer middle confidence rather than high-confidence answer or high-confidence refusal.
    v2_expected_ordering:
      - known_correct_high > unknown_abstain_high > known_wrong_low > known_overrefusal_low
      - known_overrefusal_high < known_overrefusal_low < 0
      - unknown_guess_high < unknown_guess_low < 0
- interpretation:
  - This is a reward/objective revision, not a rerun of the failed v1 recipe.
  - The first gate is CPU-side reward tests and a sanity score table; the second gate is a short GRPO smoke with reward-debug inspection before any full GPU run.
- decisions:
  - Implement reward v2 as `humility_reward_v2.py` rather than mutating `humility_reward.py`, preserving the v1 negative result.
  - Add v2 smoke/full configs using the same clean merged-SFT base and GRPO dataset, with output dirs labeled `schema_clean_sft_grpo_v2_*`.

### 025-progress - GRPO Reward V2 CPU Tests and Smoke

- at: `2026-06-24T09:55:00Z`
- kind: `train-smoke-result`
- summary: Reward V2 passed CPU-side score-ordering tests and completed a 12-step GRPO smoke. The smoke shows live reward variance and the intended reward ordering on actual sampled completions.
- evidence:
  - `experiment/phase1/grpo/humility_reward_v2.py`
  - `experiment/phase1/grpo/tests/test_humility_reward_v2.py`
  - `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_smoke.yaml`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_smoke/20260624_094700/logs/training_20260624_094806.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_smoke/20260624_094700/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_smoke/reward_debug_20260624a.jsonl`
- commands:
  - `python -m pytest experiment\phase1\grpo\tests\test_humility_reward.py experiment\phase1\grpo\tests\test_humility_reward_v2.py experiment\phase1\grpo\tests\test_build_schema_response_confidence_datasets.py -q`
  - `docker run -d --name eh-clean-sft-grpo-v2-smoke-20260624a ... train_grpo.py --config experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_smoke.yaml`
- signals:
    cpu_tests:
      result: "39 passed"
    v2_reward_score_grid:
      known_correct_high: 2.6
      known_correct_low: 1.4
      unknown_abstain_high: 1.8
      unknown_abstain_low: 0.6
      known_wrong_low: -0.2
      known_wrong_high: -1.4
      unknown_guess_low: -0.6
      unknown_guess_high: -1.8
      known_overrefusal_low: -1.4
      known_overrefusal_high: -2.6
      malformed_known_correct: -0.4
    smoke_training:
      container: eh-clean-sft-grpo-v2-smoke-20260624a
      exit_status: 0
      run_dir: scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_smoke/20260624_094700
      train_steps: 12
      train_runtime_seconds: 134.488
      train_steps_per_second: 0.089
      final_loss: 0.0008
      peak_reserved_vram_gb: 10.914
      oom_risk_level: low
      reward_std_nonzero_steps: 12
      max_frac_reward_zero_std: 0.125
      max_clipped_ratio: 0.03125
    reward_debug:
      rows: 384
      valid_json_rows: 375
      invalid_json_rows: 9
      labels:
        known: 252
        unknown: 116
        ambiguous: 16
      reward_min: -3.6
      reward_max: 2.5949
      reward_mean: 0.5375
      known_correct_mean_reward: 2.359
      unknown_abstain_mean_reward: 1.653
      known_wrong_mean_reward: -1.441
      unknown_guess_mean_reward: -1.854
      known_overrefusal_mean_reward: -2.6
- interpretation:
  - The reward-grid preflight was effective: it exposed the old weak known-overrefusal penalty before GPU use and now provides a compact reproducibility check for V2.
  - Smoke training is technically healthy. Reward variance is live on every step, clipping is low, VRAM is safe, and debug rows show the intended behavior hierarchy on real sampled completions.
  - The v2 objective now directly counterweights the v1 failure mode by making known over-refusal worse than low-confidence wrong answers and unknown low-confidence guesses.
- decisions:
  - Treat GRPO v2 as cleared for a full local run unless a separate review finds a reward-design issue.
  - Add a generic reward-grid preflight gotcha to the reusable GRPO skill guidance so future reward systems are checked before fine-tuning.

### 026-launch - GRPO Reward V2 Full Run

- at: `2026-06-24T09:58:06Z`
- kind: `train-launch`
- summary: Launched the full local GRPO v2 run from the merged clean-SFT seed-1 base after the reward-grid preflight and 12-step smoke both passed.
- evidence:
  - `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_full.yaml`
  - `experiment/phase1/grpo/humility_reward_v2.py`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_smoke/20260624_094700/`
- commands:
  - `docker run -d --name eh-clean-sft-grpo-v2-full-20260624a ... train_grpo.py --config experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_full.yaml`
- signals:
    container: eh-clean-sft-grpo-v2-full-20260624a
    docker_id: 69cd18ed8123dc07511b553765b79c557588cd83b8a18cc822a3f9de1b91bd7d
    reward_debug_full_run: disabled
    rationale:
      - The smoke debug trace already validated the reward hierarchy on sampled completions.
      - The full run should avoid generating a large debug artifact unless trainer logs show suspicious reward variance or parsing behavior.
- decisions:
  - Monitor early logs for config/import failures, then inspect trainer reward variance and capacity before treating the run as healthy.

### 027-progress - GRPO Reward V2 Full Run Early Health Check

- at: `2026-06-24T10:16:00Z`
- kind: `train-progress`
- summary: Early full-run logs show GRPO v2 training is active and healthy through step 75/1861.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
- signals:
    container: eh-clean-sft-grpo-v2-full-20260624a
    run_dir: scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831
    steps_seen:
      - 25
      - 50
      - 75
    total_steps: 1861
    current_steps_per_second: 0.083
    estimated_remaining_hours: 6.0
    max_gpu_memory_reserved_gb: 10.914
    max_gpu_memory_reserved_pct: 45.48
    oom_risk_level: low
    reward_std_step_25: 1.9333
    reward_std_step_50: 1.9700
    reward_std_step_75: 1.9974
    frac_reward_zero_std_step_75: 0.025
    clipped_ratio_step_75: 0.00375
- interpretation:
  - The run cleared the main early failure gates: model load, custom reward import, dataset load, trainer start, and nonzero reward variance.
  - The low clipping and low VRAM pressure mean there is no current reason to stop or downshift the run.
- decisions:
  - Continue monitoring on timer checkpoints until completion, then run the standard Amendment E full eval before drawing behavioral conclusions.

### 028-progress - GRPO Reward V2 Full Run 200-Step Check

- at: `2026-06-24T10:42:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 remains healthy through step 200/1861.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
- signals:
    step: 200
    total_steps: 1861
    steps_per_second: 0.082
    estimated_remaining_hours: 5.6
    max_gpu_memory_reserved_gb: 12.998
    max_gpu_memory_reserved_pct: 54.16
    oom_risk_level: low
    latest_reward_mean: 0.19975
    latest_reward_std: 1.92226
    latest_frac_reward_zero_std: 0.03
    latest_clipped_ratio: 0.005
    checkpoint_written: false
- interpretation:
  - The objective has usable comparative signal; reward variance is not collapsing.
  - The run still has substantial VRAM headroom despite reserved memory increasing after startup.
  - No checkpoint is expected until step 500 under the current config.
- decisions:
  - Keep the run active and re-check around the first checkpoint boundary.

### 029-progress - GRPO Reward V2 Full Run First Checkpoint

- at: `2026-06-24T11:45:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 reached step 500/1861 and wrote the first checkpoint.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/checkpoints/checkpoint-500/`
- signals:
    step: 500
    total_steps: 1861
    steps_per_second: 0.08
    estimated_remaining_hours: 4.7
    max_gpu_memory_reserved_gb: 13.621
    max_gpu_memory_reserved_pct: 56.76
    oom_risk_level: low
    latest_reward_mean: 0.25624
    latest_reward_std: 1.97345
    latest_frac_reward_zero_std: 0.045
    latest_clipped_ratio: 0.0075
    checkpoint_written: checkpoint-500
- interpretation:
  - The first durable recovery point exists, so an interruption can resume from a meaningful checkpoint.
  - Comparative reward signal remains strong enough to continue; no zero-variance collapse is visible.
  - Clipping remains low and there is still about 10 GB of reserved-memory headroom.
- decisions:
  - Continue the run. Next checkpoint is expected at step 1000.

### 030-progress - GRPO Reward V2 Full Run Midpoint Check

- at: `2026-06-24T12:48:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 remains stable through step 775/1861, with the first checkpoint preserved and no signs of reward collapse.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/checkpoints/checkpoint-500/`
- signals:
    step: 775
    total_steps: 1861
    steps_per_second: 0.078
    estimated_remaining_hours: 3.9
    max_gpu_memory_reserved_gb: 13.621
    latest_gpu_memory_reserved_gb: 9.391
    oom_risk_level: low
    latest_reward_mean: 0.44057
    latest_reward_std: 1.93759
    latest_frac_reward_zero_std: 0.01
    latest_clipped_ratio: 0.01
    latest_kl: 1.83638
- interpretation:
  - Reward signal remains live and comparable to earlier checkpoints.
  - No obvious instability is visible in KL, clipping, or memory.
- decisions:
  - Continue to the step-1000 checkpoint boundary.

### 031-progress - GRPO Reward V2 Full Run Codex-Restart Check

- at: `2026-06-24T13:24:00Z`
- kind: `train-progress`
- summary: After a Codex restart, the Docker training container remained active and GRPO v2 was still healthy at step 925/1861.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/checkpoints/checkpoint-500/`
- signals:
    container: eh-clean-sft-grpo-v2-full-20260624a
    step: 925
    total_steps: 1861
    progress_pct: 49.7
    steps_per_second: 0.076
    estimated_remaining_hours: 3.4
    gpu_active: true
    latest_reward_mean: 0.44561
    latest_reward_std: 1.92960
    latest_frac_reward_zero_std: 0.02
    latest_clipped_ratio: 0.0125
    latest_kl: 1.58559
    oom_risk_level: low
    checkpoints_present:
      - checkpoint-500
- interpretation:
  - The run survived the Codex client restart because it is detached in Docker.
  - No new instability is visible; continue monitoring to the step-1000 checkpoint.

### 032-progress - GRPO Reward V2 Full Run Step-1000 Checkpoint

- at: `2026-06-24T13:48:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 crossed step 1000/1861 and wrote the second checkpoint.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/checkpoints/checkpoint-1000/`
- signals:
    latest_step: 1025
    total_steps: 1861
    progress_pct: 55.1
    steps_per_second: 0.075
    estimated_remaining_hours: 3.1
    latest_reward_mean: 0.57896
    latest_reward_std: 1.89850
    latest_frac_reward_zero_std: 0.025
    latest_clipped_ratio: 0.00875
    latest_kl: 1.84755
    oom_risk_level: low
    checkpoints_present:
      - checkpoint-500
      - checkpoint-1000
- interpretation:
  - The second durable checkpoint exists.
  - Reward variance, clipping, KL, and memory remain inside the acceptable range for continuing.
- decisions:
  - Continue monitoring. Next checkpoint is expected at step 1500.

### 033-progress - GRPO Reward V2 Full Run Late Check

- at: `2026-06-24T14:49:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 remains healthy past two-thirds completion at step 1275/1861.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/checkpoints/checkpoint-1000/`
- signals:
    latest_step: 1275
    total_steps: 1861
    progress_pct: 68.5
    steps_per_second: 0.074
    estimated_remaining_hours: 2.2
    latest_reward_mean: 0.40096
    latest_reward_std: 1.95514
    latest_frac_reward_zero_std: 0.03
    latest_clipped_ratio: 0.015
    latest_kl: 1.89611
    max_gpu_memory_reserved_gb: 13.621
    latest_gpu_memory_reserved_gb: 13.295
    oom_risk_level: low
- interpretation:
  - Reward signal remains live and stable in the late-middle portion of training.
  - Memory has not grown beyond the prior safe peak.
- decisions:
  - Continue to the step-1500 checkpoint.

### 034-progress - GRPO Reward V2 Full Run Step-1500 Checkpoint

- at: `2026-06-24T15:49:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 crossed step 1500/1861 and wrote the third checkpoint.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/checkpoints/checkpoint-1500/`
- signals:
    latest_step: 1525
    total_steps: 1861
    progress_pct: 81.9
    steps_per_second: 0.073
    estimated_remaining_hours: 1.3
    latest_reward_mean: 0.52853
    latest_reward_std: 1.91537
    latest_frac_reward_zero_std: 0.04
    latest_clipped_ratio: 0.01125
    latest_kl: 1.50861
    max_gpu_memory_reserved_gb: 17.617
    max_gpu_memory_reserved_pct: 73.41
    latest_gpu_vram_used_gb: 12.27
    oom_risk_level: low
    checkpoints_present:
      - checkpoint-500
      - checkpoint-1000
      - checkpoint-1500
- interpretation:
  - The third durable checkpoint exists.
  - VRAM peaked higher in this window but remains below the danger band, with low OOM risk and enough headroom to continue.
  - Reward variance remains live through the late run.
- decisions:
  - Continue to completion and inspect final artifacts before launching eval.

### 035-progress - GRPO Reward V2 Full Run Final Stretch

- at: `2026-06-24T16:40:00Z`
- kind: `train-progress`
- summary: Full GRPO v2 is in the final stretch at step 1725/1861 with stable metrics.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
- signals:
    latest_step: 1725
    total_steps: 1861
    progress_pct: 92.7
    steps_per_second: 0.072
    estimated_training_remaining_minutes: 32
    latest_reward_mean: 0.57024
    latest_reward_std: 1.89607
    latest_frac_reward_zero_std: 0.02
    latest_clipped_ratio: 0.015
    latest_kl: 1.90200
    latest_gpu_vram_used_gb: 15.758
    max_gpu_memory_reserved_gb: 17.617
    oom_risk_level: low
- interpretation:
  - No late-run stop signal is visible.
  - Continue through final save, then verify final artifacts and run metadata before eval.

### 036-result - GRPO Reward V2 Full Run Completed

- at: `2026-06-24T17:16:00Z`
- kind: `train-result`
- summary: Full GRPO v2 completed cleanly and saved final adapter artifacts.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model/`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/training_lineage.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/capacity_features.json`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/logs/training_20260624_095936.jsonl`
- signals:
    container: eh-clean-sft-grpo-v2-full-20260624a
    exit_status: 0
    final_step: 1861
    train_runtime_seconds: 25983.384
    train_steps_per_second: 0.072
    final_loss: 0.1785
    peak_reserved_vram_gb: 17.617
    peak_reserved_vram_pct: 73.41
    oom_risk_level: low
    final_model_files_present:
      - adapter_config.json
      - adapter_model.safetensors
      - tokenizer.json
      - tokenizer_config.json
      - training_args.bin
- interpretation:
  - The V2 full training run is valid as a completed local experimental artifact.
  - Capacity was safe despite late-run reserved-memory growth.
  - No behavioral conclusion should be drawn until the full SelfAware eval completes.

### 037-launch - GRPO Reward V2 Full SelfAware Eval

- at: `2026-06-24T17:18:00Z`
- kind: `eval-launch`
- summary: Launched the full SelfAware eval for the completed clean schema-SFT -> GRPO v2 seed-1 adapter on the corrected merged-SFT base.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`
- commands:
  - `docker run -d --name eh-clean-sft-grpo-v2-eval-full-20260624a ... run_eval.py --config experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml --live-vllm`
- signals:
    container: eh-clean-sft-grpo-v2-eval-full-20260624a
    docker_id: baedbbe7db4b3b4bdfc9d238f58e83d927a21996ffeb16ac4f32057b18e71f9f
    model_name: /workspace/repo/scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit
    adapter: /workspace/repo/scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model
    results_dir: results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b
- decisions:
  - Monitor early startup for vLLM/model/adapter errors before assuming the eval is running.

### 038-progress - GRPO Reward V2 Eval Startup Healthy

- at: `2026-06-24T17:22:00Z`
- kind: `eval-progress`
- summary: Full SelfAware eval for GRPO v2 started successfully and is actively generating with vLLM.
- evidence:
  - `docker logs --tail 160 eh-clean-sft-grpo-v2-eval-full-20260624a`
- signals:
    container: eh-clean-sft-grpo-v2-eval-full-20260624a
    status: running
    gpu_active: true
    live_gpu_vram_used_mb: 11530
    result_dir_visible_at_startup_check: false
- interpretation:
  - vLLM/model/adapter startup cleared; the eval is doing generation work.
  - Result files may not be host-visible until later in the run or completion; continue monitoring rather than treating the absent directory as failure.

### 039-result - GRPO Reward V2 Full SelfAware Eval

- at: `2026-06-24T17:59:00Z`
- kind: `eval-result`
- summary: GRPO v2 improved the refusal-boundary tradeoff versus GRPO v1, but did not solve confidence calibration. Confidence moved to many distinct values, but all values remain clustered high and are nearly indistinguishable across correct answers, wrong answers, over-refusals, and correct abstentions.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b/clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b/clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware/scored_rows.jsonl`
  - `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b/comparisons/summary_table.csv`
- signals:
    eval_container: eh-clean-sft-grpo-v2-eval-full-20260624a
    exit_status: 0
    config_sha: 7e45890660a1824b
    n: 3369
    refusal_recall_pct: 93.41
    answer_on_unknown_pct: 6.59
    over_refusal_pct: 66.62
    refusal_rate_pct: 74.83
    correct_on_known_pct: 53.85
    truthful_pct: 41.08
    confidence_coverage_pct: 100.0
    mean_response_confidence: 0.813382
    response_confidence_unique_values: 50
    response_confidence_min: 0.7014
    response_confidence_max: 0.8844
    brier_vs_response_appropriateness: 0.403378
    confidence_by_behavior:
      known_correct_mean: 0.82224
      known_refusal_mean: 0.810927
      known_wrong_mean: 0.820013
      unknown_refusal_mean: 0.811085
      unknown_answer_mean: 0.812354
    retry_counts:
      zero_retries: 3369
      retry_exhausted: 0
    prior_v1_comparison:
      truthful_pct: "39.69 -> 41.08"
      answer_on_unknown_pct: "4.46 -> 6.59"
      over_refusal_pct: "75.70 -> 66.62"
      mean_response_confidence: "0.746546 -> 0.813382"
      brier_vs_response_appropriateness: "0.369721 -> 0.403378"
- interpretation:
  - V2 partially fixed the v1 behavior failure: it retained more known answers and improved total truthful rate while still keeping unknown answering low relative to SFT.
  - V2 did not fix confidence learning. The model now varies the scalar cosmetically, but confidence remains high for inappropriate over-refusals and wrong answers.
  - The reward-grid preflight was still valuable: it prevented the worst v1 incentive geometry, but offline reward ordering alone is not sufficient evidence that confidence will become behavior-conditional after GRPO.
- decisions:
  - Treat GRPO v2 as "best behavior tradeoff so far among the clean SFT downstream runs, but confidence still failed."
  - Add a reusable eval gotcha: after confidence-reward GRPO, always report confidence by behavioral cell, not just mean confidence, coverage, or unique-value count.
