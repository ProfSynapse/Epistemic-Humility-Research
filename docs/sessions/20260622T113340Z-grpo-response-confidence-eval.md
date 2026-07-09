---
schema_version: research-session/v1
session_id: 20260622T113340Z-grpo-response-confidence-eval
title: GRPO Response-Confidence Eval
status: active
created_at: '2026-06-22T11:33:40Z'
updated_at: '2026-06-22T13:42:31Z'
phase: phase1
question: Does the completed SFT-bridge GRPO adapter improve response-appropriate
  confidence and truthful SelfAware behavior compared with its SFT JSON-bridge base?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Amendment B GRPO eval follow-up after the first completed SFT
    JSON-bridge -> GRPO seed-1 full run.
  changed_by_session: Adds response-appropriateness confidence scoring and standard
    SelfAware eval configs for the completed GRPO adapter.
checkpoints: []
legacy_session:
  id: grpo-response-confidence-eval
  path: docs/sessions/0016 - grpo-response-confidence-eval.md
---
# GRPO Response-Confidence Eval

## Question

Does the completed SFT-bridge GRPO adapter improve response-appropriate confidence and truthful SelfAware behavior compared with its SFT JSON-bridge base?

## Trajectory Position

This session evaluates the completed local SFT JSON-bridge -> GRPO seed-1 adapter against its merged SFT JSON-bridge base. It is bounded Amendment B/GRPO evidence, not locked v0.3 headline evidence.

## Summary

The full SelfAware response-confidence eval completed for the SFT JSON-bridge base and the completed SFT JSON-bridge -> GRPO seed-1 adapter. GRPO reduced over-refusal but also reduced unknown refusal recall, leaving truthful rate statistically unchanged; both arms emitted confidence 1.0 on every row, so this run does not show learned confidence calibration.

Follow-up diagnostics marked the GRPO adapter as a failed confidence-learning
model rather than a candidate checkpoint. The collapse was already present in
the SFT JSON-bridge control and is plausibly seeded by supervised bridge targets
that used `confidence: 1.0` for both known answers and unknown abstentions, then
reinforced by the current reward formula's endpoint target for appropriate
responses.

## Checkpoints

### 001-planning - Response-Confidence Eval Setup

- at: `2026-06-22T11:43:11Z`
- kind: `planning`
- summary: Added a GRPO-aligned stated-confidence metric for response appropriateness while preserving the existing known-label and answer-correctness confidence metrics.
- evidence:
  - `experiment/phase1/eval/scorers.py`
  - `experiment/phase1/eval/tests/test_scorers.py`
  - `experiment/phase1/eval/config/eval_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_smoke_local_4b.yaml`
  - `experiment/phase1/eval/config/eval_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_unknown_smoke_local_4b.yaml`
  - `experiment/phase1/eval/config/eval_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_local_4b.yaml`
- commands:
  - `python -m pytest experiment/phase1/eval/tests/test_scorers.py -q`
- decisions:
  - Compare the merged SFT JSON-bridge base as the no-adapter arm against the completed GRPO adapter on that same base.
  - Interpret `confidence` for this GRPO eval as response appropriateness: correct known answers and correct unknown abstentions are high-confidence targets.
- next_steps:
  - Run full SelfAware live-vLLM eval after known and unknown smokes clear.

### 002-validation - Known/Unknown Smoke Evals

- at: `2026-06-22T11:43:11Z`
- kind: `validation`
- summary: Known-block and unknown-block smoke evals both completed with 100% stated-confidence coverage, zero retries, and zero retry exhaustion. The first 64 SelfAware rows are all known; the unknown block starts at offset 2337, so a second smoke was required.
- evidence:
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_smoke_4b/`
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_unknown_smoke_4b/`
- commands:
  - `docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v "${PWD}:/workspace/repo" -w /workspace/repo unsloth/unsloth:latest experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_smoke_local_4b.yaml --live-vllm`
  - `docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v "${PWD}:/workspace/repo" -w /workspace/repo unsloth/unsloth:latest experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_unknown_smoke_local_4b.yaml --live-vllm`
- signals:
    known_smoke:
      sft_json_bridge_seed1:
        over_refusal_pct: 73.44
        truthful_pct: 14.06
        confidence_coverage_pct: 100.0
        mean_stated_confidence: 1.0
      sft_bridge_grpo_seed1:
        over_refusal_pct: 62.5
        truthful_pct: 17.19
        confidence_coverage_pct: 100.0
        mean_stated_confidence: 1.0
    unknown_smoke:
      sft_json_bridge_seed1:
        refusal_recall_pct: 89.06
        truthful_pct: 89.06
        response_confidence_mae: 0.109375
        mean_stated_confidence: 1.0
      sft_bridge_grpo_seed1:
        refusal_recall_pct: 79.69
        truthful_pct: 79.69
        response_confidence_mae: 0.203125
        mean_stated_confidence: 1.0
- decisions:
  - Treat confidence saturation at 1.0 as a potential finding or prompt-contract artifact; do not interpret confidence calibration strongly until full eval and row review complete.

### 003-result - Full SelfAware Response-Confidence Eval

