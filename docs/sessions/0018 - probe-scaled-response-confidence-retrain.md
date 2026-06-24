---
schema_version: research-session/v1
session_id: probe-scaled-response-confidence-retrain
title: Probe-Scaled Response Confidence Retrain
status: active
created_at: '2026-06-23T09:36:54Z'
updated_at: '2026-06-23T09:40:26Z'
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