- at: `2026-06-22T12:24:00Z`
- kind: `result`
- summary: Full live-vLLM SelfAware eval completed successfully for both arms in Docker container `eh-grpo-response-confidence-eval-full-20260622074347` with exit code 0. GRPO did not improve truthful rate versus the SFT JSON-bridge base (`40.84%` vs `41.14%`; McNemar `p=0.45009106`) despite reducing known over-refusal.
- evidence:
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b/sft_json_bridge_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b/sft_bridge_grpo_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b/comparisons/summary_table.csv`
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b/comparisons/mcnemar.csv`
- commands:
  - `docker run -d --name eh-grpo-response-confidence-eval-full-20260622074347 --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v "${PWD}:/workspace/repo" -w /workspace/repo unsloth/unsloth:latest experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_local_4b.yaml --live-vllm`
  - `docker inspect eh-grpo-response-confidence-eval-full-20260622074347 --format "{{.State.Status}} {{.State.ExitCode}}"`
  - `docker rm eh-grpo-response-confidence-eval-full-20260622074347`
- signals:
    full_selfaware:
      sft_json_bridge_seed1:
        n: 3369
        refusal_recall_pct: 93.02
        over_refusal_pct: 62.86
        refusal_rate_pct: 72.1
        correct_on_known_pct: 49.08
        truthful_pct: 41.14
        truthful_ci: [0.3941674087266251, 0.4266102701098249]
        confidence_coverage_pct: 100.0
        mean_stated_confidence: 1.0
        unique_confidence_values: 1
        response_confidence_mae: 0.588602
      sft_bridge_grpo_seed1:
        n: 3369
        refusal_recall_pct: 86.72
        over_refusal_pct: 55.71
        refusal_rate_pct: 65.21
        correct_on_known_pct: 46.47
        truthful_pct: 40.84
        truthful_ci: [0.3920451172454734, 0.42358266547937073]
        confidence_coverage_pct: 100.0
        mean_stated_confidence: 1.0
        unique_confidence_values: 1
        response_confidence_mae: 0.59157
      paired_comparison:
        b_base_not_grpo: 76
        c_grpo_not_base: 66
        mcnemar_p_value: 0.45009106
- interpretation:
  - GRPO shifted policy toward answering: it converted 167 known refusals into answers, increasing correct known count from 426 to 481, but it also converted 65 more unknown rows into answers, reducing correct unknown refusals from 960 to 895.
  - Because every parsed confidence was exactly 1.0, the confidence field is currently a schema-compliant but non-informative channel under this deterministic response-confidence eval.
- next_steps:
  - Decide whether to run a temperature/prompt diagnostic for confidence variation before additional GRPO training.
  - Treat this GRPO run as evidence of a behavior tradeoff, not evidence that stated-confidence calibration is solved.

### 004-interpretation - GRPO Confidence Collapse Failure

- at: `2026-06-22T13:42:31Z`
- kind: `interpretation`
- summary: Follow-up diagnostics showed the completed SFT JSON-bridge -> GRPO seed-1 adapter failed the confidence-learning objective. It preserved a degenerate confidence channel rather than learning calibrated response confidence.
- evidence:
  - `scratch/grpo_bootstrap/confidence_diagnostics/20260622_response_confidence/`
  - `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b/`
  - `experiment/phase1/grpo/build_sft_json_bridge_dataset.py`
  - `experiment/phase1/grpo/humility_reward.py`
- signals:
    failed_grpo_adapter:
      model_tag: sft_bridge_grpo_seed1
      truthful_pct: 40.84
      refusal_recall_pct: 86.72
      over_refusal_pct: 55.71
      confidence_coverage_pct: 100.0
      mean_stated_confidence: 1.0
      unique_confidence_values: 1
      response_confidence_mae: 0.59157
    sft_json_bridge_control:
      model_tag: sft_json_bridge_seed1
      truthful_pct: 41.14
      refusal_recall_pct: 93.02
      over_refusal_pct: 62.86
      confidence_coverage_pct: 100.0
      mean_stated_confidence: 1.0
      unique_confidence_values: 1
      response_confidence_mae: 0.588602
    ordinary_sft_amendment_b_comparison:
      sft_seed1_mean_confidence: 0.435581
      sft_seed2_mean_confidence: 0.365246
      sft_seed3_mean_confidence: 0.34981
      sft_merged_seed1_mean_confidence: 0.479383
      sft_merged_seed2_mean_confidence: 0.391848
      sft_merged_seed3_mean_confidence: 0.381145
- interpretation:
  - The ordinary SFT Amendment B evals did not show the all-1.0 confidence collapse; they emitted varied confidence values with means around 0.35-0.48 under the answer-confidence contract.
  - The special SFT JSON bridge did show the all-1.0 collapse before GRPO. That bridge trained `confidence: 1.0` for both known gold answers and unknown abstentions.
  - Higher-temperature diagnostics, a stronger scale prompt, and no structured-output grammar still produced confidence 1.0 on parsed rows, so the collapse is not explained by deterministic decoding or the structured-output schema alone.
  - The current GRPO reward made 1.0 the mathematical calibration target for appropriate known answers and appropriate unknown abstentions; paired with the bridge target, this likely reinforced endpoint confidence rather than teaching graded confidence expression.
- decisions:
  - Mark `sft_bridge_grpo_seed1` as a failed model for the response-confidence learning objective.
  - Do not use the failed GRPO adapter as a candidate model for future comparisons except as negative evidence.
  - Preserve logs, eval metrics, diagnostics, lineage, and this session note as the failure record.
  - Delete local failed-model weight artifacts to avoid accidental reuse.
- disposition:
    deleted_local_artifacts:
      - `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/final_model`
      - `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/merged-16bit`
      - `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/checkpoints`
    retained_local_evidence:
      - `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/logs/`
      - `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/training_lineage.json`
      - `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/capacity_features.json`
- next_steps:
  - Replace endpoint confidence targets with a banded confidence reward/bridge design before another GRPO attempt.
  - Add reward sanity tests that penalize exact 0.0/1.0 endpoints when calibrated expression, not deterministic correctness, is the target.
